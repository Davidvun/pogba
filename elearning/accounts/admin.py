from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserSession, ActivityLog

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'role', 'is_active', 'is_suspended']
    list_filter = ['role', 'is_active', 'is_suspended']
    fieldsets = UserAdmin.fieldsets + (
        ('Role & Status', {'fields': ('role', 'is_suspended', 'phone', 'email_verified', 'phone_verified')}),
        ('Profile', {'fields': ('profile_picture', 'bio')}),
    )

@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_info', 'ip_address', 'is_active', 'last_activity']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__username', 'device_info', 'ip_address']

@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'ip_address', 'timestamp']
    list_filter = ['timestamp']
    search_fields = ['user__username', 'action', 'description']
