from rest_framework import generics, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, inline_serializer
from rest_framework import serializers as drf_serializers
from .models import Incident
from .serializers import IncidentSerializer, IncidentListSerializer
from .permissions import IsOwnerOrReadOnly
from .utils import get_minio_client


@extend_schema(
    summary='List all incidents',
    description='Get a list of all incidents. Supports filtering by status, incident_type, and searching.',
    parameters=[
        OpenApiParameter(name='status', description='Filter by status', required=False, type=str),
        OpenApiParameter(name='incident_type', description='Filter by incident type', required=False, type=str),
        OpenApiParameter(name='search', description='Search in title and description', required=False, type=str),
    ],
    responses={200: IncidentListSerializer(many=True)}
)
class IncidentListView(generics.ListAPIView):
    queryset = Incident.objects.select_related('user').all()
    serializer_class = IncidentListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'incident_type']
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@extend_schema(
    summary='Create a new incident',
    description='Create a new incident report. Authenticated users only.',
    request=IncidentSerializer,
    responses={201: IncidentSerializer},
    examples=[
        OpenApiExample(
            'Flood incident example',
            value={
                'title': 'Lũ lụt tại đường Nguyễn Huệ',
                'description': 'Nước ngập sâu khoảng 1.5m, cần cứu hộ khẩn cấp',
                'incident_type': 'flood',
                'location_lat': 10.762622,
                'location_long': 106.660172,
                'images': ['https://example.com/image1.jpg', 'https://example.com/image2.jpg']
            },
            request_only=True
        )
    ]
)
class IncidentCreateView(generics.CreateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@extend_schema(
    summary='Get incident details',
    description='Retrieve detailed information about a specific incident.',
    responses={200: IncidentSerializer}
)
class IncidentDetailView(generics.RetrieveAPIView):
    queryset = Incident.objects.select_related('user').all()
    serializer_class = IncidentSerializer


@extend_schema(
    summary='Update an incident',
    description='Update an incident. Only the owner can update their incident.',
    request=IncidentSerializer,
    responses={200: IncidentSerializer},
    examples=[
        OpenApiExample(
            'Update status example',
            value={
                'status': 'resolved',
                'description': 'Đã được cứu hộ thành công'
            },
            request_only=True
        )
    ]
)
class IncidentUpdateView(generics.UpdateAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


@extend_schema(
    summary='Delete an incident',
    description='Delete an incident. Only the owner can delete their incident.',
    responses={204: None}
)
class IncidentDeleteView(generics.DestroyAPIView):
    queryset = Incident.objects.all()
    serializer_class = IncidentSerializer
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]


@extend_schema(
    summary='Upload images for incident',
    description='Upload one or multiple images to MinIO. Returns URLs of uploaded images.',
    request={
        'multipart/form-data': {
            'type': 'object',
            'properties': {
                'images': {
                    'type': 'array',
                    'items': {
                        'type': 'string',
                        'format': 'binary'
                    }
                }
            }
        }
    },
    responses={
        200: inline_serializer(
            name='ImageUploadResponse',
            fields={
                'urls': drf_serializers.ListField(child=drf_serializers.URLField())
            }
        )
    }
)
class ImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        images = request.FILES.getlist('images')
        
        if not images:
            return Response(
                {'error': 'No images provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate file types and sizes
        ALLOWED_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
        MAX_SIZE = 10 * 1024 * 1024  # 10MB
        
        for image in images:
            if image.content_type not in ALLOWED_TYPES:
                return Response(
                    {'error': f'Invalid file type: {image.content_type}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if image.size > MAX_SIZE:
                return Response(
                    {'error': f'File too large: {image.name}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        uploaded_urls = []
        for image in images:
            try:
                url = get_minio_client().upload_file(image, folder='incidents')
                uploaded_urls.append(url)
            except Exception as e:
                # Cleanup previously uploaded files on failure
                for url in uploaded_urls:
                    try:
                        get_minio_client().delete_file(url)
                    except Exception:
                        pass  # Best effort cleanup
                return Response(
                    {'error': f'Failed to upload image: {e!s}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        
        return Response({'urls': uploaded_urls}, status=status.HTTP_200_OK)

