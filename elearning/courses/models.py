from django.db import models
from django.conf import settings
from django.utils.text import slugify

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']


class Course(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField()
    tutor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='courses')
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='courses')
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    is_free = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title
    
    def get_total_units(self):
        return self.units.count()
    
    def get_enrolled_students(self):
        from elearning.payments.models import Purchase
        return Purchase.objects.filter(course=self, status='completed').count()
    
    class Meta:
        ordering = ['-created_at']


class Unit(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='units')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.course.title} - {self.title}"
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']


class Video(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='videos')
    title = models.CharField(max_length=200)
    video_url = models.URLField(help_text="Video URL (YouTube, Vimeo, or direct link)")
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    thumbnail = models.ImageField(upload_to='video_thumbnails/', blank=True, null=True)
    duration = models.PositiveIntegerField(help_text="Duration in seconds", default=0)
    order = models.PositiveIntegerField(default=0)
    is_free = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.unit.title} - {self.title}"
    
    class Meta:
        ordering = ['order']
        unique_together = ['unit', 'order']


class Material(models.Model):
    MATERIAL_TYPES = [
        ('pdf', 'PDF'),
        ('doc', 'Document'),
        ('slide', 'Slides'),
        ('other', 'Other'),
    ]
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    file = models.FileField(upload_to='materials/')
    material_type = models.CharField(max_length=10, choices=MATERIAL_TYPES, default='pdf')
    is_free = models.BooleanField(default=False)
    is_downloadable = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
    
    class Meta:
        ordering = ['title']


class MaterialView(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='material_views')
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name='views')
    is_completed = models.BooleanField(default=False)
    viewed_at = models.DateTimeField(auto_now_add=True)
    last_viewed_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.material.title}"
    
    class Meta:
        unique_together = ['student', 'material']
        ordering = ['-last_viewed_at']


class VideoWatch(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_watches')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='watches')
    watch_time = models.PositiveIntegerField(default=0, help_text="Total watch time in seconds")
    progress = models.FloatField(default=0.0, help_text="Percentage watched (0-100)")
    is_completed = models.BooleanField(default=False)
    last_position = models.PositiveIntegerField(default=0, help_text="Last watched position in seconds")
    is_active = models.BooleanField(default=False, help_text="Is currently watching")
    started_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.video.title}"
    
    class Meta:
        unique_together = ['student', 'video']
        ordering = ['-updated_at']


class Attendance(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='attendances')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='attendances')
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(auto_now_add=True)
    active_watch_time = models.PositiveIntegerField(default=0, help_text="Active watch time in seconds")
    is_present = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.username} - {self.video.title} - {self.date}"
    
    class Meta:
        unique_together = ['student', 'video', 'date']
        ordering = ['-date']


class CourseEnrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    progress = models.FloatField(default=0.0, help_text="Course completion percentage")
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title}"
    
    class Meta:
        unique_together = ['student', 'course']
        ordering = ['-enrolled_at']
