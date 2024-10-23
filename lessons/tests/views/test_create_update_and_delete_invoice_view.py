from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, UserAccount, Gender, Transaction, Lesson,LessonType,LessonDuration,LessonStatus
from django.urls import reverse
from lessons.views import get_student_balance,get_student_invoice,create_new_invoice,update_invoice,update_invoice_when_delete
from lessons.tests.helpers import reverse_with_next
from django.contrib import messages
from django.utils import timezone
from datetime import time
import datetime

class CreateUpdateDeleteInvoiceTestCase(TestCase):

    # this function test if invoice can be successfully create, update and delete
    # tested function: create_new_invoice, update_invoice, update_invoice_when_delete

    def setUp(self):

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

    def create_new_lesson_THIRTY(self):
        self.saved_lesson = Lesson.objects.create(
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.THIRTY,
            lesson_date_time = datetime.datetime(2022, 11, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED
        )

    def create_new_lesson_FOURTY_FIVE(self):
        self.saved_lesson = Lesson.objects.create(
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2022, 11, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED
        )

    def create_new_lesson_HOUR(self):
        self.saved_lesson = Lesson.objects.create(
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.HOUR,
            lesson_date_time = datetime.datetime(2022, 11, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED
        )
    
    def create_new_invoice_THIRTY(self):
        self.invoice = Invoice.objects.create(
            reference_number = '1-001',
            student_ID = '1',
            fees_amount = '15',
            amounts_need_to_pay = '15',
            lesson_ID = '1',
            invoice_status = InvoiceStatus.UNPAID,
        )

    def create_new_invoice_HOUR(self):
        self.invoice = Invoice.objects.create(
            reference_number = '1-001',
            student_ID = '1',
            fees_amount = '20',
            amounts_need_to_pay = '20',
            lesson_ID = '1',
            invoice_status = InvoiceStatus.UNPAID,
        )



    def test_create_new_invoice_THIRTY(self):
        self.create_new_lesson_THIRTY()
        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()
        create_new_invoice(self.student.id, self.saved_lesson)
        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before + 1, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 15)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 15)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        balance = get_student_balance(self.student)

        self.assertEqual(balance[0], 0 - invoice[0].amounts_need_to_pay)

    def test_create_new_invoice_FOURTY_FIVE(self):
        self.create_new_lesson_FOURTY_FIVE()
        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()
        create_new_invoice(self.student.id, self.saved_lesson)
        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before + 1, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 18)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 18)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        balance = get_student_balance(self.student)

        self.assertEqual(balance[0], 0 - invoice[0].amounts_need_to_pay)

    def test_create_new_invoice_HOUR(self):
        self.create_new_lesson_HOUR()
        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()
        create_new_invoice(self.student.id, self.saved_lesson)
        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before + 1, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 20)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 20)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        balance = get_student_balance(self.student)

        self.assertEqual(balance[0], 0 - invoice[0].amounts_need_to_pay)

    def test_update_invoice_THIRY_TO_HOUR(self):
        self.create_new_lesson_THIRTY()
        self.create_new_invoice_THIRTY()

        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()

        self.assertEqual(self.invoice.reference_number, '1-001')
        self.assertEqual(self.invoice.student_ID, str(self.student.id))
        self.assertEqual(int(self.invoice.fees_amount), 15)
        self.assertEqual(self.invoice.invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(int(self.invoice.amounts_need_to_pay), 15)
        self.assertEqual(self.invoice.lesson_ID, str(self.saved_lesson.lesson_id))

        self.assertEqual(self.saved_lesson.duration, LessonDuration.THIRTY)

        self.saved_lesson.duration = LessonDuration.HOUR
        self.saved_lesson.save()

        update_invoice(self.saved_lesson)

        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 20)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 20)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))
        
        self.assertEqual(self.saved_lesson.duration, LessonDuration.HOUR)

    def test_update_invoice_HOUR_TO_FOURTY_FIVE(self):
        self.create_new_lesson_HOUR()
        self.create_new_invoice_HOUR()

        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()

        self.assertEqual(self.invoice.reference_number, '1-001')
        self.assertEqual(self.invoice.student_ID, str(self.student.id))
        self.assertEqual(int(self.invoice.fees_amount), 20)
        self.assertEqual(self.invoice.invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(int(self.invoice.amounts_need_to_pay), 20)
        self.assertEqual(self.invoice.lesson_ID, str(self.saved_lesson.lesson_id))

        self.assertEqual(self.saved_lesson.duration, LessonDuration.HOUR)

        self.saved_lesson.duration = LessonDuration.FOURTY_FIVE
        self.saved_lesson.save()

        update_invoice(self.saved_lesson)

        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 18)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 18)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        self.assertEqual(self.saved_lesson.duration, LessonDuration.FOURTY_FIVE)

    def test_update_invoice_when_invoice_not_exist(self):
        self.create_new_lesson_HOUR()

        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()

        update_invoice(self.saved_lesson)

        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before + 1, invoice_count_before_after)
        self.assertEqual(lesson_count_before, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 20)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.UNPAID)
        self.assertEqual(invoice[0].amounts_need_to_pay, 20)
        self.assertEqual(invoice[0].lesson_ID, str(self.saved_lesson.lesson_id))

        self.assertEqual(self.saved_lesson.duration, LessonDuration.HOUR)


    def test_update_invoice_when_delete(self):
        self.create_new_lesson_HOUR()
        self.create_new_invoice_HOUR()

        lesson_count_before = Lesson.objects.count()
        invoice_count_before = Invoice.objects.count()

        update_invoice_when_delete(self.saved_lesson)
        self.saved_lesson.delete()

        lesson_count_after = Lesson.objects.count()
        invoice_count_before_after = Invoice.objects.count()

        self.assertEqual(invoice_count_before , invoice_count_before_after)
        self.assertEqual(lesson_count_before - 1, lesson_count_after)

        invoice = get_student_invoice(self.student)

        self.assertEqual(invoice[0].reference_number, '1-001')
        self.assertEqual(invoice[0].student_ID, str(self.student.id))
        self.assertEqual(invoice[0].fees_amount, 0)
        self.assertEqual(invoice[0].invoice_status, InvoiceStatus.DELETED)
        self.assertEqual(invoice[0].amounts_need_to_pay, 0)
        self.assertEqual(invoice[0].lesson_ID, '')

