from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, UserAccount, Gender, Transaction, Lesson,LessonType,LessonDuration,LessonStatus
from django.urls import reverse
from lessons.views import pay_for_invoice,get_student_transaction,get_student_balance,get_student_invoice,get_child_invoice
from lessons.tests.helpers import reverse_with_next
from django.contrib import messages
from django.utils import timezone
from datetime import time
import datetime

class PayForInvoiceTestCase(TestCase):

    # this function test if pay for invoice function works as expected
    # related function: pay_for_invoice and used function within it

    def setUp(self):
        self.url = reverse('pay_for_invoice')

        self.student = UserAccount.objects.create_student(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.org',
            password='Password123',
            balance = 0,
            gender = Gender.MALE,
        )

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

        self.invoice = Invoice.objects.create(
            reference_number = '1-001',
            student_ID = '1',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = '1',
            invoice_status = InvoiceStatus.UNPAID,
        )

    def create_new_invoice(self):
        self.invoice1 = Invoice.objects.create(
            reference_number = '2-001',
            student_ID = '2',
            fees_amount = '78',
            amounts_need_to_pay = '38',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.PARTIALLY_PAID,
        )

    def create_new_invoice_PARTIALLY_PAID(self):
        self.invoice1 = Invoice.objects.create(
            reference_number = '1-002',
            student_ID = '1',
            fees_amount = '78',
            amounts_need_to_pay = '38',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.PARTIALLY_PAID,
        )

    def create_new_invoice_PAID(self):
        self.invoice1 = Invoice.objects.create(
            reference_number = '1-002',
            student_ID = '1',
            fees_amount = '78',
            amounts_need_to_pay = '0',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.PAID,
        )

    def create_new_invoice_DELETED(self):
        self.invoice1 = Invoice.objects.create(
            reference_number = '1-002',
            student_ID = '1',
            fees_amount = '0',
            amounts_need_to_pay = '0',
            lesson_ID = '',
            invoice_status = InvoiceStatus.DELETED,
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

    def create_invoice_for_child(self):
        self.invoice_child = Invoice.objects.create(
            reference_number = '5-001',
            student_ID = '5',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.UNPAID,
        )
    
    def test_pay_for_invoice_url(self):
        self.assertEqual(self.url, '/pay_for_invoice/')

    def test_pay_for_invoice_without_logging_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

    def test_not_student_accessing_pay_for_invoice_admin(self):
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

    def test_get_pay_for_invoice_successfully_UNPAID_TO_PAID(self):
        input = {'invocie_reference': '1-001', 'amounts_pay': '78'}

        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before+1, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 0)

        invoice = get_student_invoice(self.student)
        transaction = get_student_transaction(self.student)

        self.assertEqual(transaction[0].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[0].invoice_reference_transaction, self.invoice.reference_number)
        self.assertEqual(transaction[0].transaction_amount, 78)

        self.assertEqual(invoice[0].reference_number, self.invoice.reference_number)
        self.assertEqual(invoice[0].student_ID, self.invoice.student_ID)
        self.assertEqual(invoice[0].fees_amount, int(self.invoice.fees_amount))
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.PAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 0)
        self.assertEqual(invoice[0].lesson_ID, self.invoice.lesson_ID)

    def test_get_pay_for_invoice_successfully_UNPAID_TO_PARTIALLY_PAID(self):
        input = {'invocie_reference': '1-001', 'amounts_pay': '38'}

        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before+1, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 0)

        invoice = get_student_invoice(self.student)
        transaction = get_student_transaction(self.student)

        self.assertEqual(transaction[0].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[0].invoice_reference_transaction, self.invoice.reference_number)
        self.assertEqual(transaction[0].transaction_amount, 38)

        self.assertEqual(invoice[0].reference_number, self.invoice.reference_number)
        self.assertEqual(invoice[0].student_ID, self.invoice.student_ID)
        self.assertEqual(invoice[0].fees_amount, int(self.invoice.fees_amount))
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.PARTIALLY_PAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 40)
        self.assertEqual(invoice[0].lesson_ID, self.invoice.lesson_ID)

    def test_get_pay_for_invoice_successfully_PARTIALLY_PAID_TO_PAID(self):
        self.create_new_invoice_PARTIALLY_PAID()
        input = {'invocie_reference': '1-002', 'amounts_pay': '38'}

        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before+1, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 0)

        invoice = get_student_invoice(self.student)
        transaction = get_student_transaction(self.student)

        self.assertEqual(transaction[0].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[0].invoice_reference_transaction, self.invoice1.reference_number)
        self.assertEqual(transaction[0].transaction_amount, 38)

        self.assertEqual(invoice[1].reference_number, self.invoice1.reference_number)
        self.assertEqual(invoice[1].student_ID, self.invoice1.student_ID)
        self.assertEqual(invoice[1].fees_amount, int(self.invoice1.fees_amount))
        self.assertEqual(invoice[1].invoice_status, InvoiceStatus.PAID)
        self.assertEqual(invoice[1].amounts_need_to_pay, 0)
        self.assertEqual(invoice[1].lesson_ID, self.invoice1.lesson_ID)


    def test_get_pay_for_child_invoice(self):
        self.create_child_student()
        self.create_invoice_for_child()
        input = {'invocie_reference': '5-001', 'amounts_pay': '78'}

        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before+1, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 0)

        invoice = get_child_invoice(self.student)
        transaction = get_student_transaction(self.student)

        self.assertEqual(transaction[0].Student_ID_transaction, str(self.student.id))
        self.assertEqual(transaction[0].invoice_reference_transaction, self.invoice_child.reference_number)
        self.assertEqual(transaction[0].transaction_amount, 78)

        self.assertEqual(invoice[0].reference_number, self.invoice_child.reference_number)
        self.assertEqual(invoice[0].student_ID, self.invoice_child.student_ID)
        self.assertEqual(invoice[0].fees_amount, int(self.invoice_child.fees_amount))
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.PAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 0)
        self.assertEqual(invoice[0].lesson_ID, self.invoice_child.lesson_ID)


    def test_submit_without_enter_value(self):
        input = {'invocie_reference': '', 'amounts_pay': ''}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "You cannot submit without enter a value!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_get_not_exist_invoice(self):
        input = {'invocie_reference': '1-002', 'amounts_pay': '38'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "There isn't such invoice exist!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_enter_wrong_invoice_referece_number(self):
        self.create_new_invoice()
        input = {'invocie_reference': '2-001', 'amounts_pay': '38'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "this invoice does not belong to you or your children!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_try_to_pay_for_PAID_invoice(self):
        self.create_new_invoice_PAID()
        input = {'invocie_reference': '1-002', 'amounts_pay': '38'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "This invoice has already been paid!")
        self.assertEqual(messages_list[0].level, messages.ERROR)
        
    def test_try_to_pay_for_DELETED_invoice(self):
        self.create_new_invoice_DELETED()
        input = {'invocie_reference': '1-002', 'amounts_pay': '38'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "This invoice has already been deleted!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_try_to_pay_with_a_amount_less_than_0(self):
        input = {'invocie_reference': '1-001', 'amounts_pay': '-12'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Transaction amount cannot be less than 1!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_try_to_pay_with_a_amount_larger_than_10000(self):
        input = {'invocie_reference': '1-001', 'amounts_pay': '100000'}
        invoice_count_before = Invoice.objects.count()
        transaction_count_before = Transaction.objects.count()

        self.client.login(username=self.student.email, password='Password123')
        response = self.client.post(self.url, input, follow=True)
        redirect_url = reverse('balance')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'balance.html')

        invoice_count_after = Invoice.objects.count()
        transaction_count_after = Transaction.objects.count()
        self.assertEqual(transaction_count_before, transaction_count_after)
        self.assertEqual(invoice_count_before, invoice_count_after)

        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list), 1)
        self.assertEqual(str(messages_list[0]), "Transaction amount cannot be larger than 10000!")
        self.assertEqual(messages_list[0].level, messages.ERROR)

