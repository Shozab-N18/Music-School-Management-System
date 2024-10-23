from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, UserAccount, Gender, Transaction, Lesson,LessonType,LessonDuration,LessonStatus
from django.urls import reverse
from lessons.views import get_student_balance,get_student_invoice,create_new_invoice,update_invoice,update_invoice_when_delete
from lessons.tests.helpers import reverse_with_next
from django.contrib import messages
from django.utils import timezone
from datetime import time
import datetime

class GetAllTransactionHistoryTestCase(TestCase):

    # this test test if function that display one particular student's invoices and transactions work as expect
    # related view function: get_student_invoices_and_transactions

    def setUp(self):

        self.student = UserAccount.objects.create_student(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.org',
            password='Password123',
            balance = 0,
            gender = Gender.MALE,
        )

        self.url = reverse('student_invoices_and_transactions', kwargs={'student_id':self.student.id})

        self.teacher = UserAccount.objects.create_teacher(
            first_name='Bob',
            last_name='Jacobs',
            email='bobby@example.org',
            password='Password123',
            gender = Gender.MALE,
        )

        self.admin = UserAccount.objects.create_admin(
            first_name='Jane',
            last_name='Doe',
            email='janedoe@example.org',
            password='Password123',
            gender = 'F',
        )

        self.director = UserAccount.objects.create_superuser(
            first_name='Barbare',
            last_name='Dutch',
            email='barbdutch@example.org',
            password='Password123',
            gender = Gender.FEMALE,
        )

    def test_edit_lesson_url(self):
        self.assertEqual(self.url, f'/student_invoices_and_transactions/{self.student.id}')

    def test_access_invoices_and_transactions_history_when_log_in_as_admin(self):
        self.client.login(username=self.admin.email, password='Password123')
        response = self.client.get(self.url)                         
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_invoices_and_transactions.html')

    def test_access_invoices_and_transactions_history_when_log_in_as_director(self):
        self.client.login(username=self.director.email, password='Password123')
        response = self.client.get(self.url)                         
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_invoices_and_transactions.html')

    def test_access_invoices_and_transactions_history_without_being_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

    def test_access_invoices_and_transactions_history_when_log_in_as_student(self):
        self.client.login(username=self.student.email, password='Password123')
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')