from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework_datatables.filters import DatatablesFilterBackend
from django.db.models import Q

from cis.utils import CIS_user_only
from ..models import Form1098T
from ..serializers import Form1098TSerializer


class Form1098TViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Form1098T with automatic DataTables support.
    """
    serializer_class = Form1098TSerializer
    permission_classes = [CIS_user_only]
    
    def get_queryset(self):
        """Optimize queryset with select_related and prefetch_related."""
        queryset = Form1098T.objects.select_related(
            'student__user',
            'student__highschool',
            'published_by'
        ).prefetch_related('downloads').filter(is_published=True)
        
        return queryset
