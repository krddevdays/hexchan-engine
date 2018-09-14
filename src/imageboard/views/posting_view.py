# Standard library imports
# import logging
import os

# Django imports
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth import get_user
from django.db import transaction, DatabaseError
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt

# Third party imports
import PIL.Image
import bleach

# App imports
from gensokyo import config
from imageboard.models import Board, Thread, Post, Image
from imageboard.forms import PostingForm
from imageboard import exceptions


@csrf_exempt
def posting_view(request):
    try:
        # Check request type
        if not request.POST:
            raise exceptions.BadRequestType

        # Get form data
        form = PostingForm(request.POST)
        if not form.is_valid():
            raise exceptions.FormValidationError(form.errors)

        # Get form type
        form_type = form.cleaned_data['form_type']

        # Get and check board object
        board_id = form.cleaned_data['board_id']
        board = get_board(board_id)

        #  If creating post in a thread - get and check that thread
        if form_type == 'new_post':
            # Get and check  thread
            thread_id = form.cleaned_data['thread_id']
            thread = get_thread(thread_id)
        else:
            thread = None

        # # Check captcha
        # captcha_error = check_captcha(request)
        # if captcha_error:
        #     return make_error_message(captcha_error)

        # Get list of uploaded image objects
        images = request.FILES.getlist('images')

        # Check message
        check_message_content(cleaned_data=form.cleaned_data, images=images)

    except exceptions.ImageboardError as e:
        return render(request, 'imageboard/posting_error_page.html', context={'exception': e}, status=403)

    # Create thread, op post, save images, bump board's thread counter
    # try:
    with transaction.atomic():
        # Bump board's post HID counter
        board.last_post_hid = F('last_post_hid') + 1
        board.save()
        board.refresh_from_db()

        if form_type == 'new_thread':
            thread = create_thread(request, board)
            post = create_post(request, board, thread, form.cleaned_data, is_op=True)
            save_images(post, images)
            thread.op = post
            thread.save()
        else:
            post = create_post(request, board, thread, form.cleaned_data)
            save_images(post, images)
            thread.save()
    #
    # # Handle database errors
    # except DatabaseError as database_error:
    #     print(database_error)  # TODO LOGGING
    #     return handle_error('database_is_broken')
    #
    # # Handle file saving errors
    # except IOError as io_error:
    #     print(io_error)  # TODO LOGGING
    #     return handle_error('storage_is_broken')

    # Redirect to the new thread or post
    if form_type == 'new_post':
        return redirect('thread_page', board_hid=board.hid, thread_hid=thread.hid)
    else:
        return redirect('board_page', board_hid=board.hid)


def get_board(board_id: int) -> Board:
    """Get valid Board model object."""
    try:
        board = Board.objects.get(id=board_id, is_deleted=False)
    except Board.DoesNotExist:
        raise exceptions.BoardNotFound

    # Check board status
    if board.is_locked:
        raise exceptions.BoardIsLocked

    return board


def get_thread(thread_id: int) -> Thread:
    """Get valid Thread model object."""
    try:
        thread = Thread.objects.get(id=thread_id, is_deleted=False)
    except Thread.DoesNotExist:
        raise exceptions.ThreadNotFound

    # Check thread status
    if thread.is_locked:
        raise exceptions.ThreadIsLocked

    # Check thread posts num
    if thread.posts.count() >= thread.max_posts_num:
        raise exceptions.PostLimitWasReached

    return thread


def check_message_content(cleaned_data, images):
    # Check honeypot. Yes, the email field is a honeypot!
    if len(cleaned_data['email']) > 0:
        raise exceptions.BadMessageContent('content is invalid')

    # Check if empty message
    if not cleaned_data['text'] and not images:
        raise exceptions.BadMessageContent('empty message')

    # Check number of files
    if len(images) > config.FILE_MAX_NUM:
        raise exceptions.BadMessageContent('too many files')

    # Check file(s) for field 'file'
    for file_object in images:
        if file_object.size > config.FILE_MAX_SIZE:
            raise exceptions.BadMessageContent('file is too large')
        if file_object.content_type not in config.FILE_MIME_TYPES:
            raise exceptions.BadMessageContent('invalid file type')

    # TODO: remember to check password with regex when saving it


def get_client_ip(request) -> str:
    """Get real client IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def save_images(post: Post, images) -> None:
    """Save all images in request."""
    for image_file in images:
        # Load image with PIL library
        image_pil_object = PIL.Image.open(image_file)

        # Create thumbnail with PIL library
        thumbnail_pil_object = image_pil_object.copy()
        thumbnail_pil_object.thumbnail(config.IMAGE_THUMB_SIZE)

        # Create Django image object
        image = Image(
            post=post,

            original_name=image_file.name,
            mimetype=image_file.content_type,
            size=image_file.size,
            width=image_pil_object.width,
            height=image_pil_object.height,

            thumb_width=thumbnail_pil_object.width,
            thumb_height=thumbnail_pil_object.height,
        )

        # Save image to the database
        image.save()

        # Save image to the disk
        image_full_path = os.path.join(settings.MEDIA_ROOT, image.path())
        with open(image_full_path, 'wb+') as destination:
            for chunk in image_file.chunks(config.IMAGE_CHUNK_SIZE):
                destination.write(chunk)

        # Save thumbnail to the disk
        image_thumb_full_path = os.path.join(settings.MEDIA_ROOT, image.thumb_path())
        thumbnail_pil_object.save(image_thumb_full_path, "PNG")


def create_thread(request, board: Board) -> Thread:
    thread = Thread(
        hid=board.last_post_hid,
        board=board,
        max_posts_num=board.default_max_posts_num,
    )
    thread.save()
    return thread


def create_post(request, board: Board, thread: Thread, cleaned_data: dict, is_op: bool = False) -> Post:
    title = bleach.clean(cleaned_data['title'])
    author = bleach.clean(cleaned_data['author'])
    email = bleach.clean(cleaned_data['email'])
    text = bleach.clean(cleaned_data['text'])
    password = cleaned_data['password']

    post = Post(
        hid=board.last_post_hid,
        thread=thread,

        text=text,
        title=title,
        author=author,
        email=email,  # TODO: save emails
        password=password,  # TODO: save passwords

        is_op=is_op,

        created_by=get_user(request) if request.user.is_authenticated else None,

        ip_address=get_client_ip(request),
    )
    post.save()
    return post
