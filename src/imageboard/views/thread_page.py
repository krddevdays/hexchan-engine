# Standard import
import datetime

# Django imports
from django.template.loader import render_to_string
from django.db.models import Prefetch
from django.http import HttpResponse, Http404
from django.core.cache import cache

# App imports
from imageboard.models import Board, Thread, Post
from imageboard.forms import PostingForm


def thread_page(request, board_hid, thread_hid):
    # Get boards
    boards = Board.objects.order_by('hid').all()

    # Get current board
    try:
        board = boards.get(hid=board_hid, is_deleted=False)
    except Board.DoesNotExist:
        raise Http404('Board not found')

    # Thread queryset
    try:
        thread = Thread.objects.get(board__hid=board_hid, hid=thread_hid, is_deleted=False)
    except Thread.DoesNotExist:
        raise Http404('Thread not found')

    # Get cached page if exists and return it
    cache_key = 'thread_page__{board_hid}__{thread_hid}'.format(board_hid=board_hid, thread_hid=thread_hid)
    cache_record = cache.get(cache_key)
    if cache_record is not None and not request.user.is_authenticated:
        timestamp, rendered_template = cache_record
        if thread.updated_at == timestamp:
            return HttpResponse(rendered_template)

    # Refs and replies queryset
    refs_and_replies_queryset = Post.objects\
        .select_related('thread', 'thread__board')\
        .only('is_op', 'hid', 'thread__hid', 'thread__board__hid')

    # Combine prefetch args, also prefetch required images
    prefetch_args = [
        Prefetch('op'),
        Prefetch('op__images'),
        Prefetch('op__replies', queryset=refs_and_replies_queryset),
        Prefetch('op__post_set', queryset=refs_and_replies_queryset, to_attr='refs'),
        Prefetch('posts', queryset=Post.objects.filter(is_op=False)),
        Prefetch('posts__images'),
        Prefetch('posts__replies', queryset=refs_and_replies_queryset),
        Prefetch('posts__post_set', queryset=refs_and_replies_queryset, to_attr='refs'),
    ]

    # Prefetch stuff for the thread
    thread = Thread.objects\
        .select_related('board')\
        .prefetch_related(*prefetch_args) \
        .get(board__hid=board_hid, hid=thread_hid, is_deleted=False)

    # Init post creation form
    form = PostingForm(
        initial={
            'form_type': 'new_post',
            'board_id': board.id,
            'thread_id': thread.id
        },
    )

    # Cache data
    cache_data = {
        'updated_at': thread.updated_at,
        'generated_at': datetime.datetime.now(),
        'board': board,
        'thread': thread,
    }

    # Render template
    rendered_template = render_to_string(
        'imageboard/thread_page.html',
        {
            'form': form,
            'board': board,
            'boards': boards,
            'thread': thread,
            'cache_data': cache_data,
        },
        request
    )

    # Write page to cache
    if not request.user.is_authenticated:
        new_cache_record = (thread.updated_at, rendered_template,)
        cache.set(cache_key, new_cache_record)

    # Return response
    return HttpResponse(rendered_template)
