from rest_framework import serializers
from .models import RescuerDetail, RescueTeam, TeamMember, Notification
from users.serializers import UserSerializer


class RescuerDetailSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.full_name', read_only=True)

    class Meta:
        model = RescuerDetail
        fields = [
            'id', 'user', 'user_email', 'user_name', 'national_id', 
            'national_id_image', 'skill_set', 'experience_years', 
            'address', 'verified', 'availability_status', 'created_at'
        ]
        read_only_fields = ['id', 'verified', 'created_at']


class RescuerRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for rescuer registration"""
    class Meta:
        model = RescuerDetail
        fields = [
            'national_id', 'national_id_image', 'skill_set', 
            'experience_years', 'address'
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        # Check if user already has rescuer detail
        if hasattr(user, 'rescuer_detail'):
            raise serializers.ValidationError('User already registered as rescuer')
        validated_data['user'] = user
        return super().create(validated_data)


class TeamMemberSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    team_name = serializers.CharField(source='team.name', read_only=True)

    class Meta:
        model = TeamMember
        fields = [
            'id', 'team', 'team_name', 'user', 'role', 'status',
            'request_message', 'joined_at', 'left_at'
        ]
        read_only_fields = ['id', 'joined_at', 'left_at']


class RescueTeamSerializer(serializers.ModelSerializer):
    leader = UserSerializer(read_only=True)
    member_count = serializers.SerializerMethodField()
    members = TeamMemberSerializer(many=True, read_only=True)

    class Meta:
        model = RescueTeam
        fields = [
            'id', 'name', 'description', 'logo_url', 'leader',
            'area_name', 'operating_radius', 'specialty', 
            'is_active', 'member_count', 'members', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'leader', 'created_at', 'updated_at']

    def get_member_count(self, obj):
        return obj.members.filter(status=TeamMember.STATUS_APPROVED).count()

    def create(self, validated_data):
        user = self.context['request'].user
        # Check if user is rescuer
        if user.role != 'rescuer':
            raise serializers.ValidationError('Only rescuers can create teams')
        validated_data['leader'] = user
        team = super().create(validated_data)
        
        # Auto add leader as team member
        TeamMember.objects.create(
            team=team,
            user=user,
            role=TeamMember.ROLE_LEADER,
            status=TeamMember.STATUS_APPROVED
        )
        return team


class RescueTeamListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list view"""
    leader_name = serializers.CharField(source='leader.full_name', read_only=True)
    member_count = serializers.SerializerMethodField()

    class Meta:
        model = RescueTeam
        fields = [
            'id', 'name', 'description', 'logo_url', 'leader_name',
            'area_name', 'operating_radius', 'specialty', 
            'is_active', 'member_count', 'created_at'
        ]

    def get_member_count(self, obj):
        return obj.members.filter(status=TeamMember.STATUS_APPROVED).count()


class JoinTeamSerializer(serializers.Serializer):
    """Serializer for joining a team"""
    request_message = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True, allow_null=True)
    sender_email = serializers.EmailField(source='sender.email', read_only=True, allow_null=True)

    class Meta:
        model = Notification
        fields = [
            'id', 'receiver', 'sender', 'sender_name', 'sender_email',
            'type', 'title', 'content', 'related_id', 
            'is_read', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
