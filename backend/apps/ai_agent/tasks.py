from celery import shared_task

from .providers import AIProviderError, get_provider


@shared_task
def generate_content_task(provider_name, prompt):
    try:
        provider = get_provider(provider_name)
        return {"ok": True, "result": provider.generate_text(prompt)}
    except AIProviderError as exc:
        return {"ok": False, "error": str(exc)}


@shared_task
def translate_content_task(provider_name, text, source_locale, target_locale):
    try:
        provider = get_provider(provider_name)
        return {"ok": True, "result": provider.translate_text(text, source_locale, target_locale)}
    except AIProviderError as exc:
        return {"ok": False, "error": str(exc)}
