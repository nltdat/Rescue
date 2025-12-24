from django.contrib import admin
from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('title', 'incident_type', 'status', 'user', 'created_at')
    list_filter = ('status', 'incident_type', 'created_at')
    search_fields = ('title', 'description', 'user__email', 'user__full_name')
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'incident_type', 'status')
        }),
        ('Location', {
            'fields': ('location_lat', 'location_long')
        }),
        ('Media', {
            'fields': ('images',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
