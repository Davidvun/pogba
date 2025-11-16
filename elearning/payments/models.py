from django.db import models
from django.conf import settings
from elearning.courses.models import Course
import uuid

class Purchase(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='purchases')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='purchases')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    transaction_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.course.title} - {self.status}"
    
    class Meta:
        ordering = ['-created_at']


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ('purchase', 'Course Purchase'),
        ('refund', 'Refund'),
    ]
    
    purchase = models.ForeignKey(Purchase, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='purchase')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_charge_id = models.CharField(max_length=255, blank=True, null=True)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.transaction_type} - {self.amount} - {self.created_at}"
    
    class Meta:
        ordering = ['-created_at']


class PaymentMethod(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='payment_methods')
    stripe_payment_method_id = models.CharField(max_length=255)
    card_last4 = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.card_brand} **** {self.card_last4}"
    
    class Meta:
        ordering = ['-created_at']
