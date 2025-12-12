from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse, OpenApiParameter
from drf_spectacular.types import OpenApiTypes

from .models import User
from .serializers import (
    UserSerializer, 
    RegisterSerializer, 
    LoginSerializer,
    LogoutSerializer,
    TokenResponseSerializer,
    RegisterResponseSerializer
)
from .permissions import IsAdminRole


@extend_schema(
    summary='Register a new user',
    description='Create a new user account and receive JWT tokens for authentication',
    request=RegisterSerializer,
    responses={
        201: RegisterResponseSerializer,
        400: OpenApiResponse(description='Bad request - validation errors')
    },
    examples=[
        OpenApiExample(
            'Register User Example',
            value={
                'email': 'user@example.com',
                'password': 'securepass123',
                'full_name': 'Nguyen Van A',
                'phone': '0901234567',
                'role': 'user',
                'location_lat': 10.762622,
                'location_long': 106.660172
            },
            request_only=True,
        ),
        OpenApiExample(
            'Register Response Example',
            value={
                'user': {
                    'id': 1,
                    'email': 'user@example.com',
                    'full_name': 'Nguyen Van A',
                    'phone': '0901234567',
                    'role': 'user',
                    'location_lat': 10.762622,
                    'location_long': 106.660172,
                    'created_at': '2025-12-12T14:30:00Z',
                    'updated_at': '2025-12-12T14:30:00Z'
                },
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGc...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGc...'
            },
            response_only=True,
            status_codes=['201']
        )
    ],
    tags=['Authentication']
)
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        data = {
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }
        return Response(data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary='Login with email and password',
    description='Authenticate user and receive JWT access and refresh tokens',
    request=LoginSerializer,
    responses={
        200: TokenResponseSerializer,
        401: OpenApiResponse(description='Unauthorized - invalid credentials')
    },
    examples=[
        OpenApiExample(
            'Login Request Example',
            value={
                'email': 'user@example.com',
                'password': 'securepass123'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Login Response Example',
            value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            },
            response_only=True,
            status_codes=['200']
        )
    ],
    tags=['Authentication']
)
class LoginView(TokenObtainPairView):
    """Login endpoint - returns JWT tokens"""
    serializer_class = LoginSerializer


@extend_schema(
    summary='Logout and blacklist refresh token',
    description='Logout user by blacklisting the refresh token. Requires authentication.',
    request=LogoutSerializer,
    responses={
        205: OpenApiResponse(description='Successfully logged out'),
        400: OpenApiResponse(description='Bad request - invalid or missing refresh token'),
        401: OpenApiResponse(description='Unauthorized - authentication required')
    },
    examples=[
        OpenApiExample(
            'Logout Request Example',
            value={
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            },
            request_only=True,
        )
    ],
    tags=['Authentication']
)
class LogoutView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    summary='Refresh access token',
    description='Get a new access token using a valid refresh token',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh': {
                    'type': 'string',
                    'description': 'Refresh token'
                }
            },
            'required': ['refresh']
        }
    },
    responses={
        200: OpenApiResponse(description='New access token'),
        401: OpenApiResponse(description='Invalid or expired refresh token')
    },
    examples=[
        OpenApiExample(
            'Token Refresh Request',
            value={
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            },
            request_only=True,
        ),
        OpenApiExample(
            'Token Refresh Response',
            value={
                'access': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...',
                'refresh': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...'
            },
            response_only=True,
            status_codes=['200']
        )
    ],
    tags=['Authentication']
)
class TokenRefreshAPIView(TokenRefreshView):
    """Refresh token endpoint - returns new access token"""
    pass


@extend_schema(
    summary='Get or update current user profile',
    description='Retrieve or update the authenticated user profile. Requires authentication.',
    request=UserSerializer,
    responses={
        200: UserSerializer,
        401: OpenApiResponse(description='Unauthorized - authentication required')
    },
    examples=[
        OpenApiExample(
            'Get Profile Response',
            value={
                'id': 1,
                'email': 'user@example.com',
                'full_name': 'Nguyen Van A',
                'phone': '0901234567',
                'role': 'user',
                'location_lat': 10.762622,
                'location_long': 106.660172,
                'created_at': '2025-12-12T14:30:00Z',
                'updated_at': '2025-12-12T14:30:00Z'
            },
            response_only=True,
            status_codes=['200']
        ),
        OpenApiExample(
            'Update Profile Request',
            value={
                'full_name': 'Nguyen Van B',
                'phone': '0907654321',
                'location_lat': 10.823099,
                'location_long': 106.629662
            },
            request_only=True,
        )
    ],
    tags=['User Profile']
)
class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_object(self):
        return self.request.user


@extend_schema(
    summary='List all users (Admin only)',
    description='Get a list of all registered users. Only accessible by admin users.',
    responses={
        200: UserSerializer(many=True),
        401: OpenApiResponse(description='Unauthorized - authentication required'),
        403: OpenApiResponse(description='Forbidden - admin access required')
    },
    examples=[
        OpenApiExample(
            'User List Response',
            value=[
                {
                    'id': 1,
                    'email': 'user1@example.com',
                    'full_name': 'Nguyen Van A',
                    'phone': '0901234567',
                    'role': 'user',
                    'location_lat': 10.762622,
                    'location_long': 106.660172,
                    'created_at': '2025-12-12T14:30:00Z',
                    'updated_at': '2025-12-12T14:30:00Z'
                },
                {
                    'id': 2,
                    'email': 'rescuer@example.com',
                    'full_name': 'Tran Thi B',
                    'phone': '0909876543',
                    'role': 'rescuer',
                    'location_lat': 10.823099,
                    'location_long': 106.629662,
                    'created_at': '2025-12-12T15:00:00Z',
                    'updated_at': '2025-12-12T15:00:00Z'
                }
            ],
            response_only=True,
            status_codes=['200']
        )
    ],
    tags=['User Management']
)
class UserListView(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (IsAdminRole,)
