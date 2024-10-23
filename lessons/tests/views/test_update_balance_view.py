from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, UserAccount, Gender, Transaction
from django.urls import reverse
from lessons.views import update_balance

class UpdateBalanceTestCase(TestCase):

    # this function test if functions that related to update balance works as expceted
    # tested view function: update_invoice and function within it

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

    def create_new_invoice(self):
        self.invoice = Invoice.objects.create(
            reference_number = '1-001',
            student_ID = '1',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = '1',
            invoice_status = InvoiceStatus.UNPAID,
        )

    def create_new_invoice2(self):
        self.invoice2 = Invoice.objects.create(
            reference_number = '1-002',
            student_ID = '1',
            fees_amount = '30',
            amounts_need_to_pay = '10',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.PARTIALLY_PAID,
        )

    def create_new_transactions(self):
        self.transaction = Transaction.objects.create(
            Student_ID_transaction = '1',
            invoice_reference_transaction = '1-002',
            transaction_amount = '20'
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
            reference_number = '2-001',
            student_ID = '2',
            fees_amount = '66',
            amounts_need_to_pay = '66',
            lesson_ID = '2',
            invoice_status = InvoiceStatus.UNPAID,
        )

    def create_transaction_for_child(self):
        self.transaction2 = Transaction.objects.create(
            Student_ID_transaction = '1',
            invoice_reference_transaction = '2-001',
            transaction_amount = '28'
        )


    def test_update_balance_without_any_invoices_and_transactions(self):
        before_count_invoice = Invoice.objects.count()
        before_count_transaction = Transaction.objects.count()

        update_balance(self.student)

        after_count_invoice = Invoice.objects.count()
        after_count_transaction = Transaction.objects.count()

        self.assertEqual(self.student.balance, 0)
        self.assertEqual(before_count_invoice, after_count_invoice)
        self.assertEqual(before_count_transaction, after_count_transaction)

    def test_update_balance_with_1_invoice(self):
        before_count_invoice = Invoice.objects.count()
        before_count_transaction = Transaction.objects.count()

        self.create_new_invoice()

        update_balance(self.student)

        after_count_invoice = Invoice.objects.count()
        after_count_transaction = Transaction.objects.count()

        self.assertEqual(self.student.balance, -78)
        self.assertEqual(before_count_invoice + 1, after_count_invoice)
        self.assertEqual(before_count_transaction, after_count_transaction)

    def test_update_balance_with_2_invoice_and_1_transactions(self):
        before_count_invoice = Invoice.objects.count()
        before_count_transaction = Transaction.objects.count()

        self.create_new_invoice()
        self.create_new_invoice2()
        self.create_new_transactions()

        update_balance(self.student)

        after_count_invoice = Invoice.objects.count()
        after_count_transaction = Transaction.objects.count()

        self.assertEqual(self.student.balance, -88)
        self.assertEqual(before_count_invoice + 2, after_count_invoice)
        self.assertEqual(before_count_transaction + 1, after_count_transaction)

    def test_update_balance_with_self_invoices_and_children_invoices(self):
        before_count_invoice = Invoice.objects.count()
        before_count_transaction = Transaction.objects.count()
        before_count_user = UserAccount.objects.count()

        self.create_new_invoice()
        self.create_new_invoice2()
        self.create_new_transactions()
        self.create_child_student()
        self.create_invoice_for_child()

        update_balance(self.student)
    
        after_count_invoice = Invoice.objects.count()
        after_count_transaction = Transaction.objects.count()
        after_count_user = UserAccount.objects.count()

        self.assertEqual(self.student.balance, -154)
        self.assertEqual(before_count_invoice + 3, after_count_invoice)
        self.assertEqual(before_count_transaction + 1, after_count_transaction)
        self.assertEqual(before_count_user + 1, after_count_user)

    def test_update_balance_with_self_and_children_invoices_and_transactions(self):
        before_count_invoice = Invoice.objects.count()
        before_count_transaction = Transaction.objects.count()
        before_count_user = UserAccount.objects.count()

        self.create_new_invoice()
        self.create_new_invoice2()
        self.create_new_transactions()
        self.create_child_student()
        self.create_invoice_for_child()
        self.create_transaction_for_child()

        update_balance(self.student)
    
        after_count_invoice = Invoice.objects.count()
        after_count_transaction = Transaction.objects.count()
        after_count_user = UserAccount.objects.count()

        self.assertEqual(self.student.balance, -126)
        self.assertEqual(before_count_invoice + 3, after_count_invoice)
        self.assertEqual(before_count_transaction + 2, after_count_transaction)
        self.assertEqual(before_count_user + 1, after_count_user)