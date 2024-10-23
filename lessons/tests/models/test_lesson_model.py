from django.core.exceptions import ValidationError
from django.test import TestCase
from lessons.models import UserAccount, Lesson, Gender, LessonType,LessonDuration,LessonStatus
from lessons.modelHelpers import is_valid_lessonStatus,is_valid_lessonDuration,is_valid_lessonType
from django.db import IntegrityError
import datetime
from django.utils import timezone

class LessonModelTestCase(TestCase):
    """Unit Tests for Lesson model"""

    fixtures = ['lessons/tests/fixtures/useraccounts.json'], ['lessons/tests/fixtures/lessons.json']
    def setUp(self):

        self.teacher = UserAccount.objects.get(email='barbdutch@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.second_student = UserAccount.objects.get(email='janedoe@example.org')

        self.child = UserAccount.objects.get(email='bobbylee@example.org')

        self.lesson = Lesson.objects.get(lesson_id = 1)
        self.lesson.lesson_status = LessonStatus.FULLFILLED
        self.lesson.save()

        self.lesson2 = Lesson.objects.get(lesson_id = 2)
        self.lesson2.lesson_status = LessonStatus.FULLFILLED
        self.lesson2.save()

        self.lesson3 = Lesson.objects.get(lesson_id = 3)
        self.lesson3.lesson_status = LessonStatus.FULLFILLED
        self.lesson3.teacher_id = self.teacher
        self.lesson3.save()

        self.lesson4 = Lesson.objects.get(lesson_id = 4)
        self.lesson4.lesson_status = LessonStatus.FULLFILLED
        self.lesson4.student_id = self.second_student
        self.lesson4.teacher_id = self.teacher
        self.lesson4.save()

        Lesson.objects.get(lesson_id = 5).delete()

    def create_child_lessons(self):
        self.booked_child_lesson = Lesson.objects.create(
            type = LessonType.PRACTICE,
            duration = LessonDuration.HOUR,
            lesson_date_time = datetime.datetime(2022, 11, 22, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.child,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED
        )

        self.booked_child_lesson2 = Lesson.objects.create(
            type = LessonType.THEORY,
            duration = LessonDuration.FOURTY_FIVE,
            lesson_date_time = datetime.datetime(2022, 7, 25, 20, 8, 7, tzinfo=timezone.utc),
            teacher_id = self.teacher,
            student_id = self.child,
            request_date = datetime.date(2022, 10, 15),
            lesson_status = LessonStatus.FULLFILLED
        )

    def _assert_lesson_is_valid(self,lesson):
        try:
            lesson.full_clean()
        except(ValidationError):
            self.fail('Test user should be valid')

    def _assert_lesson_is_invalid(self,lesson):
        with self.assertRaises(ValidationError):
            lesson.full_clean()

    def test_violate_primary_key_unique_constraint(self):
        with self.assertRaises(IntegrityError):
            self.lessonCopy = Lesson.objects.create(
                type = LessonType.INSTRUMENT,
                duration = LessonDuration.THIRTY,
                lesson_date_time = datetime.datetime(2022, 11, 20, 15, 15, 0, tzinfo=timezone.utc),
                teacher_id = self.teacher,
                student_id = self.student,
                request_date = datetime.date(2022, 10, 15),
                )

    def _all_lessons_are_valid(self):
        self._assert_lesson_is_valid(self.lesson)
        self._assert_lesson_is_valid(self.lesson2)
        self._assert_lesson_is_valid(self.lesson3)

    def test_all_lessons_are_valid(self):
        self._all_lessons_are_valid()

    def test_lesson_dates_are_different(self):
        self.assertNotEqual(self.lesson.lesson_date_time, self.lesson2.lesson_date_time)
        self.assertNotEqual(self.lesson.lesson_date_time, self.lesson3.lesson_date_time)
        self.assertNotEqual(self.lesson2.lesson_date_time, self.lesson3.lesson_date_time)
        self._all_lessons_are_valid()

    def test_all_lesson_types_are_valid(self):
        self.assertTrue(is_valid_lessonType(self.lesson))
        self.assertTrue(is_valid_lessonType(self.lesson2))
        self.assertTrue(is_valid_lessonType(self.lesson3))

        self._all_lessons_are_valid()

    def test_all_lesson_durations_are_valid(self):
        self.assertTrue(is_valid_lessonDuration(self.lesson))
        self.assertTrue(is_valid_lessonDuration(self.lesson2))
        self.assertTrue(is_valid_lessonDuration(self.lesson3))

        self._all_lessons_are_valid()

    def test_lesson_type_is_invalid(self):
        self.lesson.type = 'NONlessonType'
        self.assertFalse(is_valid_lessonType(self.lesson))
        self._assert_lesson_is_invalid(self.lesson)

    def test_lesson_duration_is_invalid(self):
        self.lesson.duration = 'randomDuration'
        self.assertFalse(is_valid_lessonDuration(self.lesson))
        self._assert_lesson_is_invalid(self.lesson)

    def test_lesson2_type_is_invalid(self):
        self.lesson2.type = 'NONlessonType2'
        self.assertFalse(is_valid_lessonType(self.lesson2))
        self._assert_lesson_is_invalid(self.lesson2)

    def test_lesson2_duration_is_invalid(self):
        self.lesson2.duration = 'randomDuration2'
        self.assertFalse(is_valid_lessonDuration(self.lesson2))
        self._assert_lesson_is_invalid(self.lesson2)

    def test_all_lessons_request_date_is_equal(self):
        self.assertEqual(self.lesson.request_date, self.lesson2.request_date)
        self.assertEqual(self.lesson.request_date, self.lesson3.request_date)
        self.assertEqual(self.lesson2.request_date, self.lesson3.request_date)

    def test_all_lesson_status_is_valid(self):
        self.assertTrue(is_valid_lessonStatus(self.lesson))
        self.assertTrue(is_valid_lessonStatus(self.lesson2))
        self.assertTrue(is_valid_lessonStatus(self.lesson3))

    def test_student_deletion_deletes_all_related_lessons(self):
        before_count = Lesson.objects.count()
        UserAccount.objects.get(email = self.student.email).delete()
        after_count = Lesson.objects.count()
        self.assertEqual(before_count-3,after_count)
        self.assertEqual(after_count,1)

        before_second_count = Lesson.objects.count()
        UserAccount.objects.get(email = self.second_student.email).delete()
        after_second_count = Lesson.objects.count()
        self.assertEqual(before_second_count-1,after_second_count)
        self.assertEqual(after_second_count,0)

    def test_delete_child_deletes_all_related_lessons(self):
        self.create_child_lessons()
        before_count = Lesson.objects.count()
        UserAccount.objects.get(email = self.child.email).delete()
        after_count = Lesson.objects.count()
        self.assertEqual(before_count-2,after_count)
        self.assertEqual(after_count,4)

    def test_student_deletion_deletes_child_and_all_student_and_child_lessons(self):
        self.create_child_lessons()
        before_count = Lesson.objects.count()
        UserAccount.objects.get(email = self.student.email).delete()
        self.assertEqual(UserAccount.objects.count(),6) #second student and teacher

        after_count = Lesson.objects.count()
        self.assertEqual(before_count-5,after_count)
        self.assertEqual(after_count,1)

    def test_teacher_deletion_deletes_all_related_lessons(self):
        self.create_child_lessons()
        before_count = Lesson.objects.count()
        UserAccount.objects.get(email = self.teacher.email).delete()
        after_count = Lesson.objects.count()
        self.assertEqual(before_count-6,after_count)
        self.assertEqual(after_count,0)
