import requests

LOCALE_NAMES = {"en": "English", "km": "Khmer"}


class AIProviderError(Exception):
    pass


class BaseAIProvider:
    def generate_text(self, prompt: str) -> str:
        raise NotImplementedError

    def translate_text(self, text: str, source_locale: str, target_locale: str) -> str:
        """§5.7's translate action — implemented as generate_text with a fixed
        prompt shape, since every provider here only needs to expose one real
        primitive (chat/completion) to support both generate and translate."""
        source = LOCALE_NAMES.get(source_locale, source_locale)
        target = LOCALE_NAMES.get(target_locale, target_locale)
        prompt = (
            f"Translate the following {source} text to {target}. "
            f"Return only the translation, no explanation or preamble.\n\n{text}"
        )
        return self.generate_text(prompt)


class OpenAICompatibleProvider(BaseAIProvider):
    """Shared by OpenAI itself and the generic custom/OpenAI-compatible endpoint
    (§5.7, §10.1) — both speak the same chat-completions request shape."""

    def __init__(self, api_key, base_url="https://api.openai.com/v1", model="gpt-4o-mini"):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def generate_text(self, prompt: str) -> str:
        resp = requests.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={"model": self.model, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise AIProviderError(f"OpenAI-compatible API error {resp.status_code}: {resp.text[:300]}")
        return resp.json()["choices"][0]["message"]["content"].strip()


class AnthropicProvider(BaseAIProvider):
    def __init__(self, api_key, model="claude-sonnet-5"):
        self.api_key = api_key
        self.model = model

    def generate_text(self, prompt: str) -> str:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={"model": self.model, "max_tokens": 1024, "messages": [{"role": "user", "content": prompt}]},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise AIProviderError(f"Anthropic API error {resp.status_code}: {resp.text[:300]}")
        return resp.json()["content"][0]["text"].strip()


class GeminiProvider(BaseAIProvider):
    def __init__(self, api_key, model="gemini-2.0-flash"):
        self.api_key = api_key
        self.model = model

    def generate_text(self, prompt: str) -> str:
        resp = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent",
            params={"key": self.api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=30,
        )
        if resp.status_code >= 400:
            raise AIProviderError(f"Gemini API error {resp.status_code}: {resp.text[:300]}")
        return resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()


PROVIDER_NAMES = ("openai", "anthropic", "gemini", "custom")


def get_setting(key, default=None):
    from apps.settings_app.models import Setting

    try:
        return Setting.objects.get(key=key).value
    except Setting.DoesNotExist:
        return default


def get_provider(name: str) -> BaseAIProvider:
    """Every provider's config lives in the Settings module (§4: "stored via the
    Settings module"), not a dedicated model — Settings already does encrypted
    key/value storage, no need to duplicate it."""
    if name not in PROVIDER_NAMES:
        raise AIProviderError(f"Unknown provider '{name}'. Choices: {', '.join(PROVIDER_NAMES)}")

    api_key = get_setting(f"ai_{name}_api_key")
    if not api_key:
        raise AIProviderError(f"No API key configured for provider '{name}' — set it in Settings first.")

    if name == "openai":
        model = get_setting("ai_openai_model", "gpt-4o-mini")
        return OpenAICompatibleProvider(api_key, model=model)
    if name == "custom":
        base_url = get_setting("ai_custom_base_url")
        if not base_url:
            raise AIProviderError("ai_custom_base_url must be set in Settings for the custom provider.")
        model = get_setting("ai_custom_model", "gpt-4o-mini")
        return OpenAICompatibleProvider(api_key, base_url=base_url, model=model)
    if name == "anthropic":
        model = get_setting("ai_anthropic_model", "claude-sonnet-5")
        return AnthropicProvider(api_key, model=model)
    model = get_setting("ai_gemini_model", "gemini-2.0-flash")
    return GeminiProvider(api_key, model=model)
