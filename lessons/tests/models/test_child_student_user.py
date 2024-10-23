#tests for child student UserRole
from django.core.exceptions import ValidationError
from django.test import TestCase
from lessons.models import UserAccount,UserRole, Gender

from lessons.modelHelpers import is_valid_gender,is_valid_role

class TestChildStudentUser(TestCase):
    """Unit Tests for child student UserAccounts of the application"""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']
    def setUp(self):

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.child = UserAccount.objects.get(email='bobbylee@example.org')

        self.admin = UserAccount.objects.get(email='bobby@example.org')

    def _assert_student_is_valid(self):
        try:
            self.student.full_clean()
        except(ValidationError):
            self.fail('Test user should be valid')

    def _assert_child_student_is_valid(self):
        try:
            self.child.full_clean()
        except(ValidationError):
            self.fail('Test user should be valid')

    def _assert_child_student_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.child.full_clean()

    def _create_second_student(self):
        student = UserAccount.objects.get(email='janedoe@example.org')
        return student

    def test_child_first_name_must_not_be_blank(self):
        self.child.first_name = ''
        self._assert_child_student_is_invalid()

    def test_child_first_name_need_not_be_unique(self):
        second_student = self._create_second_student()
        self.child.first_name = second_student.first_name
        self._assert_child_student_is_valid()

    def test_child_first_name_may_contain_50_characters(self):
        self.child.first_name = 'x' * 50
        self._assert_child_student_is_valid()

    def test_child_first_name_must_not_contain_more_than_50_characters(self):
        self.child.first_name = 'x' * 51
        self._assert_child_student_is_invalid()

    #tests for student last name
    def test_child_last_name_must_not_be_blank(self):
        self.child.last_name = ''
        self._assert_child_student_is_invalid()

    def test_child_last_name_need_not_be_unique(self):
        second_student = self._create_second_student()
        self.child.last_name = second_student.last_name
        self._assert_child_student_is_valid()

    def test_child_last_name_may_contain_50_characters(self):
        self.child.last_name = 'x' * 50
        self._assert_child_student_is_valid()

    def test_child_last_name_must_not_contain_more_than_50_characters(self):
        self.child.last_name = 'x' * 51
        self._assert_child_student_is_invalid()

    #tests for student email
    def test_child_email_must_not_be_blank(self):
        self.child.email = ''
        self._assert_child_student_is_invalid()

    def test_child_email_must_be_unique(self):
        second_student = self._create_second_student()
        self.child.email = second_student.email
        self._assert_child_student_is_invalid()

    def test_child_email_must_contain_at_symbol(self):
        self.child.email = 'johndoe.example.org'
        self._assert_child_student_is_invalid()

    def test_child_email_must_contain_domain_name(self):
        self.child.email = 'johndoe@.org'
        self._assert_child_student_is_invalid()

    def test_child_email_must_contain_domain(self):
        self.child.email = 'johndoe@example'
        self._assert_child_student_is_invalid()

    def test_child_email_must_not_contain_more_than_one_at(self):
        self.child.email = 'johndoe@@example.org'
        self._assert_child_student_is_invalid()

    def test_child_student_gender_string_must_be_valid(self):
        self.child.gender = 'NOTVALIDGENDER'
        self.assertFalse(is_valid_gender(self.child))
        self._assert_child_student_is_invalid()

    def test_child_student_role_string_must_be_valid(self):
        self.child.role = 'NonUserAccount'
        self.assertFalse(is_valid_role(self.child))
        self._assert_child_student_is_invalid()

    def test_child_student_is_not_staff(self):
        self.assertFalse(self.child.is_staff)

    def test_child_student_is_student(self):
        self.assertEqual(self.child.role, UserRole.STUDENT)
        self._assert_child_student_is_valid()

    def test_child_student_is_not_student(self):
        self.child.role = UserRole.ADMIN
        self.assertNotEqual(self.child.role, UserRole.STUDENT)

    def test_child_user_is_valid(self):
        self._assert_child_student_is_valid()
        self._assert_student_is_valid()

        self.assertEqual(self.child.role,UserRole.STUDENT)
        self.assertFalse(self.child.is_parent)
        self.assertNotEqual(self.child.parent_of_user,None)
        parent_of_child = self.child.parent_of_user

        self.assertEqual(parent_of_child,self.student)
        self.assertEqual(parent_of_child.email,self.student.email)
        self.assertTrue(parent_of_child.is_parent)
        self.assertEqual(self.student.parent_of_user,None)

    def test_parent_must_be_a_useraccountobject(self):
        with self.assertRaises(AttributeError):
            self.newChild = UserAccount.objects.create_child_student(
                first_name = 'Bobby',
                last_name = 'Lee',
                email = 'bobbylee@example.org',
                password = 'Password123',
                gender = Gender.MALE,
                parent_of_user = 'PARENT',
                )

    def test_parent_must_be_a_student(self):
        with self.assertRaises(AttributeError):
            self.newChild = UserAccount.objects.create_child_student(
                first_name = 'Bobby',
                last_name = 'Lee',
                email = 'bobbylee@example.org',
                password = 'Password123',
                gender = Gender.MALE,
                parent_of_user = self.admin,
                )

    def test_deletion_of_parent_deletes_child(self):
        UserAccount.objects.get(email = self.student.email).delete()
        self.assertEqual(UserAccount.objects.count(),6)
