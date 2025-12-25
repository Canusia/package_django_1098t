# webapp/django_1098t/django_1098t/serializers.py

from rest_framework import serializers
from .models import Form1098T

# webapp/django_1098t/django_1098t/serializers.py

from rest_framework import serializers
from .models import Form1098T


class Form1098TSerializer(serializers.ModelSerializer):
    """Serializer for Form1098T with DataTables support."""
    
    # Flattened fields for DataTables columns
    tax_year = serializers.IntegerField()
    published_at = serializers.DateTimeField(format='%Y-%m-%d %H:%M')
    
    # Student information (flattened dot notation)
    student_user_last_name = serializers.CharField(source='student.user.last_name', read_only=True)
    student_user_first_name = serializers.CharField(source='student.user.first_name', read_only=True)
    student_user_email = serializers.EmailField(source='student.user.email', read_only=True)
    student_highschool_name = serializers.CharField(
        source='student.highschool.name', 
        read_only=True, 
        allow_null=True,
        default=''
    )
    
    # Published by
    published_by_email = serializers.EmailField(
        source='published_by.email', 
        read_only=True, 
        allow_null=True,
        default=''
    )
    
    # Download info
    download_count = serializers.IntegerField(read_only=True)
    download_url = serializers.CharField(read_only=True)
    
    class Meta:
        model = Form1098T
        fields = [
            'id',
            'tax_year',
            'published_at',
            'student_user_first_name',
            'student_user_last_name',
            'student_user_email',
            'student_highschool_name',
            'published_by_email',
            'download_count',
            'download_url',
        ]
        
        # DataTables configuration
        datatables_always_serialize = ('id',)