from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from .models import User

@require_http_methods(["GET", "POST"])
def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if user.is_suspended:
                messages.error(request, 'Your account has been suspended.')
                return render(request, 'accounts/login.html')
            
            login(request, user)
            
            if user.is_admin():
                return redirect('admin_dashboard')
            elif user.is_tutor():
                return redirect('tutor_dashboard')
            else:
                return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')

@require_http_methods(["GET", "POST"])
def register_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        role = request.POST.get('role', 'student')
        
        if role not in ['student', 'tutor']:
            messages.error(request, 'Invalid role selected.')
            return render(request, 'accounts/register.html')
        
        if password != password_confirm:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role=role
        )
        
        messages.success(request, 'Account created successfully! Please login.')
        return redirect('login')
    
    return render(request, 'accounts/register.html')

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')

def home_view(request):
    return render(request, 'home.html')

from .decorators import admin_required, tutor_required, student_required

@admin_required
def admin_dashboard(request):
    from elearning.courses.models import Course, CourseEnrollment
    from elearning.payments.models import Purchase
    from django.db.models import Sum
    
    total_users = User.objects.count()
    total_tutors = User.objects.filter(role='tutor').count()
    total_students = User.objects.filter(role='student').count()
    total_courses = Course.objects.count()
    total_enrollments = CourseEnrollment.objects.count()
    
    total_revenue = Purchase.objects.filter(status='completed').aggregate(
        total=Sum('amount')
    )['total'] or 0
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_courses = Course.objects.order_by('-created_at')[:5]
    recent_purchases = Purchase.objects.filter(status='completed').select_related(
        'student', 'course'
    ).order_by('-completed_at')[:10]
    
    return render(request, 'dashboards/admin.html', {
        'total_users': total_users,
        'total_tutors': total_tutors,
        'total_students': total_students,
        'total_courses': total_courses,
        'total_enrollments': total_enrollments,
        'total_revenue': total_revenue,
        'recent_users': recent_users,
        'recent_courses': recent_courses,
        'recent_purchases': recent_purchases
    })

@tutor_required
def tutor_dashboard(request):
    from elearning.courses.models import Course, CourseEnrollment
    from elearning.quizzes.models import QuizAttempt
    
    my_courses = Course.objects.filter(tutor=request.user)
    total_students = CourseEnrollment.objects.filter(
        course__in=my_courses
    ).count()
    
    recent_enrollments = CourseEnrollment.objects.filter(
        course__in=my_courses
    ).select_related('student', 'course').order_by('-enrolled_at')[:10]
    
    recent_quiz_attempts = QuizAttempt.objects.filter(
        quiz__video__unit__course__in=my_courses
    ).select_related('student', 'quiz').order_by('-completed_at')[:10]
    
    return render(request, 'dashboards/tutor.html', {
        'my_courses': my_courses,
        'total_courses': my_courses.count(),
        'total_students': total_students,
        'recent_enrollments': recent_enrollments,
        'recent_quiz_attempts': recent_quiz_attempts
    })

@student_required
def student_dashboard(request):
    from elearning.courses.models import CourseEnrollment, Course
    
    enrollments = CourseEnrollment.objects.filter(
        student=request.user,
        is_active=True
    ).select_related('course')[:5]
    
    available_courses = Course.objects.filter(
        is_published=True,
        is_approved=True
    ).exclude(
        id__in=enrollments.values_list('course_id', flat=True)
    )[:6]
    
    return render(request, 'dashboards/student.html', {
        'enrollments': enrollments,
        'available_courses': available_courses
    })


@admin_required
def admin_manage_users(request):
    users = User.objects.all().order_by('-date_joined')
    tutors = users.filter(role='tutor')
    students = users.filter(role='student')
    admins = users.filter(role='admin')
    
    return render(request, 'accounts/admin_manage_users.html', {
        'users': users,
        'tutors': tutors,
        'students': students,
        'admins': admins
    })


@admin_required
def admin_create_tutor(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/admin_create_tutor.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/admin_create_tutor.html')
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            role='tutor',
            first_name=first_name,
            last_name=last_name
        )
        
        messages.success(request, f'Tutor "{user.username}" created successfully!')
        return redirect('admin_manage_users')
    
    return render(request, 'accounts/admin_create_tutor.html')


@admin_required
def admin_edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        user.is_suspended = request.POST.get('is_suspended') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        user.save()
        
        messages.success(request, f'User "{user.username}" updated successfully!')
        return redirect('admin_manage_users')
    
    return render(request, 'accounts/admin_edit_user.html', {'user_obj': user})


@admin_required
def admin_delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    
    if user.id == request.user.id:
        messages.error(request, 'You cannot delete your own account.')
        return redirect('admin_manage_users')
    
    username = user.username
    user.delete()
    messages.success(request, f'User "{username}" deleted successfully!')
    return redirect('admin_manage_users')


