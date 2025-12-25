from django.contrib import admin
from .models import RescuerDetail, RescueTeam, TeamMember, Notification


@admin.register(RescuerDetail)
class RescuerDetailAdmin(admin.ModelAdmin):
    list_display = ('user', 'national_id', 'verified', 'availability_status', 'created_at')
    list_filter = ('verified', 'availability_status', 'created_at')
    search_fields = ('user__email', 'user__full_name', 'national_id')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'national_id', 'national_id_image')
        }),
        ('Skills & Experience', {
            'fields': ('skill_set', 'experience_years', 'address')
        }),
        ('Status', {
            'fields': ('verified', 'availability_status')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['verify_rescuers', 'unverify_rescuers']
    
    def verify_rescuers(self, request, queryset):
        # Update rescuer_detail verified status
        count = queryset.update(verified=True)
        # Update user role to rescuer
        user_ids = queryset.values_list('user_id', flat=True)
        from users.models import User
        User.objects.filter(id__in=user_ids).update(role='rescuer')
        self.message_user(request, f'{count} rescuers verified and role updated')
    verify_rescuers.short_description = 'Verify selected rescuers'
    
    def unverify_rescuers(self, request, queryset):
        count = queryset.update(verified=False)
        self.message_user(request, f'{count} rescuers unverified')
    unverify_rescuers.short_description = 'Unverify selected rescuers'


@admin.register(RescueTeam)
class RescueTeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'leader', 'area_name', 'operating_radius', 'is_active', 'created_at')
    list_filter = ('is_active', 'area_name', 'created_at')
    search_fields = ('name', 'description', 'area_name', 'leader__email')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'logo_url', 'leader')
        }),
        ('Operating Area', {
            'fields': ('area_name', 'operating_radius', 'specialty')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ('user', 'team', 'role', 'status', 'joined_at')
    list_filter = ('status', 'role', 'joined_at')
    search_fields = ('user__email', 'user__full_name', 'team__name')
    readonly_fields = ('joined_at', 'left_at')
    
    fieldsets = (
        ('Membership', {
            'fields': ('team', 'user', 'role', 'status')
        }),
        ('Request Details', {
            'fields': ('request_message',)
        }),
        ('Timestamps', {
            'fields': ('joined_at', 'left_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('receiver', 'sender', 'type', 'title', 'is_read', 'created_at')
    list_filter = ('type', 'is_read', 'created_at')
    search_fields = ('receiver__email', 'sender__email', 'title', 'content')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('receiver', 'sender', 'type', 'title', 'content', 'related_id')
        }),
        ('Status', {
            'fields': ('is_read',)
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
