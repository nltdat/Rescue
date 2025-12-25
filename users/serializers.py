from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from drf_spectacular.utils import extend_schema_field
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model - used for reading user data"""
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'email', 'role', 'profile_image', 'location_lat', 'location_long', 'created_at', 'updated_at']
        read_only_fields = ['id', 'email', 'created_at', 'updated_at']
        
    def to_representation(self, instance):
        """Ensure consistent output format"""
        representation = super().to_representation(instance)
        return representation


class RegisterSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    
    email = serializers.EmailField(
        required=True,
        help_text="Email address (will be used for login)"
    )
    password = serializers.CharField(
        write_only=True,
        min_length=6,
        help_text="Password (minimum 6 characters)",
        style={'input_type': 'password'}
    )
    full_name = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Full name of the user"
    )
    phone = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Phone number"
    )
    role = serializers.ChoiceField(
        choices=['user', 'rescuer', 'admin'], 
        required=False, 
        read_only=True
    )
    location_lat = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Latitude coordinate"
    )
    location_long = serializers.FloatField(
        required=False,
        allow_null=True,
        help_text="Longitude coordinate"
    )

    class Meta:
        model = User
        fields = ['id', 'full_name', 'phone', 'email', 'password', 'role', 'location_lat', 'location_long']
        read_only_fields = ['id']

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data.pop('role', None)
        return User.objects.create_user(**validated_data, password=password, role='user')

class LoginSerializer(TokenObtainPairSerializer):
    """Custom login serializer that uses email instead of username"""
    username_field = 'email'
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Replace username field with email field in the serializer
        self.fields['email'] = serializers.EmailField(required=True, help_text="Email address")
        self.fields['password'] = serializers.CharField(
            required=True,
            write_only=True,
            help_text="Password",
            style={'input_type': 'password'}
        )
        # Remove the default username field
        self.fields.pop('username', None)


class LogoutSerializer(serializers.Serializer):
    """Serializer for logout requests"""
    
    refresh = serializers.CharField(
        required=True,
        help_text="Refresh token to be blacklisted"
    )


class TokenResponseSerializer(serializers.Serializer):
    """Serializer for token response"""
    
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")


class RegisterResponseSerializer(serializers.Serializer):
    """Serializer for registration response"""
    
    user = UserSerializer(help_text="User information")
    access = serializers.CharField(help_text="JWT access token")
    refresh = serializers.CharField(help_text="JWT refresh token")
