from rest_framework import generics, permissions, status, filters
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from django.db.models import Q
from django.utils import timezone
import math

from .models import RescuerDetail, RescueTeam, TeamMember, Notification
from .serializers import (
    RescuerDetailSerializer, RescuerRegistrationSerializer,
    RescueTeamSerializer, RescueTeamListSerializer, TeamMemberSerializer,
    JoinTeamSerializer, NotificationSerializer
)
from users.models import User


# ========== RESCUER APIS ==========

@extend_schema(
    summary='Register as rescuer',
    description='User registers to become a rescuer. Requires admin approval.',
    request=RescuerRegistrationSerializer,
    responses={201: RescuerDetailSerializer},
    examples=[
        OpenApiExample(
            'Rescuer registration',
            value={
                'national_id': '001234567890',
                'national_id_image': 'http://localhost:9000/rescue-images/cccd/xxx.jpg',
                'skill_set': ['bơi lội', 'sơ cứu', 'lái cano'],
                'experience_years': 3,
                'address': '123 Nguyễn Huệ, Quận 1, TP.HCM'
            },
            request_only=True
        )
    ]
)
class RescuerRegisterView(generics.CreateAPIView):
    serializer_class = RescuerRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        rescuer_detail = serializer.save()
        # Note: Admin needs to verify and update user.role to 'rescuer'
        return rescuer_detail


@extend_schema(
    summary='Get rescuer profile',
    description='View rescuer details by user ID',
    responses={200: RescuerDetailSerializer}
)
class RescuerProfileView(generics.RetrieveAPIView):
    queryset = RescuerDetail.objects.select_related('user').all()
    serializer_class = RescuerDetailSerializer
    lookup_field = 'user_id'


@extend_schema(
    summary='Update rescuer availability status',
    description='Rescuer updates their availability status (available/busy/offline)',
    request=RescuerDetailSerializer,
    responses={200: RescuerDetailSerializer}
)
class RescuerStatusUpdateView(generics.UpdateAPIView):
    serializer_class = RescuerDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        try:
            return self.request.user.rescuer_detail
        except RescuerDetail.DoesNotExist:
            return Response(
                {'error': 'User is not a rescuer'},
                status=status.HTTP_404_NOT_FOUND
            )


# ========== TEAM APIS ==========

