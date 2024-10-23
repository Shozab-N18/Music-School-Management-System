
from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, UserAccount, Gender, Transaction, Lesson,LessonType,LessonDuration,LessonStatus
from django.urls import reverse
from lessons.views import get_student_balance,get_student_transaction,get_student_invoice,get_child_invoice
from lessons.tests.helpers import reverse_with_next
from django.utils import timezone
from datetime import time
import datetime

class BalanceViewAndGetFunctionsTestCase(TestCase):
    '''Tests of the invoice view'''
    fixtures = ['lessons/tests/fixtures/invoices.json']

    # this function test if balance view works as expected
    # tested function: balance and function used within it, get_student_invoice, get_student_transaction, get_student_balance, get_child_invoice

    def setUp(self):
        self.url = reverse('balance')

        self.student = UserAccount.objects.create_student(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.org',
            password='Password123',
            balance = 0,
            gender = Gender.MALE,
        )

        # self.student = UserAccount.objects.get(email='johndoe@example.org')
        # self.teacher=UserAccount.objects.get(email='bobby@example.org')
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


        self.invoice = Invoice.objects.get(reference_number = '1-001')

        self.transaction = Transaction.objects.create(
            Student_ID_transaction = '1',
            invoice_reference_transaction = '1-001',
            transaction_amount = '30'
        )

        self.saved_lesson = Lesson.objects.create(
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.THIRTY,
            lesson_date_time = datetime.datetime(2022, 11, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED
        )

    def create_new_transaction(self):
        self.transaction2 = Transaction.objects.create(
            Student_ID_transaction = '1',
            invoice_reference_transaction = '1-001',
            transaction_amount = '28'
        )

    def create_new_invoice(self):
        self.invoice2 = Invoice.objects.create(
            reference_number = '1-002',
            student_ID = '1',
            fees_amount = '67',
            amounts_need_to_pay = '23',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.PARTIALLY_PAID,
        )

    def create_new_saved_lesson(self):
        self.saved_lesson2 = Lesson.objects.create(
            type = LessonType.THEORY,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2022, 10, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED
        )

    def create_child_student(self):
        self.child = UserAccount.objects.create_child_student(
            first_name = 'Ace',
            last_name = 'Lee',
            email = 'Acelee@example.org',
            password = 'Password123',
            gender = Gender.MALE,
            parent_of_user = self.student,
        )

    def create_second_child_student(self):
        self.child2 = UserAccount.objects.create_child_student(
            first_name = 'Bce',
            last_name = 'Bee',
            email = 'BoeBee@example.org',
            password = 'Password123',
            gender = Gender.FEMALE,
            parent_of_user = self.student,
        )

    def create_invoice_for_child(self):
        self.invoice_child = Invoice.objects.create(
            reference_number = '5-001',
            student_ID = '5',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.UNPAID,
        )

    def create_invoice_for_child2(self):
        self.invoice_child2 = Invoice.objects.create(
            reference_number = '6-001',
            student_ID = '6',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = '3',
            invoice_status = InvoiceStatus.UNPAID,
        )


    def test_balance_url(self):
        self.assertEqual(self.url, '/balance/')

    def test_get_balance(self):
        self.client.login(username=self.student.email, password='Password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'balance.html')

    def test_access_balance_without_being_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

    def test_not_student_accessing_balance_page_admin(self):
        self.client.login(username = self.admin.email, password = 'Password123')
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')

    def test_not_student_accessing_balance_page_director(self):
        self.client.login(username = self.director.email, password = 'Password123')
        response = self.client.get(self.url, follow=True)
        redirect_url = reverse('director_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_feed.html')


    def test_function_to_get_student_balance(self):
        balance = get_student_balance(self.student)
        self.assertEqual(len(balance), 1)
        self.assertEqual(balance[0], 0)

    def test_function_to_get_student_transactions(self):
        transaction = get_student_transaction(self.student)
        self.assertEqual(len(transaction), 1)

        self.assertEqual(transaction[0].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[0].invoice_reference_transaction, self.invoice.reference_number)
        self.assertEqual(transaction[0].transaction_amount, 30)

        self.create_new_transaction()
        transaction = get_student_transaction(self.student)
        self.assertEqual(len(transaction), 2)

        self.assertEqual(transaction[1].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[1].invoice_reference_transaction, self.invoice.reference_number)
        self.assertEqual(transaction[1].transaction_amount, 28)

    def test_function_to_get_student_invoice(self):
        invoice = get_student_invoice(self.student)
        self.assertEqual(len(invoice), 1)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 78)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        # self.assertEqual(invoice[0].amounts_need_to_pay, '78')
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        self.create_new_invoice()
        self.create_new_saved_lesson()
        invoice = get_student_invoice(self.student)
        self.assertEqual(len(invoice), 2)

        self.assertEqual(invoice[1].reference_number, '1-002')
        self.assertEqual(invoice[1].student_ID, str(self.student.id))
        self.assertEqual(invoice[1].fees_amount, 67)
        self.assertEqual(invoice[1].invoice_status, InvoiceStatus.PARTIALLY_PAID)
        self.assertEqual(invoice[1].amounts_need_to_pay, 23)
        self.assertEqual(invoice[1].lesson_ID, str(self.saved_lesson2.lesson_id))

    def test_function_to_get_child_invoice_1_child(self):
        self.create_child_student()
        child_invoices = get_child_invoice(self.student)
        self.assertEqual(len(child_invoices), 0)

        self.create_invoice_for_child()
        child_invoices = get_child_invoice(self.student)
        self.assertEqual(len(child_invoices), 1)

        self.assertEqual(child_invoices[0].reference_number, '5-001')
        self.assertEqual(child_invoices[0].student_ID, str(self.child.id))
        self.assertEqual(child_invoices[0].fees_amount, 78)
        self.assertEqual(child_invoices[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(child_invoices[0].amounts_need_to_pay, 78)
        self.assertEqual(child_invoices[0].lesson_ID, '2')

    def test_function_to_get_child_invoice_2_children(self):
        self.create_child_student()
        self.create_invoice_for_child()
        child_invoices = get_child_invoice(self.student)
        self.assertEqual(len(child_invoices), 1)

        self.create_second_child_student()
        self.create_invoice_for_child2()
        child_invoices = get_child_invoice(self.student)
        self.assertEqual(len(child_invoices), 2)

        self.assertEqual(child_invoices[1].reference_number, '6-001')
        self.assertEqual(child_invoices[1].student_ID, str(self.child2.id))
        self.assertEqual(child_invoices[1].fees_amount, 78)
        self.assertEqual(child_invoices[1].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(child_invoices[1].amounts_need_to_pay, 78)
        self.assertEqual(child_invoices[1].lesson_ID, '3')
