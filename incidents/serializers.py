from rest_framework import serializers
from .models import Incident
from users.serializers import UserSerializer


class IncidentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'user', 'title', 'description', 
            'incident_type', 'location_lat', 'location_long', 
            'images', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']

    def create(self, validated_data):
        # Set user from request context
        request = self.context.get('request')
        if request and request.user:
            validated_data['user'] = request.user
        return super().create(validated_data)


class IncidentListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view"""
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = Incident
        fields = [
            'id', 'user_name', 'user_email', 'title', 
            'incident_type', 'location_lat', 'location_long', 
            'status', 'created_at'
        ]
