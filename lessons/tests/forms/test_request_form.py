from django import forms
from lessons.forms import RequestForm
from django.test import TestCase
from lessons.models import Lesson, LessonType,LessonDuration,LessonStatus,Gender, UserAccount
import datetime
from django.utils import timezone
from django.urls import reverse


class RequestFormTestCase(TestCase):
    """Unit tests of the sign up form."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']



    def setUp(self):

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')
        self.student = UserAccount.objects.get(email='johndoe@example.org')
        self.form_input = {
            'type': LessonType.INSTRUMENT,
            'duration': LessonDuration.THIRTY,
            'lesson_date_time' : datetime.datetime(2023, 4, 4, 15, 15, 15, tzinfo=timezone.utc),
            'teachers': self.teacher.id,
            'selectedStudent': self.student.email,
        }

        self.url = reverse('new_lesson')
    def test_valid_request_form(self):
        form = RequestForm(data = self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = RequestForm()
        self.assertIn('type', form.fields)
        self.assertIn('duration', form.fields)
        self.assertIn('lesson_date_time', form.fields)
        self.assertIn('teachers', form.fields)
        date_time_field = form.fields['lesson_date_time']
        self.assertTrue(isinstance(date_time_field, forms.DateTimeField))
