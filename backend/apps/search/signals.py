from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blocks.models import PageBlock, PostBlock
from apps.pages.models import Page, PageTranslation
from apps.posts.models import Post, PostTranslation

from .tasks import index_page_task, index_post_task

# Re-index on the page/post itself, its translations, AND its blocks — editing a
# Hero block's heading through the builder changes what should be searchable on
# that page, even though it's a PageBlock save, not a Page save.


@receiver(post_save, sender=Page)
@receiver(post_delete, sender=Page)
def reindex_page(sender, instance, **kwargs):
    index_page_task.delay(instance.id)


@receiver(post_save, sender=PageTranslation)
def reindex_page_translation(sender, instance, **kwargs):
    index_page_task.delay(instance.page_id)


@receiver(post_save, sender=PageBlock)
@receiver(post_delete, sender=PageBlock)
def reindex_page_block(sender, instance, **kwargs):
    index_page_task.delay(instance.page_id)


@receiver(post_save, sender=Post)
@receiver(post_delete, sender=Post)
def reindex_post(sender, instance, **kwargs):
    index_post_task.delay(instance.id)


@receiver(post_save, sender=PostTranslation)
def reindex_post_translation(sender, instance, **kwargs):
    index_post_task.delay(instance.post_id)


@receiver(post_save, sender=PostBlock)
@receiver(post_delete, sender=PostBlock)
def reindex_post_block(sender, instance, **kwargs):
    index_post_task.delay(instance.post_id)
