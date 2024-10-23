from django.test import TestCase
from django.urls import reverse
from lessons.models import Lesson,LessonType,LessonDuration,UserAccount,Gender,LessonStatus,Invoice,InvoiceStatus
from lessons.models import UserAccount,UserRole
from django.contrib import messages

import datetime
from datetime import date
from django.utils import timezone
from django.test import Client

class DirectorRoleChangesTestCase(TestCase):
    """Tests for the director_manage_roles view."""

    def setUp(self):
        # self.url = reverse('director_manage_roles')

        # self.current = UserAccount.objects.create_superuser(
        #     first_name='Ahmed',
        #     last_name='Pedro',
        #     email='apedro@example.org',
        #     password='Password123',
        #     gender = 'M',
        # )

        # self.admin = UserAccount.objects.create_admin(
        #     first_name='Jane',
        #     last_name='Doe',
        #     email='janedoe@example.org',
        #     password='Password123',
        #     gender = 'F',
        # )

        # self.director = UserAccount.objects.create_superuser(
        #     first_name='Jack',
        #     last_name='Smith',
        #     email='jsmith@example.org',
        #     password='Password123',
        #     gender = 'M',
        # )

        self.admin = UserAccount.objects.create_admin(
                first_name='Petra',
                last_name='Pickles',
                email= 'petra.pickles@example.org',
                password='Password123',
                gender = Gender.FEMALE,
            )

        self.teacher = UserAccount.objects.create_teacher(
            first_name='Barbare',
            last_name='Dutch',
            email='barbdutch@example.org',
            password='Password123',
            gender = Gender.FEMALE,
        )

        self.student = UserAccount.objects.create_student(
            first_name='Jane',
            last_name='Doe',
            email='janedoe@example.org',
            password='Password123',
            gender = 'F',
        )

        self.lesson = Lesson.objects.create(
            lesson_id=1,
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.THIRTY,
            lesson_date_time = datetime.datetime(2022, 4, 1, 0, 0, 0, 0).replace(tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = date(2022,10,25),
            lesson_status = LessonStatus.UNFULFILLED,
            term = 2,
        )

        self.invoice = Invoice.objects.create(
            reference_number = '1-001',
            student_ID = '1',
            fees_amount = '78',
            amounts_need_to_pay = '78',
            lesson_ID = self.lesson.lesson_id,
            invoice_status = InvoiceStatus.UNPAID,
        )

        self.url = reverse('student_requests', args=[self.student.id])

        self.form_input = {
                'type':  LessonType.INSTRUMENT,
                'duration': LessonDuration.HOUR,
                'lesson_date_time': datetime.datetime(2022, 4, 1, 0, 0, 0, 0).replace(tzinfo=timezone.utc),
                'teachers': self.teacher.id,
        }

    def test_student_requests_page_url(self):
        self.assertEqual(self.url,'/student_requests/3')


    def test_succesful_lesson_update(self):

        self.client.login(email=self.admin.email, password="Password123")

        lesson_count_before = Lesson.objects.count()

        self.update_lesson_url = reverse('admin_update_request', args=[self.lesson.lesson_id])
        response = self.client.post(self.update_lesson_url,self.form_input ,follow = True)

        updated_lesson = Lesson.objects.get(lesson_id=1)
        lesson_count_after = Lesson.objects.count()

        self.lesson.refresh_from_db()
        self.assertEqual(lesson_count_before,lesson_count_after)

        self.assertEqual(updated_lesson.type, self.form_input.get('type'))
        self.assertEqual(updated_lesson.duration,self.form_input.get('duration'))
        self.assertEqual(updated_lesson.lesson_date_time, self.form_input.get('lesson_date_time'))
        self.assertEqual(updated_lesson.teacher_id, self.teacher)

        #after sucessful lesson modification
        self.assertTemplateUsed(response, 'admin_student_requests_page.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    # tests booking lessons works as required

    def test_confirm_lesson_request(self):
        #Log into an admin account
        self.client.login(email=self.admin.email, password="Password123")

        # Confirm lesson booking
        lesson_count_before = Lesson.objects.count()
        self.confirm_lesson_url = reverse('admin_confirm_booking', args=[self.lesson.lesson_id])
        self.assertEquals(self.confirm_lesson_url, '/admin_confirm_booking/1')

        response = self.client.get(self.confirm_lesson_url, follow = True)

        lesson_count_after = Lesson.objects.count()
        self.assertEqual(lesson_count_before,lesson_count_after)

        confirmed_lesson = Lesson.objects.get(lesson_id= self.lesson.lesson_id)
        self.assertEqual(confirmed_lesson.lesson_status,'BK')

        redirect_url = reverse('student_requests', args=[self.student.id])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_student_requests_page.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    def test_cant_confirm_non_existing_lesson(self):

        self.client.login(email=self.admin.email, password="Password123")

        lesson_count_before = Lesson.objects.count()
        self.confirm_lesson_url = reverse('admin_confirm_booking', args=['4'])

        response = self.client.get(self.confirm_lesson_url, follow = True)
        lesson_count_after = Lesson.objects.count()

        self.assertEqual(lesson_count_before,lesson_count_after)

        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    # Test deleting lessons works as required
    def test_delete_lesson(self):

        self.client.login(email=self.admin.email, password="Password123")

        lesson_count_before = Lesson.objects.count()
        self.delete_lesson_url = reverse('delete_lesson', args=[self.lesson.lesson_id])
        response = self.client.get(self.delete_lesson_url, follow = True)
        lesson_count_after = Lesson.objects.count()
        self.assertEqual(lesson_count_before-1,lesson_count_after)

        redirect_url = reverse('student_requests', args=[self.student.id])
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_student_requests_page.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_cant_delete_non_existing_lesson(self):

        self.client.login(email=self.admin.email, password="Password123")

        lesson_count_before = Lesson.objects.count()
        self.delete_lesson_url = reverse('delete_lesson', args=['5'])
        response = self.client.get(self.delete_lesson_url, follow = True)
        lesson_count_after = Lesson.objects.count()
        self.assertEqual(lesson_count_before,lesson_count_after)

        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)
