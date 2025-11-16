from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from .models import Purchase, Transaction
from elearning.courses.models import Course, CourseEnrollment
import stripe
import json

stripe.api_key = settings.STRIPE_SECRET_KEY


@login_required
def checkout(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_published=True)
    
    if course.is_free:
        CourseEnrollment.objects.get_or_create(
            student=request.user,
            course=course
        )
        messages.success(request, f'You have been enrolled in "{course.title}"!')
        return redirect('course_learn', course_id=course.id)
    
    existing_enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).first()
    
    if existing_enrollment:
        messages.info(request, 'You are already enrolled in this course.')
        return redirect('course_learn', course_id=course.id)
    
    return render(request, 'payments/checkout.html', {
        'course': course,
        'stripe_public_key': settings.STRIPE_PUBLIC_KEY
    })


@login_required
@require_http_methods(["POST"])
def create_payment_intent(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    
    existing_enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=course,
        is_active=True
    ).first()
    
    if existing_enrollment:
        return JsonResponse({'error': 'Already enrolled'}, status=400)
    
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(course.price * 100),
            currency='rwf',
            metadata={
                'course_id': course.id,
                'student_id': request.user.id
            }
        )
        
        Purchase.objects.create(
            student=request.user,
            course=course,
            amount=course.price,
            stripe_payment_intent_id=intent.id,
            status='pending'
        )
        
        return JsonResponse({'clientSecret': intent.client_secret})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError:
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse(status=400)
    
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        
        purchase = Purchase.objects.filter(
            stripe_payment_intent_id=payment_intent.id
        ).first()
        
        if purchase:
            purchase.status = 'completed'
            purchase.save()
            
            CourseEnrollment.objects.get_or_create(
                student=purchase.student,
                course=purchase.course,
                is_active=True
            )
            
            Transaction.objects.create(
                purchase=purchase,
                transaction_type='purchase',
                amount=purchase.amount,
                stripe_charge_id=payment_intent.get('latest_charge'),
                description=f'Purchase of {purchase.course.title}'
            )
    
    return HttpResponse(status=200)


@login_required
def payment_success(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    return render(request, 'payments/success.html', {'course': course})


@login_required
def payment_history(request):
    purchases = Purchase.objects.filter(student=request.user).select_related('course')
    return render(request, 'payments/history.html', {'purchases': purchases})
