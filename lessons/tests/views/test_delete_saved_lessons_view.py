from django.test import TestCase
from django.urls import reverse
from lessons.models import UserAccount, Lesson, Gender, LessonType,LessonDuration,LessonStatus
import datetime
from django.utils import timezone
from django.contrib import messages


class StudentFeedDeleteSavedLessonTestCase(TestCase):
    """Unit tests for the delete saved lessons view"""

    fixtures = ['lessons/tests/fixtures/useraccounts.json'], ['lessons/tests/fixtures/lessons.json']

    def setUp(self):

        self.admin = UserAccount.objects.get(email='bobby@example.org')

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.teacher2 = UserAccount.objects.get(email='amanehill@example.org')

        self.teacher3 = UserAccount.objects.get(email='johnjacks@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.lesson = Lesson.objects.get(lesson_id=1)

        self.delete_saved_url = reverse('delete_saved', kwargs={'lesson_id':self.lesson.lesson_id})

        self.lesson2 = Lesson.objects.get(lesson_id=2)

        self.lesson3 = Lesson.objects.get(lesson_id=3)

        self.lesson4 = Lesson.objects.get(lesson_id=4)

        self.lesson5 = Lesson.objects.get(lesson_id=5)

    def create_child_student(self):
        self.child = UserAccount.objects.get(email='bobbylee@example.org')

        self.child_lesson = Lesson.objects.create(
            type = LessonType.PRACTICE,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2023, 2, 25, 9, 45, 00, tzinfo=timezone.utc),
            teacher_id = self.teacher3,
            student_id = self.student,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.SAVED,
        )

    def test_delete_saved_url(self):
        self.assertEqual(self.delete_saved_url, f'/delete_saved/{self.lesson.lesson_id}')

    def test_get_delete_saved_lessons_url(self):
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.delete_saved_url, follow = True)
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),5)
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')


    def test_attempt_deletion_of_other_student_lessons(self):
        self.student_jane = UserAccount.objects.get(email='janedoe@example.org')

        self.client.login(email=self.student_jane.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.delete_saved_url, follow = True)
        after_count = Lesson.objects.count()
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),1)
        self.assertTrue(self.student_jane in student_options)
        self.assertEqual(before_count,after_count)
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),5)
        self.assertEqual(response.status_code, 200)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Attempted Deletion Not Permitted')
        self.assertEqual(messages_list[0].level, messages.WARNING)

        self.assertTemplateUsed(response, 'requests_page.html')

    def test_student_not_logged_in_deleting_saved_lessons(self):
        response = self.client.get(self.delete_saved_url, follow = True)
        redirect_url = reverse('home')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),5)
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)


    def test_not_student_accessing_deleting_saved_lessons(self):
        self.client.login(email=self.admin.email, password="Password123")
        response = self.client.get(self.delete_saved_url, follow = True)
        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),5)
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)

    def test_incorrect_deletion_of_lesson(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        self.delete_saved_url = reverse('delete_saved', kwargs={'lesson_id':60})
        response = self.client.post(self.delete_saved_url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(before_count, after_count)
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)

        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),5)

        self.assertEqual(response.status_code, 200)

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Incorrect lesson ID passed')
        self.assertEqual(messages_list[0].level, messages.ERROR)

        self.assertTemplateUsed(response, 'requests_page.html')

    def test_succesful_deletion_of_saved_lesson(self):

        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.delete_saved_url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(before_count-1, after_count)
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),4)
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Saved lesson deleted')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_succesful_multiple_deletion_of_lessons(self):
        before_count = Lesson.objects.count()

        self.client.login(email=self.student.email, password="Password123")

        response = self.client.post(self.delete_saved_url, follow = True)
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Saved lesson deleted')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        self.delete_saved_url = reverse('delete_saved', kwargs={'lesson_id':self.lesson2.lesson_id})
        response_second = self.client.post(self.delete_saved_url, follow = True)
        student_options = response_second.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertEqual(student_options[0], self.student)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response_second, 'requests_page.html')
        messages_list = list(response_second.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Saved lesson deleted')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        self.delete_saved_url = reverse('delete_saved', kwargs={'lesson_id':self.lesson3.lesson_id})
        response_third = self.client.post(self.delete_saved_url, follow = True)
        student_options = response_third.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response_third, 'requests_page.html')

        messages_list = list(response_third.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Saved lesson deleted')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        after_count = Lesson.objects.count()
        self.assertEqual(before_count-3, after_count)
        self.assertEqual(Lesson.objects.filter(student_id = self.student).count(),2)


    def test_delete_child_lesson(self):
        self.create_child_student()
        self.delete_saved_url = reverse('delete_saved', kwargs={'lesson_id':self.child_lesson.lesson_id})

        self.client.login(email=self.student.email, password="Password123")
        before_count = Lesson.objects.count()
        response = self.client.post(self.delete_saved_url, follow = True)
        after_count = Lesson.objects.count()
        self.assertEqual(before_count-1, after_count)
        student_options = response.context['students_option']
        self.assertEqual(len(student_options),2)
        self.assertTrue(self.student in student_options)
        self.assertTrue(self.child in student_options)
        self.assertEqual(Lesson.objects.filter(student_id = self.child).count(),0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'requests_page.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'Saved lesson deleted')
        self.assertEqual(messages_list[0].level, messages.SUCCESS)
