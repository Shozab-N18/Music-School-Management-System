from django.test import TestCase
from django.urls import reverse
from lessons.models import UserAccount, Lesson, UserRole, Gender, LessonType,LessonDuration,LessonStatus, Term
from lessons.forms import RequestForm
from django.contrib import messages
from django import forms
import datetime
from django.utils import timezone
from bootstrap_datepicker_plus.widgets import DateTimePickerInput
from django.conf import settings

class StudentFeedEditLessonTestCase(TestCase):
    """Unit tests for editing a requested lesson view."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json'], ['lessons/tests/fixtures/lessons.json']

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

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.other_student = UserAccount.objects.get(email='janedoe@example.org')

        self.lesson = Lesson.objects.get(lesson_id=1)
        self.lesson.lesson_status = LessonStatus.FULLFILLED
        self.lesson.save()

        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson.lesson_id})

        self.admin = UserAccount.objects.get(email='bobby@example.org')

        self.teacher2 = UserAccount.objects.get(email='amanehill@example.org')

        self.teacher3 = UserAccount.objects.get(email='johnjacks@example.org')

        self.lesson2 = Lesson.objects.get(lesson_id=2)
        self.lesson2.lesson_status = LessonStatus.FULLFILLED
        self.lesson2.save()

        self.lesson3 = Lesson.objects.get(lesson_id=3)
        self.lesson3.lesson_status = LessonStatus.FULLFILLED
        self.lesson3.save()

        self.lesson4 = Lesson.objects.get(lesson_id=4)
        self.lesson4.lesson_status = LessonStatus.FULLFILLED
        self.lesson4.save()

        self.lesson5 = Lesson.objects.get(lesson_id=5)
        self.lesson5.lesson_status = LessonStatus.FULLFILLED
        self.lesson5.save()

        self.lesson6 = Lesson.objects.create(
            type = LessonType.PRACTICE,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2023, 1, 25, 9, 45, 00, tzinfo=timezone.utc),
            teacher_id = self.teacher3,
            student_id = self.other_student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED,
        )

    def create_child_student(self):
        self.child = UserAccount.objects.get(email='bobbylee@example.org')

    def change_lessons_status_to_unfulfilled(self):
        self.lesson.lesson_status = LessonStatus.UNFULFILLED
        self.lesson.save()
        self.lesson2.lesson_status = LessonStatus.UNFULFILLED
        self.lesson2.save()
        self.lesson3.lesson_status = LessonStatus.UNFULFILLED
        self.lesson3.save()
        self.lesson4.lesson_status = LessonStatus.UNFULFILLED
        self.lesson4.save()
        self.lesson5.lesson_status = LessonStatus.UNFULFILLED
        self.lesson5.save()


    def create_forms(self):
        self.form_input = {
            'type': LessonType.INSTRUMENT,
            'duration': LessonDuration.FOURTY_FIVE,
            'lesson_date_time' : datetime.datetime(2022, 9, 21, 16, 00, 00, tzinfo=timezone.utc),
            'teachers': self.teacher2.id,
        }

        self.form_input2 = {
            'type': LessonType.PERFORMANCE,
            'duration': LessonDuration.HOUR,
            'lesson_date_time' : datetime.datetime(2022, 9, 17, 16, 00, 00, tzinfo=timezone.utc),
            'teachers': self.teacher3.id,
        }

        self.form_input_with_invalid_date = {
            'type': LessonType.PERFORMANCE,
            'duration': LessonDuration.HOUR,
            'lesson_date_time' : datetime.datetime(2024, 7, 17, 16, 00, 00, tzinfo=timezone.utc),
            'teachers': self.teacher3.id,
        }

        self.form_input_invalid_date_before_CURRENT_DATE = {
            'type': LessonType.PERFORMANCE,
            'duration': LessonDuration.HOUR,
            'lesson_date_time' : datetime.datetime(2019, 7, 17, 16, 00, 00, tzinfo=timezone.utc),
            'teachers': self.teacher3.id,
        }

    def test_edit_lesson_url(self):
        self.assertEqual(self.edit_url, f'/edit_lesson/{self.lesson.lesson_id}')

    def test_get_edit_pending_lesson_with_incorrect_lesson_id(self):
        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':0})
        before_count = Lesson.objects.count()

        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        response = self.client.get(self.edit_url, follow = True)
        after_count = Lesson.objects.count()

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        self.assertEqual(before_count,after_count)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Incorrect lesson ID passed')
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_unsuccesful_request_date_smaller_then_CURRENT_DATE(self):
        self.change_lessons_status_to_unfulfilled()
        self.create_forms()
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.edit_url, self.form_input_invalid_date_before_CURRENT_DATE, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)

        self.assertTemplateUsed(response, 'edit_request.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'The lesson date provided is beyond the term dates available')
        self.assertEqual(messages_list[0].level, messages.ERROR)

        actual_lesson = Lesson.objects.get(lesson_id = self.lesson.lesson_id)

        self.assertEqual(actual_lesson.type, self.lesson.type)
        self.assertEqual(actual_lesson.duration, self.lesson.duration)
        self.assertEqual(actual_lesson.lesson_date_time, self.lesson.lesson_date_time)
        self.assertEqual(actual_lesson.request_date, self.lesson.request_date)

    def test_not_logged_in_accessing_edit_pending_lessons(self):
        before_count = Lesson.objects.count()
        self.change_lessons_status_to_unfulfilled()
        response = self.client.get(self.edit_url, follow = True)
        after_count = Lesson.objects.count()

        redirect_url = reverse('home')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

        self.assertEqual(before_count,after_count)

    
    def test_not_student_accessing_editing_pending_lessons(self):
        self.client.login(email=self.admin.email, password="Password123")
        response = self.client.get(self.edit_url, follow = True)
        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')

    def test_unsuccesful_new_lesson_request_lesson_date_outside_term_dates(self):
        self.create_forms()
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        self.change_lessons_status_to_unfulfilled()
        response = self.client.post(self.edit_url,self.form_input_with_invalid_date,follow=True)
        after_count = Lesson.objects.count()
        self.assertEqual(after_count, before_count)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_request.html')

        response_form = response.context['form']
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'The lesson date provided is beyond the term dates available')
        self.assertEqual(messages_list[0].level, messages.ERROR)
        self.assertTrue(isinstance(response_form, RequestForm))
        self.assertTrue(response_form.is_bound)

    def test_not_permitted_edit_with_valid_but_not_accessible_lesson_id_get(self):
        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson6.lesson_id})
        response = self.client.get(self.edit_url, follow = True)
        after_count = Lesson.objects.count()

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Attempted Edit Is Not Permitted')
        self.assertEqual(messages_list[0].level, messages.WARNING)

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        self.assertEqual(before_count,after_count)

    def test_not_permitted_edit_with_valid_but_not_accessible_lesson_id_with_post(self):
        self.create_forms()
        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson6.lesson_id})
        response = self.client.post(self.edit_url, self.form_input,follow = True)
        after_count = Lesson.objects.count()

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Attempted Edit Is Not Permitted')
        self.assertEqual(messages_list[0].level, messages.WARNING)

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')
        self.assertEqual(before_count,after_count)

        attempted_to_change_lesson = Lesson.objects.get(lesson_id = self.lesson6.lesson_id)

        self.assertEqual(attempted_to_change_lesson.student_id,self.other_student)
        self.assertEqual(attempted_to_change_lesson.teacher_id,self.teacher3)
        self.assertEqual(attempted_to_change_lesson.type,self.lesson6.type)
        self.assertEqual(attempted_to_change_lesson.duration,self.lesson6.duration)
        self.assertEqual(attempted_to_change_lesson.lesson_status,self.lesson6.lesson_status)


    def test_get_edit_pending_lesson_with_correct_lesson_id(self):
        before_count = Lesson.objects.count()

        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        response = self.client.get(self.edit_url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'edit_request.html')

        self.assertEqual(before_count,after_count)

        response_form = response.context['form']
        lesson_id = response.context['lesson_id']

        self.assertTrue(isinstance(response_form, RequestForm))
        self.assertTrue(response_form.is_bound)
        self.assertEqual(int(lesson_id),self.lesson.lesson_id)

        date_time_widget = response_form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(isinstance(response_form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['teachers'], forms.ModelChoiceField))

        self.assertTrue(response_form.is_valid())

        self.assertEqual(response_form.cleaned_data.get("type"), self.lesson.type)
        self.assertEqual(response_form.cleaned_data.get("duration"), self.lesson.duration)
        self.assertEqual(response_form.cleaned_data.get("teachers"),self.teacher)
        self.assertEqual(response_form.cleaned_data.get("lesson_date_time"),self.lesson.lesson_date_time)

    def test_get_edit_pending_lesson_with_correct_lesson_third(self):
        before_count = Lesson.objects.count()
        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson3.lesson_id})

        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        response = self.client.get(self.edit_url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(response.status_code, 200)

        self.assertTemplateUsed(response, 'edit_request.html')

        self.assertEqual(before_count,after_count)

        response_form = response.context['form']
        lesson_id = response.context['lesson_id']

        self.assertTrue(isinstance(response_form, RequestForm))
        self.assertTrue(response_form.is_bound)
        self.assertEqual(int(lesson_id),self.lesson3.lesson_id)

        date_time_widget = response_form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(isinstance(response_form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['teachers'], forms.ModelChoiceField))

        self.assertTrue(response_form.is_valid())

        self.assertEqual(response_form.cleaned_data.get("type"),self.lesson3.type)
        self.assertEqual(response_form.cleaned_data.get("duration"),self.lesson3.duration)
        self.assertEqual(response_form.cleaned_data.get("teachers"),self.teacher2)
        self.assertEqual(response_form.cleaned_data.get("lesson_date_time"),self.lesson3.lesson_date_time)

    def test_edit_lesson_without_form(self):
        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        response = self.client.post(self.edit_url, follow = True)
        after_count = Lesson.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_request.html')
        self.assertEqual(before_count,after_count)

        response_form = response.context['form']
        lesson_id = response.context['lesson_id']

        self.assertTrue(isinstance(response_form, RequestForm))
        self.assertTrue(response_form.is_bound)
        self.assertEqual(int(lesson_id),self.lesson.lesson_id)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Form is not valid')
        self.assertEqual(messages_list[0].level, messages.ERROR)

        date_time_widget = response_form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(response_form.is_valid())

        self.assertTrue(isinstance(response_form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['teachers'], forms.ModelChoiceField))

        self.assertEqual(response_form.cleaned_data.get("type"), self.lesson.type)
        self.assertEqual(response_form.cleaned_data.get("duration"), self.lesson.duration)
        self.assertEqual(response_form.cleaned_data.get("teachers"),self.teacher)
        self.assertEqual(response_form.cleaned_data.get("lesson_date_time"),self.lesson.lesson_date_time)


    def test_edit_lesson_without_valid_form_type_data(self):
        self.create_forms()
        self.form_input['type'] = 'Incorrect type input'
        before_count = Lesson.objects.count()

        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()
        response = self.client.post(self.edit_url,self.form_input, follow = True)
        after_count = Lesson.objects.count()

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'edit_request.html')
        self.assertEqual(before_count,after_count)

        response_form = response.context['form']
        lesson_id = response.context['lesson_id']

        self.assertTrue(isinstance(response_form, RequestForm))
        self.assertTrue(response_form.is_bound)
        self.assertEqual(int(lesson_id),self.lesson.lesson_id)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Form is not valid')
        self.assertEqual(messages_list[0].level, messages.ERROR)

        date_time_widget = response_form.fields['lesson_date_time'].widget
        self.assertTrue(isinstance(date_time_widget, DateTimePickerInput))

        self.assertTrue(response_form.is_valid())

        self.assertTrue(isinstance(response_form.fields['type'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['duration'], forms.TypedChoiceField))
        self.assertTrue(isinstance(response_form.fields['teachers'], forms.ModelChoiceField))

        self.assertEqual(response_form.cleaned_data.get("type"), self.lesson.type)
        self.assertEqual(response_form.cleaned_data.get("duration"), self.lesson.duration)
        self.assertEqual(response_form.cleaned_data.get("teachers"),self.teacher)
        self.assertEqual(response_form.cleaned_data.get("lesson_date_time"),self.lesson.lesson_date_time)

    def test_apply_edit_to_lesson_succesfully(self):
        self.create_forms()
        request_date = self.lesson.request_date

        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()

        response = self.client.post(self.edit_url,self.form_input, follow = True)

        after_count = Lesson.objects.count()

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        self.assertEqual(before_count,after_count)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Succesfully edited lesson')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        updated_lesson = Lesson.objects.get(lesson_id = self.lesson.lesson_id)

        self.assertEqual(updated_lesson.student_id,self.student)
        self.assertEqual(updated_lesson.type, LessonType.INSTRUMENT)
        self.assertEqual(updated_lesson.request_date, request_date)
        self.assertEqual(updated_lesson.duration, LessonDuration.FOURTY_FIVE)
        self.assertEqual(updated_lesson.teacher_id,self.teacher2)
        self.assertEqual(updated_lesson.lesson_date_time,datetime.datetime(2022, 9, 21, 16, 00, 00, tzinfo=timezone.utc))

    def test_apply_edit_to_lesson2_succesfully(self):
        self.create_forms()
        request_date = self.lesson2.request_date
        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()

        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson2.lesson_id})
        response = self.client.post(self.edit_url,self.form_input2, follow = True)

        after_count = Lesson.objects.count()

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        self.assertEqual(before_count,after_count)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Succesfully edited lesson')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        updated_lesson = Lesson.objects.get(lesson_id = self.lesson2.lesson_id)

        self.assertEqual(updated_lesson.student_id,self.student)
        self.assertEqual(updated_lesson.type, LessonType.PERFORMANCE)
        self.assertEqual(updated_lesson.request_date, request_date)
        self.assertEqual(updated_lesson.duration, LessonDuration.HOUR)
        self.assertEqual(updated_lesson.teacher_id,self.teacher3)
        self.assertEqual(updated_lesson.lesson_date_time,datetime.datetime(2022, 9, 17, 16, 00, 00, tzinfo=timezone.utc))

    def test_apply_edit_to_child_lesson_succesfully(self):
        self.create_child_student()
        self.create_forms()
        self.lesson4.student_id = self.child
        request_date = self.lesson4.request_date

        before_count = Lesson.objects.count()
        self.client.login(email=self.student.email, password="Password123")
        self.change_lessons_status_to_unfulfilled()

        self.edit_url = reverse('edit_lesson', kwargs={'lesson_id':self.lesson4.lesson_id})
        response = self.client.post(self.edit_url,self.form_input2, follow = True)

        after_count = Lesson.objects.count()

        redirect_url = reverse('student_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        self.assertEqual(before_count,after_count)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Succesfully edited lesson')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        updated_lesson = Lesson.objects.get(lesson_id = self.lesson4.lesson_id)

        self.assertEqual(updated_lesson.student_id,self.child)
        self.assertEqual(updated_lesson.type, LessonType.PERFORMANCE)
        self.assertEqual(updated_lesson.request_date, request_date)
        self.assertEqual(updated_lesson.duration, LessonDuration.HOUR)
        self.assertEqual(updated_lesson.teacher_id,self.teacher3)
        self.assertEqual(updated_lesson.lesson_date_time,datetime.datetime(2022, 9, 17, 16, 00, 00, tzinfo=timezone.utc))
