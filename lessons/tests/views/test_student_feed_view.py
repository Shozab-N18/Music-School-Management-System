
from django.test import TestCase
from django.urls import reverse
from lessons.models import UserAccount, Lesson, Gender, LessonType,LessonDuration,LessonStatus
from lessons.helper import make_lesson_dictionary, make_lesson_timetable_dictionary,get_student_and_child_objects,get_student_and_child_lessons
import datetime
from django.utils import timezone
from lessons.tests.helpers import reverse_with_next

class StudentFeedTestCase(TestCase):
    """Tests for the student feed view."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json'], ['lessons/tests/fixtures/lessons.json']
    def setUp(self):

        self.url = reverse('student_feed')

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.teacher2 = UserAccount.objects.get(email='amanehill@example.org')

        self.teacher3 = UserAccount.objects.get(email='johnjacks@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.lesson = Lesson.objects.get(lesson_id=1)
        self.lesson.lesson_status = LessonStatus.FULLFILLED
        self.lesson.save()

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

    def initialise_admin(self):
        self.admin = UserAccount.objects.get(email='bobby@example.org')

    def create_child_student_with_lessons(self):
        self.child = UserAccount.objects.get(email='bobbylee@example.org')

        self.lesson.student_id = self.child
        self.lesson.save()
        self.lesson2.student_id = self.child
        self.lesson2.save()
        self.lesson3.student_id = self.child
        self.lesson3.save()

    def change_some_lessons_to_unfulfilled(self):
        self.lesson.lesson_status = LessonStatus.UNFULFILLED
        self.lesson.save()
        self.lesson2.lesson_status = LessonStatus.UNFULFILLED
        self.lesson2.save()

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

    def create_child_with_different_request_dates(self):
        self.create_child_student_with_lessons()
        self.lesson.request_date = datetime.date(2022, 8, 15)
        self.lesson.save()
        self.lesson2.request_date = datetime.date(2022, 8, 15)
        self.lesson2.save()
        self.lesson5.request_date = datetime.date(2022, 8, 15)
        self.lesson5.save()
        self.change_lessons_status_to_unfulfilled()

    def changes_some_lessons_status_to_saved(self):
        self.lesson.lesson_status = LessonStatus.SAVED
        self.lesson.save()
        self.lesson2.lesson_status = LessonStatus.SAVED
        self.lesson2.save()
        self.lesson3.lesson_status = LessonStatus.SAVED
        self.lesson3.save()

    def get_dict_from_list(self,list_dict,lesson):
        for each_dict in list_dict:
            if lesson in each_dict.keys():
                return each_dict

    def check_lesson_in_returned_dictionary(self,lesson_dictionary,expected_lesson):
        for lesson in lesson_dictionary:
            if lesson == expected_lesson and lesson.lesson_id == expected_lesson.lesson_id:
                return True

        return False

    def check_all_unfulfilled_lessons(self,list_of_dictionaries):
        self.assertTrue(self.check_lesson_in_returned_dictionary(self.get_dict_from_list(list_of_dictionaries,self.lesson),self.lesson))
        self.assertTrue(self.check_lesson_in_returned_dictionary(self.get_dict_from_list(list_of_dictionaries,self.lesson2),self.lesson2))
        self.assertTrue(self.check_lesson_in_returned_dictionary(self.get_dict_from_list(list_of_dictionaries,self.lesson3),self.lesson3))
        self.assertTrue(self.check_lesson_in_returned_dictionary(self.get_dict_from_list(list_of_dictionaries,self.lesson4),self.lesson4))
        self.assertTrue(self.check_lesson_in_returned_dictionary(self.get_dict_from_list(list_of_dictionaries,self.lesson5),self.lesson5))


    def check_unfulfilled_dictionary_equality(self,dictionary, student_id,request_number, lesson_date_without_time_string, type_string, lesson_duration_string, teacher_name):
        self.assertEqual(dictionary['Student'] , student_id)
        self.assertEqual(dictionary['Lesson Request'] , request_number)
        self.assertEqual(dictionary['Lesson Date'] , lesson_date_without_time_string)
        self.assertEqual(dictionary['Lesson'] , type_string)
        self.assertEqual(dictionary['Lesson Duration'] , lesson_duration_string)
        self.assertEqual(dictionary['Teacher'] , teacher_name)

    def check_fulfilled_dictionary_equality(self,dictionary,student_id, type_string, lesson_date_without_time_string, lesson_duration_string, teacher_name):
        self.assertEqual(dictionary['Student'] , student_id)
        self.assertEqual(dictionary['Lesson'] , type_string)
        self.assertEqual(dictionary['Lesson Date'] , lesson_date_without_time_string)
        self.assertEqual(dictionary['Lesson Duration'] , lesson_duration_string)
        self.assertEqual(dictionary['Teacher'] , teacher_name)

    def test_dictionary_format_for_unfulfilled_lessons(self):
        self.change_lessons_status_to_unfulfilled()

        unfullfilled_lessons = make_lesson_dictionary(self.student, "Lesson Request")

        request_date_str = self.lesson.request_date.strftime("%Y-%m-%d")
        self.assertEqual(len(unfullfilled_lessons[request_date_str]),5)

        #print(lesson_dict[self.lesson])
        self.check_unfulfilled_dictionary_equality(self.get_dict_from_list(unfullfilled_lessons[request_date_str],self.lesson)[self.lesson],self.student,'1',"2022-11-20", "INSTRUMENT", "30 minutes", "Barbare Dutch")
        self.check_unfulfilled_dictionary_equality(self.get_dict_from_list(unfullfilled_lessons[request_date_str],self.lesson2)[self.lesson2],self.student,'2',"2022-10-20", "THEORY", "45 minutes", "Barbare Dutch")
        self.check_unfulfilled_dictionary_equality(self.get_dict_from_list(unfullfilled_lessons[request_date_str],self.lesson3)[self.lesson3],self.student,'3',"2022-09-20", "PERFORMANCE", "60 minutes", "Amane Hill")
        self.check_unfulfilled_dictionary_equality(self.get_dict_from_list(unfullfilled_lessons[request_date_str],self.lesson4)[self.lesson4],self.student,'4',"2022-12-25", "PRACTICE", "45 minutes", "Amane Hill")
        self.check_unfulfilled_dictionary_equality(self.get_dict_from_list(unfullfilled_lessons[request_date_str],self.lesson5)[self.lesson5],self.student,'5',"2022-09-25", "PRACTICE", "45 minutes", "Jonathan Jacks")

    def test_dictionary_format_for_fullfilled_lessons(self):
        lesson_dict = make_lesson_timetable_dictionary(self.student)

        #print(lesson_dict)
        self.assertEqual(len(lesson_dict),5)
        #print(lesson_dict[self.lesson])
        self.check_fulfilled_dictionary_equality(lesson_dict[self.lesson], self.student,LessonType.INSTRUMENT.label, "2022-11-20", "15:15 - 15:45", "Miss Barbare Dutch")
        self.check_fulfilled_dictionary_equality(lesson_dict[self.lesson2], self.student,LessonType.THEORY.label, "2022-10-20", "16:00 - 16:45", "Miss Barbare Dutch")
        self.check_fulfilled_dictionary_equality(lesson_dict[self.lesson3], self.student,LessonType.PERFORMANCE.label, "2022-09-20", "09:45 - 10:45", "Mr Amane Hill")
        self.check_fulfilled_dictionary_equality(lesson_dict[self.lesson4], self.student,LessonType.PRACTICE.label, "2022-12-25", "09:45 - 10:30", "Mr Amane Hill")
        self.check_fulfilled_dictionary_equality(lesson_dict[self.lesson5], self.student,LessonType.PRACTICE.label, "2022-09-25", "09:45 - 10:30", "Jonathan Jacks")

    def test_student_feed_url(self):
        self.assertEqual(self.url,'/student_feed/')

    def test_get_student_feed_with_booked_lessons(self):
        self.initialise_admin()
        self.client.login(email=self.student.email, password="Password123")

        response = self.client.get(self.url,follow = True)
        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']
        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        self.assertEqual(len(fullfilled_lessons),5)
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson2))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson3))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson4))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson5))
        self.assertEqual(greeting_str, 'Welcome back John Doe, this is your feed!')
        self.assertEqual(len(unfullfilled_lessons),0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_student_feed_with_some_pending_and_saved_lessons(self):
        self.initialise_admin()
        self.change_lessons_status_to_unfulfilled()
        self.changes_some_lessons_status_to_saved()
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.url, follow = True)

        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']

        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        request_date_str = self.lesson.request_date.strftime("%Y-%m-%d")
        self.assertEqual(len(unfullfilled_lessons[request_date_str]),2)
        self.assertEqual(len(fullfilled_lessons), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_get_student_feed_with_pending_lessons(self):
        self.initialise_admin()
        self.change_lessons_status_to_unfulfilled()
        self.client.login(email=self.student.email, password="Password123")

        response = self.client.get(self.url, follow = True)

        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']

        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        request_date_str = self.lesson.request_date.strftime("%Y-%m-%d")
        self.assertEqual(len(unfullfilled_lessons[request_date_str]),5)
        self.check_all_unfulfilled_lessons(unfullfilled_lessons[request_date_str])
        self.assertEqual(greeting_str, f'Welcome back {self.student}, this is your feed!')
        self.assertEqual(len(fullfilled_lessons),0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_get_student_feed_with_booked_and_requested_lessons(self):
        self.initialise_admin()
        self.change_some_lessons_to_unfulfilled()
        self.client.login(email=self.student.email, password="Password123")

        response = self.client.get(self.url,follow = True)
        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']
        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        self.assertEqual(greeting_str, 'Welcome back John Doe, this is your feed!')
        self.assertEqual(len(fullfilled_lessons),3)
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson3))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson4))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson5))

        request_date_str = self.lesson.request_date.strftime("%Y-%m-%d")
        self.assertEqual(len(unfullfilled_lessons[request_date_str]),2)
        self.assertTrue(self.check_lesson_in_returned_dictionary(unfullfilled_lessons[request_date_str][0],self.lesson))
        self.assertTrue(self.check_lesson_in_returned_dictionary(unfullfilled_lessons[request_date_str][1],self.lesson2))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_get_student_feed_with_pending_lessons_without_an_admin(self):
        self.change_lessons_status_to_unfulfilled()
        self.client.login(email=self.student.email, password="Password123")
        admin = UserAccount.objects.get(email='bobby@example.org').delete()
        response = self.client.get(self.url, follow = True)

        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']

        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, 'No Admins Available To Contact')
        request_date_str = self.lesson.request_date.strftime("%Y-%m-%d")
        self.assertEqual(len(unfullfilled_lessons[request_date_str]),5)
        self.check_all_unfulfilled_lessons(unfullfilled_lessons[request_date_str])
        self.assertEqual(greeting_str, f'Welcome back {self.student}, this is your feed!')
        self.assertEqual(len(fullfilled_lessons),0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_get_booked_lessons_with_student_and_child(self):
        self.initialise_admin()
        self.create_child_student_with_lessons()
        self.client.login(email=self.student.email, password="Password123")

        response = self.client.get(self.url,follow = True)
        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']
        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        self.assertEqual(len(fullfilled_lessons),5)
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson2))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson3))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson4))
        self.assertTrue(self.check_lesson_in_returned_dictionary(fullfilled_lessons,self.lesson5))

        self.assertEqual(fullfilled_lessons[self.lesson]['Student'].__str__(), f'{self.child}')
        self.assertEqual(fullfilled_lessons[self.lesson2]['Student'].__str__(), f'{self.child}')
        self.assertEqual(fullfilled_lessons[self.lesson3]['Student'].__str__(), f'{self.child}')
        self.assertEqual(fullfilled_lessons[self.lesson4]['Student'].__str__(), f'{self.student}')
        self.assertEqual(fullfilled_lessons[self.lesson5]['Student'].__str__(), f'{self.student}')

        self.assertEqual(greeting_str, 'Welcome back John Doe, this is your feed!')
        self.assertEqual(len(unfullfilled_lessons),0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_get_pending_lessons_with_different_requests_dates(self):
        self.create_child_with_different_request_dates()
        self.initialise_admin()
        self.client.login(email=self.student.email, password="Password123")

        response = self.client.get(self.url,follow = True)
        unfullfilled_lessons = response.context['unfulfilled_requests']
        fullfilled_lessons = response.context['fullfilled_lessons']
        greeting_str = response.context['greeting']
        admin_email = response.context['admin_email']

        self.assertEqual(admin_email, f'To Further Edit Bookings Contact {self.admin.email}')
        self.assertEqual(len(fullfilled_lessons),0)

        request_date_str_first = self.lesson.request_date.strftime("%Y-%m-%d")
        request_date_str_second = self.lesson3.request_date.strftime("%Y-%m-%d")


        self.assertTrue(request_date_str_first in unfullfilled_lessons.keys())
        self.assertTrue(request_date_str_second in unfullfilled_lessons.keys())


        self.assertEqual(len(unfullfilled_lessons[request_date_str_first]),3)
        self.assertEqual(len(unfullfilled_lessons[request_date_str_second]),2)



        self.check_lesson_in_returned_dictionary(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson5),self.lesson5)
        self.assertEqual(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson5)[self.lesson5]['Student'].__str__(), f'{self.student}')

        self.check_lesson_in_returned_dictionary(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson),self.lesson)
        self.assertEqual(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson)[self.lesson]['Student'].__str__(), f'{self.child}')

        self.check_lesson_in_returned_dictionary(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson2),self.lesson2)
        self.assertEqual(self.get_dict_from_list(unfullfilled_lessons[request_date_str_first],self.lesson2)[self.lesson2]['Student'].__str__(), f'{self.child}')

        self.check_lesson_in_returned_dictionary(self.get_dict_from_list(unfullfilled_lessons[request_date_str_second],self.lesson4),self.lesson4)
        self.assertEqual(self.get_dict_from_list(unfullfilled_lessons[request_date_str_second],self.lesson4)[self.lesson4]['Student'].__str__(), f'{self.student}')

        self.check_lesson_in_returned_dictionary(self.get_dict_from_list(unfullfilled_lessons[request_date_str_second],self.lesson3),self.lesson3)
        self.assertEqual(self.get_dict_from_list(unfullfilled_lessons[request_date_str_second],self.lesson3)[self.lesson3]['Student'].__str__(), f'{self.child}')

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'student_feed.html')

    def test_post_student_feed_forbidden(self):
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.post(self.url, follow = True)
        self.assertEqual(response.status_code, 403)

    def test_get_student_feed_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url,follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

    def test_not_student_accessing_student_feed(self):
        self.initialise_admin()
        self.client.login(email=self.admin.email, password="Password123")
        response = self.client.get(self.url, follow = True)
        redirect_url = reverse('admin_feed')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')
