from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Avg
from django.core.paginator import Paginator
from elearning.accounts.decorators import admin_required, tutor_required, student_required
from .models import Course, Category, Unit, Video, Material, CourseEnrollment, VideoWatch, Attendance, MaterialView
from elearning.accounts.models import User
from elearning.quizzes.models import Quiz, Question, Answer
from elearning.payments.models import Purchase
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
import json


@admin_required
def admin_create_course(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        tutor_id = request.POST.get('tutor')
        category_id = request.POST.get('category')
        price = request.POST.get('price', 0)
        is_free = request.POST.get('is_free') == 'on'
        thumbnail = request.FILES.get('thumbnail')
        
        tutor = get_object_or_404(User, id=tutor_id, role='tutor')
        category = get_object_or_404(Category, id=category_id) if category_id else None
        
        course = Course.objects.create(
            title=title,
            description=description,
            tutor=tutor,
            category=category,
            price=price if not is_free else 0,
            is_free=is_free,
            thumbnail=thumbnail,
            is_approved=True
        )
        
        messages.success(request, f'Course "{course.title}" created successfully!')
        return redirect('admin_manage_courses')
    
    tutors = User.objects.filter(role='tutor')
    categories = Category.objects.all()
    return render(request, 'courses/admin_create_course.html', {
        'tutors': tutors,
        'categories': categories
    })


@admin_required
def admin_manage_courses(request):
    courses = Course.objects.all().select_related('tutor', 'category')
    return render(request, 'courses/admin_manage_courses.html', {'courses': courses})


@admin_required
def admin_edit_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course.title = request.POST.get('title')
        course.description = request.POST.get('description')
        course.price = request.POST.get('price', 0)
        course.is_free = request.POST.get('is_free') == 'on'
        course.is_published = request.POST.get('is_published') == 'on'
        
        if request.FILES.get('thumbnail'):
            course.thumbnail = request.FILES.get('thumbnail')
        
        tutor_id = request.POST.get('tutor')
        if tutor_id:
            course.tutor = get_object_or_404(User, id=tutor_id, role='tutor')
        
        category_id = request.POST.get('category')
        if category_id:
            course.category = get_object_or_404(Category, id=category_id)
        
        course.save()
        messages.success(request, f'Course "{course.title}" updated successfully!')
        return redirect('admin_manage_courses')
    
    tutors = User.objects.filter(role='tutor')
    categories = Category.objects.all()
    return render(request, 'courses/admin_edit_course.html', {
        'course': course,
        'tutors': tutors,
        'categories': categories
    })


@admin_required
def admin_delete_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    title = course.title
    course.delete()
    messages.success(request, f'Course "{title}" deleted successfully!')
    return redirect('admin_manage_courses')


@tutor_required
def tutor_my_courses(request):
    courses = Course.objects.filter(tutor=request.user).prefetch_related('units')
    return render(request, 'courses/tutor_my_courses.html', {'courses': courses})


@tutor_required
def tutor_course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id, tutor=request.user)
    units = course.units.prefetch_related('videos', 'materials').all()
    return render(request, 'courses/tutor_course_detail.html', {
        'course': course,
        'units': units
    })


