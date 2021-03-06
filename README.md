# hexchan-engine
Hexchan-engine is an anonymous imageboard software written in Python using Django framework.

What's an *imageboard*, you may ask. It's a webforum, where you can post messages without registration 
and pictures are typically used to communicate all sorts of ideas, thus *imageboard*. 
An example would be the infamous 4chan.org.

## Is it deployed somewhere?
Yes, it powers an already existing Russian imageboard **Hexchan** at https://hexchan.org
Feel free to visit us and leave a message in English or Russian.

## Can I use it?
Of course! Hexchan-engine is licensed under MIT license, so you may use it to make your own imageboard.
Although we wouldn't recommend doing this right now, the engine is still a work in progress. 
Also there is no installation manual yet. Stay tuned for our first release!

## What features does it have?
### For users:
* Markup commands (modelled after Wakaba engine's markup)
* Multiple image attachments
* Fullscreen image viewer
* Mobile-friendly layout
* Thread and post hiding
* Reply popup
* User's threads and posts highlighting
### For admins:
* Administrative panel (created with Django Admin module)
* Moderation features: bans, regex-based wordfilter, checksum-based imagefilter
* Captcha
* Hidden boards (active, but not displayed in the board list)
* Sticky threads (always stay at top of the first page)
* Configurable posts and threads limits

## Docker 🐳

You can enable the generation of fake content by setting up 
the env variable `FAKE_CONTENT` to `True` in `docker-compose.yml` (the default is `False`).
**The operation may take several minutes**.

The imageboard will be available on [http://localhost](http://localhost) in your browser. 
And you can login as superuser in the admin panel on [http://localhost/admin](http://localhost/admin).

### Docker Compose

To run the app with database inside docker containers via `docker-compose`: 

```bash
docker-compose build
docker-compose up -d
docker exec -it hexchan_app python src/manage.py createsuperuser
```

To stop app with database's volume removing:

```bash
docker-compose down --volumes
```

### Docker Stack (Swarm)

Run in Docker Swarm cluster do next steps:

```bash
docker-compose build
docker stack deploy -c docker-stack.yml hexchan
```

To stop the stack:

```bash
docker stack rm hexchan
```

### External storage

By default the app stores all media files on local file system. 
If you want to use external storage such as AWS S3 or another compatible storage,
you should to set 3 settings: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY` and `AWS_STORAGE_BUCKET_NAME`.
In case of using the docker compose or stack it's already inside yaml files in commended section.
Also it's done with [django-storages](https://django-storages.readthedocs.io/en/latest/).
It means you can use any of supported storages with minimal code changes.
