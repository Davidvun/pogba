from django.contrib import admin
from .models import Purchase, Transaction, PaymentMethod

@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'amount', 'status', 'created_at', 'completed_at']
    list_filter = ['status', 'created_at']
    search_fields = ['student__username', 'course__title', 'transaction_id']
    readonly_fields = ['transaction_id']

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'transaction_type', 'amount', 'payment_method', 'created_at']
    list_filter = ['transaction_type', 'created_at']
    search_fields = ['purchase__student__username', 'stripe_charge_id']

@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ['user', 'card_brand', 'card_last4', 'is_default', 'created_at']
    list_filter = ['card_brand', 'is_default']
    search_fields = ['user__username', 'card_last4']
