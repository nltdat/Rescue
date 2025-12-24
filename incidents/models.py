from django.db import models
from users.models import User


class Incident(models.Model):
    INCIDENT_TYPE_FLOOD = 'flood'
    INCIDENT_TYPE_FIRE = 'fire'
    INCIDENT_TYPE_EARTHQUAKE = 'earthquake'
    INCIDENT_TYPE_STORM = 'storm'
    INCIDENT_TYPE_ACCIDENT = 'accident'
    INCIDENT_TYPE_MEDICAL = 'medical'
    INCIDENT_TYPE_OTHER = 'other'

    INCIDENT_TYPE_CHOICES = [
        (INCIDENT_TYPE_FLOOD, 'Flood'),
        (INCIDENT_TYPE_FIRE, 'Fire'),
        (INCIDENT_TYPE_EARTHQUAKE, 'Earthquake'),
        (INCIDENT_TYPE_STORM, 'Storm'),
        (INCIDENT_TYPE_ACCIDENT, 'Accident'),
        (INCIDENT_TYPE_MEDICAL, 'Medical Emergency'),
        (INCIDENT_TYPE_OTHER, 'Other'),
    ]

    STATUS_OPEN = 'open'
    STATUS_ASSIGNED = 'assigned'
    STATUS_IN_PROGRESS = 'in_progress'
    STATUS_RESOLVED = 'resolved'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Open'),
        (STATUS_ASSIGNED, 'Assigned'),
        (STATUS_IN_PROGRESS, 'In Progress'),
        (STATUS_RESOLVED, 'Resolved'),
        (STATUS_CLOSED, 'Closed'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='incidents')
    title = models.CharField(max_length=255)
    description = models.TextField()
    incident_type = models.CharField(max_length=50, choices=INCIDENT_TYPE_CHOICES)
    location_lat = models.FloatField()
    location_long = models.FloatField()
    images = models.JSONField(default=list, blank=True)  # Store list of image URLs
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=STATUS_OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['incident_type']),
        ]

    def __str__(self):
        return f"{self.incident_type.upper()}: {self.title}"
