from rest_framework import mixins, viewsets

from .models import ContactSubmission
from .permissions import ContactSubmissionPermission
from .serializers import ContactSubmissionSerializer


class ContactSubmissionViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """Create (public) + list (staff) only — a one-way mailbox, not a full CRUD
    resource. No update/destroy: submissions are a record of what a visitor
    sent, not something staff should be able to silently edit."""

    queryset = ContactSubmission.objects.all()
    serializer_class = ContactSubmissionSerializer
    permission_classes = [ContactSubmissionPermission]
