"""
URL configuration for elearning project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from elearning.accounts import views as account_views
from elearning.courses import views as course_views
from elearning.payments import views as payment_views
from elearning.quizzes import views as quiz_views

urlpatterns = [
    path('', account_views.home_view, name='home'),
    
    path('accounts/login/', account_views.login_view, name='login'),
    path('accounts/register/', account_views.register_view, name='register'),
    path('accounts/logout/', account_views.logout_view, name='logout'),
    
    path('admin-dashboard/', account_views.admin_dashboard, name='admin_dashboard'),
    path('manage/users/', account_views.admin_manage_users, name='admin_manage_users'),
    path('manage/users/create-tutor/', account_views.admin_create_tutor, name='admin_create_tutor'),
    path('manage/users/<int:user_id>/edit/', account_views.admin_edit_user, name='admin_edit_user'),
    path('manage/users/<int:user_id>/delete/', account_views.admin_delete_user, name='admin_delete_user'),
    
    path('manage/courses/', course_views.admin_manage_courses, name='admin_manage_courses'),
    path('manage/courses/create/', course_views.admin_create_course, name='admin_create_course'),
    path('manage/courses/<int:course_id>/edit/', course_views.admin_edit_course, name='admin_edit_course'),
    path('manage/courses/<int:course_id>/delete/', course_views.admin_delete_course, name='admin_delete_course'),
    
    path('admin/', admin.site.urls),
    
    path('tutor-dashboard/', account_views.tutor_dashboard, name='tutor_dashboard'),
    path('tutor/courses/', course_views.tutor_my_courses, name='tutor_my_courses'),
    path('tutor/courses/<int:course_id>/', course_views.tutor_course_detail, name='tutor_course_detail'),
    path('tutor/courses/<int:course_id>/units/create/', course_views.tutor_create_unit, name='tutor_create_unit'),
    path('tutor/units/<int:unit_id>/edit/', course_views.tutor_edit_unit, name='tutor_edit_unit'),
    path('tutor/units/<int:unit_id>/videos/add/', course_views.tutor_add_video, name='tutor_add_video'),
    path('tutor/units/<int:unit_id>/materials/add/', course_views.tutor_add_material, name='tutor_add_material'),
    path('tutor/courses/<int:course_id>/progress/', course_views.tutor_student_progress, name='tutor_student_progress'),
    
    path('tutor/quizzes/create/<int:video_id>/', quiz_views.tutor_create_quiz, name='tutor_create_quiz'),
    path('tutor/quizzes/<int:quiz_id>/edit/', quiz_views.tutor_edit_quiz, name='tutor_edit_quiz'),
    path('tutor/quizzes/<int:quiz_id>/questions/add/', quiz_views.tutor_add_question, name='tutor_add_question'),
    path('tutor/questions/<int:question_id>/delete/', quiz_views.tutor_delete_question, name='tutor_delete_question'),
    path('tutor/quizzes/<int:quiz_id>/analytics/', quiz_views.tutor_quiz_analytics, name='tutor_quiz_analytics'),
    
    path('student-dashboard/', account_views.student_dashboard, name='student_dashboard'),
    path('courses/', course_views.course_catalog, name='course_catalog'),
    path('courses/<slug:slug>/', course_views.course_detail, name='course_detail'),
    path('my-courses/', course_views.my_courses, name='my_courses'),
    path('courses/<int:course_id>/learn/', course_views.course_learn, name='course_learn'),
    path('videos/<int:video_id>/progress/', course_views.track_video_progress, name='track_video_progress'),
    path('materials/<int:material_id>/view/', course_views.view_material, name='view_material'),
    
    path('courses/<int:course_id>/checkout/', payment_views.checkout, name='checkout'),
    path('courses/<int:course_id>/create-payment-intent/', payment_views.create_payment_intent, name='create_payment_intent'),
    path('payments/webhook/', payment_views.stripe_webhook, name='stripe_webhook'),
    path('courses/<int:course_id>/payment/success/', payment_views.payment_success, name='payment_success'),
    path('my-payments/', payment_views.payment_history, name='payment_history'),
    
    path('quizzes/<int:quiz_id>/take/', quiz_views.take_quiz, name='take_quiz'),
    path('quizzes/<int:quiz_id>/submit/', quiz_views.submit_quiz, name='submit_quiz'),
    path('quizzes/attempts/<int:attempt_id>/results/', quiz_views.quiz_results, name='quiz_results'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
