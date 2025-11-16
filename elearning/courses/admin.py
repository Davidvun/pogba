from django.contrib import admin
from .models import Category, Course, Unit, Video, Material, VideoWatch, Attendance, CourseEnrollment

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'tutor', 'category', 'price', 'is_free', 'is_approved', 'created_at']
    list_filter = ['is_free', 'is_approved', 'category']
    search_fields = ['title', 'tutor__username']
    prepopulated_fields = {'slug': ('title',)}

@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'created_at']
    list_filter = ['course']
    search_fields = ['title', 'course__title']

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit', 'duration', 'is_free', 'order']
    list_filter = ['is_free', 'unit__course']
    search_fields = ['title', 'unit__title']

@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit', 'material_type', 'is_free', 'is_downloadable']
    list_filter = ['material_type', 'is_free']
    search_fields = ['title', 'unit__title']

@admin.register(VideoWatch)
class VideoWatchAdmin(admin.ModelAdmin):
    list_display = ['student', 'video', 'progress', 'is_completed', 'updated_at']
    list_filter = ['is_completed', 'is_active']
    search_fields = ['student__username', 'video__title']

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ['student', 'video', 'date', 'active_watch_time', 'is_present']
    list_filter = ['is_present', 'date']
    search_fields = ['student__username', 'video__title']

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'enrolled_at', 'is_active', 'progress']
    list_filter = ['is_active', 'enrolled_at']
    search_fields = ['student__username', 'course__title']
