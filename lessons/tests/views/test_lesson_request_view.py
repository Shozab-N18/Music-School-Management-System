
from django.test import TestCase
from django.urls import reverse
from lessons.forms import RequestForm
from lessons.models import Lesson, UserAccount,Gender,UserRole,LessonType,LessonDuration,LessonStatus

from lessons.helper import get_student_and_child_objects
from django import forms
from django.utils import timezone
import datetime
from lessons.tests.helpers import reverse_with_next
from bootstrap_datepicker_plus.widgets import DateTimePickerInput

from django.db import IntegrityError
from django.db import transaction

class LessonRequestViewTestCase(TestCase):
    """Unit tests for the lesson request view"""

    fixtures = ['lessons/tests/fixtures/useraccounts.json'], ['lessons/tests/fixtures/lessons.json']
    def setUp(self):
        self.url = reverse('requests_page')

        self.admin = UserAccount.objects.get(email='bobby@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.saved_lesson = Lesson.objects.get(lesson_id = 1)

        self.saved_lesson2 = Lesson.objects.get(lesson_id = 2)

    def create_child_student(self):
        self.child = UserAccount.objects.get(email='bobbylee@example.org')

    def change_lessons_status_to_unfulfilled(self):
        self.saved_lesson.lesson_status = LessonStatus.UNFULFILLED
        self.saved_lesson.save()
        self.saved_lesson2.lesson_status = LessonStatus.UNFULFILLED
        self.saved_lesson2.save()

    def test_request_url(self):
        self.assertEqual(self.url,'/requests_page/')

    def test_get_request_page_without_being_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url,follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

    def test_not_student_accessing_request_page(self):
        self.client.login(email=self.admin.email, password="Password123")
        response = self.client.get(self.url, follow = True)
        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')

    def test_drop_down_of_users_is_populated_with_student_and_child(self):
        self.create_child_student()
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.url, follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        student_options = response.context['students_option']

        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertTrue(self.child in student_options)

    def test_drop_down_of_users_is_populated_with_student(self):
        self.client.login(email=self.student.email, password="Password123")
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.get(self.url, follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        self.assertTrue(self.student in student_options)

    def test_function_to_get_student_and_children(self):
        #self.fail()
        self.create_child_student()
        options = get_student_and_child_objects(self.student)

        self.assertEqual(len(options),2)

        self.assertTrue(self.student in options)
        self.assertTrue(self.child in options)

        actual_student = list(filter(lambda student: student.email == self.student.email,options))
        actual_child = list(filter(lambda student: student.email == self.child.email,options))

        self.assertEqual(actual_student[0].email,self.student.email)
        self.assertEqual(actual_child[0].email,self.child.email)

        self.assertTrue(actual_student[0].is_parent)
        self.assertEqual(actual_student[0].parent_of_user,None)
        self.assertEqual(actual_child[0].parent_of_user.email,actual_student[0].email)

        self.assertEqual(actual_student[0].role,UserRole.STUDENT)
        self.assertEqual(actual_child[0].role,UserRole.STUDENT)

    def test_saved_lessons_with_different_request_date(self):
        Lesson.objects.get(lesson_id = 3).delete()
        Lesson.objects.get(lesson_id = 4).delete()
        Lesson.objects.get(lesson_id = 5).delete()

        self.client.login(email=self.student.email, password="Password123")
        self.saved_lesson2.request_date = datetime.date(2022, 11, 15)
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.get(self.url, follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        form = response.context['form']
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        self.assertTrue(self.student in student_options)
        self.assertEqual(len(response.context['lessons']),2)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)


    def test_get_request_page_with_saved_lessons(self):
        self.client.login(email=self.student.email, password="Password123")
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.get(self.url, follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        form = response.context['form']
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        self.assertTrue(self.student in student_options)

        self.assertEqual(len(response.context['lessons']),5)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        date_time_widget = form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(isinstance(form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(form.fields['teachers'], forms.ModelChoiceField))

    def test_get_request_page_without_saved_lessons(self):
        self.change_lessons_status_to_unfulfilled()
        Lesson.objects.get(lesson_id = 1).delete()
        Lesson.objects.get(lesson_id = 2).delete()
        Lesson.objects.get(lesson_id = 3).delete()
        Lesson.objects.get(lesson_id = 4).delete()
        Lesson.objects.get(lesson_id = 5).delete()

        self.client.login(email=self.student.email, password="Password123")
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        response = self.client.get(self.url, follow = True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        form = response.context['form']
        self.assertEqual(len(response.context['lessons']),0)
        student_options = response.context['students_option']

        self.assertEqual(len(student_options),1)
        self.assertTrue(self.student in student_options)
        self.assertTrue(isinstance(form, RequestForm))
        self.assertFalse(form.is_bound)

        date_time_widget = form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(isinstance(form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(form.fields['teachers'], forms.ModelChoiceField))

    def test_post_request_page_forbidden(self):
        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.post(self.url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(before_count, after_count)
