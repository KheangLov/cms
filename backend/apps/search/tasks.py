from celery import shared_task


@shared_task
def index_page_task(page_id):
    from apps.pages.models import Page

    from .indexing import index_page, remove_page

    try:
        page = Page.all_objects.get(pk=page_id)
    except Page.DoesNotExist:
        remove_page(page_id)
        return
    index_page(page)


@shared_task
def index_post_task(post_id):
    from apps.posts.models import Post

    from .indexing import index_post, remove_post

    try:
        post = Post.all_objects.get(pk=post_id)
    except Post.DoesNotExist:
        remove_post(post_id)
        return
    index_post(post)
