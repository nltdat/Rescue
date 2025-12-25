from django.db import models
from users.models import User


class RescuerDetail(models.Model):
    AVAILABILITY_AVAILABLE = 'available'
    AVAILABILITY_BUSY = 'busy'
    AVAILABILITY_OFFLINE = 'offline'

    AVAILABILITY_CHOICES = [
        (AVAILABILITY_AVAILABLE, 'Available'),
        (AVAILABILITY_BUSY, 'Busy'),
        (AVAILABILITY_OFFLINE, 'Offline'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='rescuer_detail')
    national_id = models.CharField(max_length=50, unique=True)
    national_id_image = models.URLField(max_length=500, blank=True)  # URL to CCCD image
    skill_set = models.JSONField(default=list)  # ["bơi lội", "sơ cứu", "lái cano"]
    experience_years = models.IntegerField(default=0)
    address = models.TextField(blank=True)
    verified = models.BooleanField(default=False)
    availability_status = models.CharField(
        max_length=20, 
        choices=AVAILABILITY_CHOICES, 
        default=AVAILABILITY_AVAILABLE
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Rescuer: {self.user.email}"

    class Meta:
        verbose_name = 'Rescuer Detail'
        verbose_name_plural = 'Rescuer Details'


class RescueTeam(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    logo_url = models.URLField(max_length=500, blank=True)
    leader = models.ForeignKey(User, on_delete=models.CASCADE, related_name='led_teams')
    area_name = models.CharField(max_length=255)  # Vùng hoạt động
    operating_radius = models.FloatField(help_text='Bán kính hoạt động (km)')
    specialty = models.CharField(max_length=255, blank=True)  # Chuyên môn
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['-created_at']


class TeamMember(models.Model):
    ROLE_LEADER = 'leader'
    ROLE_VICE_LEADER = 'vice_leader'
    ROLE_MEMBER = 'member'

    ROLE_CHOICES = [
        (ROLE_LEADER, 'Leader'),
        (ROLE_VICE_LEADER, 'Vice Leader'),
        (ROLE_MEMBER, 'Member'),
    ]

    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    STATUS_LEFT = 'left'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_LEFT, 'Left'),
    ]

    team = models.ForeignKey(RescueTeam, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='team_memberships')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_MEMBER)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    request_message = models.TextField(blank=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    left_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['team', 'user']
        ordering = ['-joined_at']

    def __str__(self):
        return f"{self.user.email} - {self.team.name} ({self.status})"


class Notification(models.Model):
    TYPE_JOIN_REQUEST = 'join_request'
    TYPE_JOIN_APPROVED = 'join_approved'
    TYPE_JOIN_REJECTED = 'join_rejected'
    TYPE_TASK_ASSIGNED = 'task_assigned'
    TYPE_ALERT = 'alert'
    TYPE_MEMBER_LEFT = 'member_left'

    TYPE_CHOICES = [
        (TYPE_JOIN_REQUEST, 'Join Request'),
        (TYPE_JOIN_APPROVED, 'Join Approved'),
        (TYPE_JOIN_REJECTED, 'Join Rejected'),
        (TYPE_TASK_ASSIGNED, 'Task Assigned'),
        (TYPE_ALERT, 'Alert'),
        (TYPE_MEMBER_LEFT, 'Member Left'),
    ]

    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='sent_notifications')
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    title = models.CharField(max_length=255)
    content = models.TextField()
    related_id = models.IntegerField(null=True, blank=True)  # ID of team or incident
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type} to {self.receiver.email}"
