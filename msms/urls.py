"""msms URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
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
from lessons import views
from django.contrib.auth import views as auth_views

#Required for admin DateTimeField
from django.views.i18n import JavaScriptCatalog

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name = 'home'),
    path('jsi18n', JavaScriptCatalog.as_view(), name = 'js-catalog'),
    path('student_feed/', views.student_feed, name = 'student_feed'),
    path('requests_page/', views.requests_page, name = 'requests_page'),

    path('new_lesson/', views.new_lesson, name = 'new_lesson'), #adds the single lesson to the database
    path('save_lessons/', views.save_lessons, name = 'save_lessons'),
    path('delete_pending/<int:lesson_id>', views.delete_pending, name = 'delete_pending'), #delete single pending lesson
    path('delete_saved/<int:lesson_id>', views.delete_saved, name = 'delete_saved'),
    path('edit_lesson/<int:lesson_id>', views.edit_lesson, name = 'edit_lesson'),

    path('admin_feed', views.admin_feed, name = 'admin_feed'),

    path('director_manage_roles/', views.director_manage_roles, name = 'director_manage_roles'),
    path('director_feed', views.director_feed, name = 'director_feed'),
    path('promote_director/<str:current_user_email>', views.promote_director, name = 'promote_director'),
    path('promote_admin/<str:current_user_email>', views.promote_admin, name = 'promote_admin'),

    path('disable_user/<str:current_user_email>', views.disable_user, name = 'disable_user'),
    path('delete_user/<str:current_user_email>', views.delete_user, name = 'delete_user'),
    path('update_user/<str:current_user_id>', views.update_user, name = 'update_user'),
    path('create_admin_page', views.create_admin_page, name = 'create_admin_page'),


    path('sign_up/', views.sign_up, name = 'sign_up'),
    path('sign_up_child/', views.sign_up_child, name = 'sign_up_child'),

    path('balance/', views.balance, name = 'balance'), # this is the url for student balance page that shows all the information relates to balance, invoices and transactions
    path('pay_for_invoice/', views.pay_for_invoice, name = 'pay_for_invoice'), # this is the url for function that allows student to pay for his and his children's invoices
    path('transaction_history/', views.get_all_transactions,name='transaction_history'), # this is the url for transaction_history that dispaly all students' transaction history in a table
    path('invoices_history/', views.get_all_invocies, name = 'invoices_history'), # this is the url for invoices_history that dispaly all students' invoice history in a table
    path('student_invoices_and_transactions/<str:student_id>', views.get_student_invoices_and_transactions, name = 'student_invoices_and_transactions'), # this is the url for student_invoices_and_transactions page 
                                                                                                                                                        # that display all the transactions and invoices history for on particular student

    path('log_out/', views.log_out, name = 'log_out'),

    path('student_requests/<str:student_id>', views.student_requests, name='student_requests'),
    path('admin_update_request_page/<str:lesson_id>', views.admin_update_request_page,name='admin_update_request_page'),
    path('admin_confirm_booking/<str:lesson_id>', views.admin_confirm_booking,name='admin_confirm_booking'),
    path('admin_update_request/<str:lesson_id>', views.admin_update_request, name='admin_update_request'),
    path('delete_lesson/<str:lesson_id>', views.delete_lesson, name='delete_lesson'),

    path('term_management', views.term_management_page, name='term_management'),
    path('add_term_page', views.add_term_page, name='add_term_page'),
    path('create_term', views.create_term, name='create_term'),
    path('edit_term_details_page/<str:term_number>',views.edit_term_details_page, name='edit_term_details_page'),
    path('update_term_details/<str:term_number>',views.update_term_details,name='update_term_details'),
    path('delete_term/<str:term_number>', views.delete_term, name='delete_term'),
]
