from django.urls import path

from .views import AIProviderStatusView, GenerateContentView, TaskStatusView, TranslateContentView

urlpatterns = [
    path("ai/generate/", GenerateContentView.as_view(), name="ai-generate"),
    path("ai/translate/", TranslateContentView.as_view(), name="ai-translate"),
    path("ai/tasks/<str:task_id>/", TaskStatusView.as_view(), name="ai-task-status"),
    path("ai/providers/", AIProviderStatusView.as_view(), name="ai-provider-status"),
]