@extend_schema(
    summary='List all rescue teams',
    description='Get list of all rescue teams. Supports filtering by area and searching nearby teams.',
    parameters=[
        OpenApiParameter(name='area_name', description='Filter by area', type=str),
        OpenApiParameter(name='lat', description='User latitude for nearby search', type=float),
        OpenApiParameter(name='lng', description='User longitude for nearby search', type=float),
        OpenApiParameter(name='radius', description='Search radius in km (default: 50)', type=float),
        OpenApiParameter(name='search', description='Search in name, description, specialty', type=str),
    ],
    responses={200: RescueTeamListSerializer(many=True)}
)
class TeamListView(generics.ListAPIView):
    serializer_class = RescueTeamListSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['area_name', 'is_active']
    search_fields = ['name', 'description', 'specialty']

    def get_queryset(self):
        queryset = RescueTeam.objects.filter(is_active=True).select_related('leader')
        
        # Nearby search by coordinates
        lat = self.request.query_params.get('lat')
        lng = self.request.query_params.get('lng')
        radius = float(self.request.query_params.get('radius', 50))  # default 50km
        
        if lat and lng:
            lat = float(lat)
            lng = float(lng)
            # Filter teams within operating radius
            # Note: This is a simple filter, for production use PostGIS
            nearby_teams = []
            for team in queryset:
                if team.leader.location_lat and team.leader.location_long:
                    distance = self._calculate_distance(
                        lat, lng,
                        team.leader.location_lat, team.leader.location_long
                    )
                    if distance <= radius:
                        nearby_teams.append(team.id)
            queryset = queryset.filter(id__in=nearby_teams)
        
        return queryset

    def _calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points in km using Haversine formula"""
        R = 6371  # Earth radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c


@extend_schema(
    summary='Create new rescue team',
    description='Create a new rescue team. Only rescuers can create teams.',
    request=RescueTeamSerializer,
    responses={201: RescueTeamSerializer},
    examples=[
        OpenApiExample(
            'Team creation',
            value={
                'name': 'Đội cứu hộ Quận 7',
                'description': 'Chuyên cứu hộ lũ lụt khu vực Quận 7',
                'logo_url': 'http://localhost:9000/rescue-images/teams/logo.jpg',
                'area_name': 'Quận 7, TP.HCM',
                'operating_radius': 15.0,
                'specialty': 'Cứu hộ lũ lụt'
            },
            request_only=True
        )
    ]
)
class TeamCreateView(generics.CreateAPIView):
    serializer_class = RescueTeamSerializer
    permission_classes = [permissions.IsAuthenticated]


@extend_schema(
    summary='Get team details',
    description='Get detailed information about a rescue team including members',
    responses={200: RescueTeamSerializer}
)
class TeamDetailView(generics.RetrieveAPIView):
    queryset = RescueTeam.objects.prefetch_related('members__user').all()
    serializer_class = RescueTeamSerializer


@extend_schema(
    summary='Get team members',
    description='Get list of team members with their status',
    parameters=[
        OpenApiParameter(name='status', description='Filter by status (pending/approved/rejected/left)', type=str),
    ],
    responses={200: TeamMemberSerializer(many=True)}
)
class TeamMembersView(generics.ListAPIView):
    serializer_class = TeamMemberSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'role']

    def get_queryset(self):
        team_id = self.kwargs.get('pk')
        return TeamMember.objects.filter(team_id=team_id).select_related('user', 'team')


# ========== TEAM MEMBERSHIP APIS ==========

@extend_schema(
    summary='Join a team',
    description='Send request to join a rescue team. Creates notification for team leader.',
    request=JoinTeamSerializer,
    responses={201: TeamMemberSerializer},
    examples=[
        OpenApiExample(
            'Join request',
            value={
                'request_message': 'Tôi có kinh nghiệm 3 năm cứu hộ lũ lụt, mong được tham gia đội'
            },
            request_only=True
        )
    ]
)
class JoinTeamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            team = RescueTeam.objects.get(pk=pk)
        except RescueTeam.DoesNotExist:
            return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)

        user = request.user

        # Check if user is rescuer
        if user.role != 'rescuer':
            return Response(
                {'error': 'Only rescuers can join teams'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if already a member
        existing = TeamMember.objects.filter(team=team, user=user).first()
        if existing:
            if existing.status == TeamMember.STATUS_APPROVED:
                return Response({'error': 'Already a member'}, status=status.HTTP_400_BAD_REQUEST)
            elif existing.status == TeamMember.STATUS_PENDING:
                return Response({'error': 'Join request already pending'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = JoinTeamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Create membership request
        membership = TeamMember.objects.create(
            team=team,
            user=user,
            status=TeamMember.STATUS_PENDING,
            request_message=serializer.validated_data.get('request_message', '')
        )

        # Create notification for team leader
        Notification.objects.create(
            receiver=team.leader,
            sender=user,
            type=Notification.TYPE_JOIN_REQUEST,
            title=f'Yêu cầu tham gia nhóm {team.name}',
            content=f'{user.full_name} muốn tham gia nhóm {team.name}. Lời nhắn: {membership.request_message}',
            related_id=membership.id
        )

        return Response(
            TeamMemberSerializer(membership).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    summary='Approve/Reject team join request',
    description='Leader approves or rejects a team join request',
    request=TeamMemberSerializer,
    responses={200: TeamMemberSerializer}
)
class ApproveMembershipView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, membership_id):
        try:
            membership = TeamMember.objects.select_related('team', 'user').get(pk=membership_id)
        except TeamMember.DoesNotExist:
            return Response({'error': 'Membership not found'}, status=status.HTTP_404_NOT_FOUND)

        # Check if user is team leader
        if membership.team.leader != request.user:
            return Response(
                {'error': 'Only team leader can approve/reject'},
                status=status.HTTP_403_FORBIDDEN
            )

        new_status = request.data.get('status')
        if new_status not in [TeamMember.STATUS_APPROVED, TeamMember.STATUS_REJECTED]:
            return Response(
                {'error': 'Status must be approved or rejected'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.status = new_status
        membership.save()

        # Create notification for user
        notification_type = (Notification.TYPE_JOIN_APPROVED 
                           if new_status == TeamMember.STATUS_APPROVED 
                           else Notification.TYPE_JOIN_REJECTED)
        
        Notification.objects.create(
            receiver=membership.user,
            sender=request.user,
            type=notification_type,
            title=f'Yêu cầu tham gia nhóm {membership.team.name}',
            content=f'Yêu cầu tham gia nhóm {membership.team.name} đã được {"chấp nhận" if new_status == TeamMember.STATUS_APPROVED else "từ chối"}',
            related_id=membership.team.id
        )

        return Response(TeamMemberSerializer(membership).data)


@extend_schema(
    summary='Leave team',
    description='Member leaves a rescue team',
    responses={200: {'description': 'Successfully left the team'}}
)
class LeaveTeamView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, pk):
        try:
            team = RescueTeam.objects.get(pk=pk)
        except RescueTeam.DoesNotExist:
            return Response({'error': 'Team not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            membership = TeamMember.objects.get(team=team, user=request.user)
        except TeamMember.DoesNotExist:
            return Response({'error': 'Not a team member'}, status=status.HTTP_404_NOT_FOUND)

        # Leader cannot leave
        if membership.role == TeamMember.ROLE_LEADER:
            return Response(
                {'error': 'Leader cannot leave the team. Transfer leadership first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.status = TeamMember.STATUS_LEFT
        membership.left_at = timezone.now()
        membership.save()

        # Notify leader
        Notification.objects.create(
            receiver=team.leader,
            sender=request.user,
            type=Notification.TYPE_MEMBER_LEFT,
            title=f'Thành viên rời nhóm {team.name}',
            content=f'{request.user.full_name} đã rời khỏi nhóm {team.name}',
            related_id=team.id
        )

        return Response({'message': 'Successfully left the team'})


# ========== NOTIFICATION APIS ==========

@extend_schema(
    summary='List user notifications',
    description='Get list of notifications for current user',
    parameters=[
        OpenApiParameter(name='is_read', description='Filter by read status', type=bool),
        OpenApiParameter(name='type', description='Filter by notification type', type=str),
    ],
    responses={200: NotificationSerializer(many=True)}
)
class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['is_read', 'type']

    def get_queryset(self):
        return Notification.objects.filter(receiver=self.request.user).select_related('sender')


@extend_schema(
    summary='Mark notification as read',
    description='Mark a notification as read',
    responses={200: NotificationSerializer}
)
class MarkNotificationReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk, receiver=request.user)
        except Notification.DoesNotExist:
            return Response({'error': 'Notification not found'}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save()

        return Response(NotificationSerializer(notification).data)


@extend_schema(
    summary='Mark all notifications as read',
    description='Mark all notifications for current user as read',
    responses={200: {'description': 'All notifications marked as read'}}
)
class MarkAllNotificationsReadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        count = Notification.objects.filter(
            receiver=request.user,
            is_read=False
        ).update(is_read=True)

        return Response({'message': f'{count} notifications marked as read'})
