from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from lessons.models import Lesson, UserAccount,Gender,UserRole,LessonType,LessonDuration,LessonStatus,Term
from django.contrib import messages
from lessons.forms import RequestForm
from lessons.views import get_saved_lessons
from django.conf import settings
from django.utils import timezone
from datetime import time
import datetime
from lessons.tests.helpers import reverse_with_next

from django.db import IntegrityError
from django.db import transaction

class RequestNewLessonTest(TestCase):
    """Unit tests for requesting a new lesson view."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']

    def setUp(self):
        settings.CURRENT_DATE = datetime.date(2022, 9,1)

        self.term_six = Term.objects.create(
            term_number=6,
            start_date = datetime.date(2023, 6,5),
            end_date = datetime.date(2023, 7,21),
        )

        self.term_one = Term.objects.create(
            term_number=1,
            start_date = datetime.date(2022, 9,1),
            end_date = datetime.date(2022, 10,21),
        )

        self.admin = UserAccount.objects.get(email='bobby@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.url = reverse('new_lesson')

        self.form_input = {
            'type': LessonType.INSTRUMENT,
            'duration': LessonDuration.THIRTY,
            'lesson_date_time' : datetime.datetime(2023, 4, 4, 15, 15, 15, tzinfo=timezone.utc),
            'teachers': self.teacher.id,
            'selectedStudent': self.student.email,
        }

        self.form_input_2 = {
            'type': LessonType.PERFORMANCE,
            'duration': LessonDuration.HOUR,
            'lesson_date_time' : datetime.datetime(2023, 5, 4, 15, 15, 15, tzinfo=timezone.utc),
            'teachers': self.teacher.id,
            'selectedStudent': self.student.email,
        }

        self.form_input_invalid_date = {
            'type': LessonType.THEORY,
            'duration': LessonDuration.FOURTY_FIVE,
            'lesson_date_time' : datetime.datetime(2023, 9, 4, 15, 15, 15, tzinfo=timezone.utc),
            'teachers': self.teacher.id,
            'selectedStudent': self.student.email,
        }

        self.form_input_invalid_date_before_CURRENT_DATE = {
            'type': LessonType.THEORY,
            'duration': LessonDuration.FOURTY_FIVE,
            'lesson_date_time' : datetime.datetime(2022, 8, 30, 15, 15, 15, tzinfo=timezone.utc),
            'teachers': self.teacher.id,
            'selectedStudent': self.student.email,
        }

    def create_child_student(self):
        self.child = UserAccount.objects.get(email='bobbylee@example.org')

    def create_saved_lessons(self):
        self.saved_lesson = Lesson.objects.create(
            type = LessonType.INSTRUMENT,
            duration = LessonDuration.THIRTY,
            lesson_date_time = datetime.datetime(2022, 11, 20, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED
        )


        self.saved_lesson2 = Lesson.objects.create(
            type = LessonType.THEORY,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2022, 10, 20, 15, 0, 0, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED
        )

        self.saved_lesson3 = Lesson.objects.create(
            type = LessonType.PERFORMANCE,
            duration = LessonDuration.HOUR,
            lesson_date_time = datetime.datetime(2022, 9, 20, 9, 45, 0, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED
        )

    def test_new_lesson_url(self):
        self.assertEqual(self.url,'/new_lesson/')

    def test_valid_new_lesson_form(self):
        self.assertEqual(len(UserAccount.objects.filter(role = UserRole.TEACHER)), 3)
        form = RequestForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_unsuccesful_new_lesson_selected_selectedStudent_is_not_valid(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        self.form_input['selectedStudent'] = 'notextistentemail@example.org'
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.post(self.url, self.form_input, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        form = response.context['form']
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Selected user account does not exist')
        self.assertEqual(messages_list[0].level, messages.ERROR)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertTrue(form.is_bound)

    def test_unsuccesful_new_lesson_request_lesson_date_outside_term_dates(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.post(self.url,self.form_input_invalid_date,follow=True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        form = response.context['form']
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'The lesson date provided is beyond the term dates available')
        self.assertEqual(messages_list[0].level, messages.ERROR)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertTrue(form.is_bound)

    def test_unsuccesful_new_lesson_not_logged_in(self):
        redirect_url = reverse('home',)
        before_count = Lesson.objects.count()
        response = self.client.get(self.url,follow = True)
        after_count = Lesson.objects.count()
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertEqual(after_count, before_count)

    def test_get_new_lesson_without_lessons_saved(self):
        redirect_url = reverse('requests_page')
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.url, follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'requests_page.html')
        form = response.context['form']

        self.assertEqual(len(response.context['lessons']),0)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

    def test_get_new_lesson_with_lessons_saved(self):
        redirect_url = reverse('requests_page')
        self.create_saved_lessons()
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.url, follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'requests_page.html')
        form = response.context['form']
        self.assertEqual(len(response.context['lessons']),3)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

    def test_unsuccesful_new_lesson_user_is_admin(self):
        self.client.login(email=self.admin.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.get(self.url,follow=True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)

        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')


    def test_unsuccesful_lesson_request_bad_data_lesson_type(self):
        self.client.login(email=self.student.email, password="Password123")
        self.form_input['type'] = 'BAD CHOICE'

        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'requests_page.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertTrue(form.is_bound)
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'The lesson information provided is invalid!')
        self.assertEqual(messages_list[0].level, messages.ERROR)


    def test_unsuccesful_lesson_request_bad_data_lesson_duration(self):
        self.client.login(email=self.student.email, password="Password123")
        self.form_input['duration'] = 'BAD DURATION CHOICE'

        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input, follow = True)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'requests_page.html')
        form = response.context['form']
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'The lesson information provided is invalid!')
        self.assertEqual(messages_list[0].level, messages.ERROR)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertTrue(form.is_bound)

    def test_unsuccesful_request_date_smaller_then_CURRENT_DATE(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.url, self.form_input_invalid_date_before_CURRENT_DATE, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)
        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertTrue(form.is_bound)

        self.assertTemplateUsed(response, 'requests_page.html')

    def test_succesful_request(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.url, self.form_input, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count+1)
        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        lessons = response.context['lessons']
        self.assertEqual(len(lessons),1)
        #check lessons size is now 4 for the user
        self.assertEqual(lessons[0].student_id.email, self.student.email)
        self.assertEqual(lessons[0].type,LessonType.INSTRUMENT)
        self.assertEqual(lessons[0].duration, LessonDuration.THIRTY)
        self.assertEqual(lessons[0].lesson_date_time, datetime.datetime(2023, 4, 4, 15, 15, 15, tzinfo=timezone.utc))
        self.assertEqual(lessons[0].teacher_id, self.teacher)

        self.assertTemplateUsed(response, 'requests_page.html')

    def test_multiple_lesson_creation_by_student(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.url, self.form_input, follow = True)
        second_response = self.client.post(self.url, self.form_input_2, follow = True)

        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count+2)
        self.assertTemplateUsed(second_response, 'requests_page.html')

        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        form = second_response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        lessons = second_response.context['lessons']
        actual_lessons = Lesson.objects.filter(lesson_status = LessonStatus.SAVED, student_id = self.student)
        self.assertEqual(len(lessons),len(actual_lessons))
        self.assertEqual(lessons[0].student_id.email, self.student.email)
        self.assertEqual(lessons[0].type,actual_lessons[0].type)
        self.assertEqual(lessons[0].duration, actual_lessons[0].duration)
        self.assertEqual(lessons[0].lesson_date_time, actual_lessons[0].lesson_date_time)
        self.assertEqual(lessons[0].teacher_id, self.teacher)

        self.assertEqual(lessons[1].student_id.email, self.student.email)
        self.assertEqual(lessons[1].type,actual_lessons[1].type)
        self.assertEqual(lessons[1].duration, actual_lessons[1].duration)
        self.assertEqual(lessons[1].lesson_date_time, actual_lessons[1].lesson_date_time)
        self.assertEqual(lessons[1].teacher_id, self.teacher)

    def test_succesful_child_request(self):
        self.create_child_student()
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        #change the forms
        self.form_input['selectedStudent'] = self.child.email
        response = self.client.post(self.url, self.form_input, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count+1)
        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        lessons = response.context['lessons']
        self.assertEqual(len(lessons),1)

        self.assertEqual(lessons[0].student_id.email, self.child.email)
        self.assertEqual(lessons[0].type,LessonType.INSTRUMENT)
        self.assertEqual(lessons[0].duration, LessonDuration.THIRTY)
        self.assertEqual(lessons[0].lesson_date_time, datetime.datetime(2023, 4, 4, 15, 15, 15, tzinfo=timezone.utc))
        self.assertEqual(lessons[0].teacher_id, self.teacher)

        self.assertTemplateUsed(response, 'requests_page.html')

    def test_succesful_child_request_and_student_request(self):
        self.create_child_student()
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        #change the forms
        self.form_input['selectedStudent'] = self.child.email
        response = self.client.post(self.url, self.form_input, follow = True)
        second_response = self.client.post(self.url, self.form_input_2, follow = True)

        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count+2)

        form = response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        form = second_response.context['form']
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        lessons = second_response.context['lessons']
        self.assertEqual(len(lessons),2)

        child_lesson = Lesson.objects.get(lesson_status = LessonStatus.SAVED, student_id = self.child)
        student_lesson = Lesson.objects.get(lesson_status = LessonStatus.SAVED,student_id  = self.student)

        self.assertEqual(lessons[0].student_id.email, self.student.email)
        self.assertEqual(lessons[0].type,student_lesson.type)
        self.assertEqual(lessons[0].duration, student_lesson.duration)
        self.assertEqual(lessons[0].lesson_date_time, student_lesson.lesson_date_time)
        self.assertEqual(lessons[0].teacher_id, self.teacher)

        self.assertEqual(lessons[1].student_id.email, self.child.email)
        self.assertEqual(lessons[1].type,child_lesson.type)
        self.assertEqual(lessons[1].duration, child_lesson.duration)
        self.assertEqual(lessons[1].lesson_date_time, child_lesson.lesson_date_time)
        self.assertEqual(lessons[1].teacher_id, self.teacher)

        self.assertTemplateUsed(response, 'requests_page.html')
