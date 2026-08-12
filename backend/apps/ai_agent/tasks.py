from celery import shared_task

from .providers import AIProviderError, get_provider


def _notify(user_id, task_id, result):
    from apps.realtime.utils import notify_user

    notify_user(user_id, {"event": "ai.completed", "task_id": task_id, **result})


@shared_task(bind=True)
def generate_content_task(self, provider_name, prompt, user_id=None):
    try:
        provider = get_provider(provider_name)
        result = {"ok": True, "result": provider.generate_text(prompt)}
    except AIProviderError as exc:
        result = {"ok": False, "error": str(exc)}
    _notify(user_id, self.request.id, result)
    return result


@shared_task(bind=True)
def translate_content_task(self, provider_name, text, source_locale, target_locale, user_id=None):
    try:
        provider = get_provider(provider_name)
        result = {"ok": True, "result": provider.translate_text(text, source_locale, target_locale)}
    except AIProviderError as exc:
        result = {"ok": False, "error": str(exc)}
    _notify(user_id, self.request.id, result)
    return result
