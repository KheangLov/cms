from celery.result import AsyncResult
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .providers import PROVIDER_NAMES, get_setting
from .tasks import generate_content_task, translate_content_task


class GenerateContentView(APIView):
    """§5.7 — runs as a Celery task so the request/response cycle never blocks on
    a slow AI call (§6.1). Delivery is poll-based for now via TaskStatusView;
    Phase 8 adds a WebSocket push on top of this once Channels consumers exist —
    polling stays as the fallback, it isn't replaced."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        prompt = request.data.get("prompt")
        provider = request.data.get("provider", "openai")
        if not prompt:
            return Response({"detail": "prompt is required"}, status=400)
        task = generate_content_task.delay(provider, prompt, user_id=request.user.id)
        return Response({"task_id": task.id}, status=202)


class TranslateContentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        text = request.data.get("text")
        source_locale = request.data.get("source_locale", "en")
        target_locale = request.data.get("target_locale", "km")
        provider = request.data.get("provider", "openai")
        if not text:
            return Response({"detail": "text is required"}, status=400)
        task = translate_content_task.delay(provider, text, source_locale, target_locale, user_id=request.user.id)
        return Response({"task_id": task.id}, status=202)


class TaskStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, task_id):
        result = AsyncResult(task_id)
        payload = {"task_id": task_id, "status": result.status}
        if result.successful():
            payload.update(result.result)
        elif result.failed():
            payload["ok"] = False
            payload["error"] = str(result.result)
        return Response(payload)


class AIProviderStatusView(APIView):
    """Lets the admin UI show "Connected: OpenAI, Anthropic" (§11's design
    preview already mocked this) without ever exposing the actual keys."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({name: bool(get_setting(f"ai_{name}_api_key")) for name in PROVIDER_NAMES})
