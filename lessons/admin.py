"""Configuration of the admin interface for MSMS"""
from django.contrib import admin
from .models import UserAccount,Lesson, Invoice, Transaction,Term
# Register your models here.
@admin.register(UserAccount)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'id','email', 'first_name', 'last_name','role', 'gender' , 'balance', 'is_active', 'is_staff', 'is_superuser', 'is_parent', 'parent_of_user'
    ]
    # ordering = ('email',)

@admin.register(Lesson)
class UserAdmin(admin.ModelAdmin):
    list_display = [
        'lesson_id', 'request_date' ,'type', 'duration' , 'lesson_date_time', 'teacher_id', 'student_id', 'lesson_status'
    ]

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['reference_number','student_ID', 'lesson_ID', 'fees_amount', 'invoice_status', 'amounts_need_to_pay'
    ]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['Student_ID_transaction', 'invoice_reference_transaction', 'transaction_amount'
    ]

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['term_number', 'start_date', 'end_date'
    ]



    # ordering = ('request_date',)
    # search_fields = ('lesson_id','duration')
    # list_filter = ('lesson_date_time','duration','is_booked','student_id')