@tutor_required
def tutor_create_unit(request, course_id):
    course = get_object_or_404(Course, id=course_id, tutor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        order = request.POST.get('order', 0)
        
        Unit.objects.create(
            course=course,
            title=title,
            description=description,
            order=order
        )
        
        messages.success(request, 'Unit created successfully!')
        return redirect('tutor_course_detail', course_id=course.id)
    
    max_order = course.units.count()
    return render(request, 'courses/tutor_create_unit.html', {
        'course': course,
        'suggested_order': max_order + 1
    })


@tutor_required
def tutor_edit_unit(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__tutor=request.user)
    
    if request.method == 'POST':
        unit.title = request.POST.get('title')
        unit.description = request.POST.get('description')
        unit.order = request.POST.get('order', 0)
        unit.save()
        
        messages.success(request, 'Unit updated successfully!')
        return redirect('tutor_course_detail', course_id=unit.course.id)
    
    return render(request, 'courses/tutor_edit_unit.html', {'unit': unit})


@tutor_required
def tutor_add_video(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__tutor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        video_url = request.POST.get('video_url')
        video_file = request.FILES.get('video_file')
        thumbnail = request.FILES.get('thumbnail')
        duration = request.POST.get('duration', 0)
        order = request.POST.get('order', 0)
        is_free = request.POST.get('is_free') == 'on'
        
        Video.objects.create(
            unit=unit,
            title=title,
            video_url=video_url or '',
            video_file=video_file,
            thumbnail=thumbnail,
            duration=duration,
            order=order,
            is_free=is_free
        )
        
        messages.success(request, 'Video added successfully!')
        return redirect('tutor_course_detail', course_id=unit.course.id)
    
    max_order = unit.videos.count()
    return render(request, 'courses/tutor_add_video.html', {
        'unit': unit,
        'suggested_order': max_order + 1
    })


@tutor_required
def tutor_add_material(request, unit_id):
    unit = get_object_or_404(Unit, id=unit_id, course__tutor=request.user)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        file = request.FILES.get('file')
        material_type = request.POST.get('material_type', 'pdf')
        is_free = request.POST.get('is_free') == 'on'
        is_downloadable = request.POST.get('is_downloadable') == 'on'
        
        if file:
            Material.objects.create(
                unit=unit,
                title=title,
                file=file,
                material_type=material_type,
                is_free=is_free,
                is_downloadable=is_downloadable
            )
            
            messages.success(request, 'Material uploaded successfully!')
        else:
            messages.error(request, 'Please select a file to upload.')
        
        return redirect('tutor_course_detail', course_id=unit.course.id)
    
    return render(request, 'courses/tutor_add_material.html', {'unit': unit})


def course_catalog(request):
    courses = Course.objects.filter(is_published=True, is_approved=True).select_related('tutor', 'category')
    categories = Category.objects.all()
    
    category_filter = request.GET.get('category')
    search_query = request.GET.get('q')
    
    if category_filter:
        courses = courses.filter(category_id=category_filter)
    
    if search_query:
        courses = courses.filter(
            Q(title__icontains=search_query) | 
            Q(description__icontains=search_query)
        )
    
    paginator = Paginator(courses, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'courses/catalog.html', {
        'page_obj': page_obj,
        'categories': categories,
        'selected_category': category_filter,
        'search_query': search_query
    })


def course_detail(request, slug):
    course = get_object_or_404(Course, slug=slug, is_published=True)
    units = course.units.prefetch_related('videos', 'materials').all()
    
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            is_active=True
        ).exists()
    
    return render(request, 'courses/course_detail.html', {
        'course': course,
        'units': units,
        'is_enrolled': is_enrolled
    })


@student_required
def my_courses(request):
    enrollments = CourseEnrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')
    
    return render(request, 'courses/my_courses.html', {'enrollments': enrollments})


@login_required
def course_learn(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).first()
    
    if not enrollment and not course.is_free:
        messages.error(request, 'You need to enroll in this course first.')
        return redirect('course_detail', slug=course.slug)
    
    if not enrollment and course.is_free:
        enrollment = CourseEnrollment.objects.create(
            student=request.user,
            course=course
        )
    
    units = course.units.prefetch_related('videos', 'materials').all()
    
    return render(request, 'courses/course_learn.html', {
        'course': course,
        'units': units,
        'enrollment': enrollment
    })


@login_required
@require_http_methods(["POST"])
def track_video_progress(request, video_id):
    video = get_object_or_404(Video, id=video_id)
    data = json.loads(request.body)
    
    watch_time = data.get('watch_time', 0)
    progress = data.get('progress', 0)
    last_position = data.get('last_position', 0)
    
    watch, created = VideoWatch.objects.get_or_create(
        student=request.user,
        video=video
    )
    
    watch.watch_time = watch_time
    watch.progress = progress
    watch.last_position = last_position
    watch.is_completed = progress >= 90
    watch.save()
    
    return JsonResponse({'status': 'success'})


@tutor_required
def tutor_student_progress(request, course_id):
    course = get_object_or_404(Course, id=course_id, tutor=request.user)
    enrollments = CourseEnrollment.objects.filter(course=course).select_related('student')
    
    return render(request, 'courses/tutor_student_progress.html', {
        'course': course,
        'enrollments': enrollments
    })

@login_required
def view_material(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    unit = material.unit
    course = unit.course
    
    enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).first()
    
    if not enrollment:
        if course.is_free:
            enrollment = CourseEnrollment.objects.create(
                student=request.user,
                course=course
            )
        else:
            from elearning.payments.models import Purchase
            purchase = Purchase.objects.filter(
                student=request.user,
                course=course,
                status='completed'
            ).first()
            
            if purchase:
                enrollment, created = CourseEnrollment.objects.get_or_create(
                    student=request.user,
                    course=course,
                    defaults={'is_active': True}
                )
            else:
                messages.error(request, 'You need to enroll in this course to access this material.')
                return redirect('course_detail', slug=course.slug)
    
    material_view, created = MaterialView.objects.get_or_create(
        student=request.user,
        material=material
    )
    
    if not material_view.is_completed:
        material_view.is_completed = True
        material_view.save()
        
        if enrollment:
            total_materials = Material.objects.filter(unit__course=course).count()
            viewed_materials = MaterialView.objects.filter(
                student=request.user,
                material__unit__course=course,
                is_completed=True
            ).count()
            
            total_videos = Video.objects.filter(unit__course=course).count()
            completed_videos = VideoWatch.objects.filter(
                student=request.user,
                video__unit__course=course,
                is_completed=True
            ).count()
            
            total_items = total_materials + total_videos
            completed_items = viewed_materials + completed_videos
            
            if total_items > 0:
                enrollment.progress = (completed_items / total_items) * 100
                enrollment.save()
    
    return render(request, 'courses/view_material.html', {
        'material': material,
        'unit': unit,
        'course': course
    })
