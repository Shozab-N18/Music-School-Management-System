from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from lessons.forms import SignUpForm
from lessons.models import UserAccount, Gender, UserRole
from django.contrib import messages

class SignUpChildViewTestCase(TestCase):
    """Tests of the sign up view for a child."""
    fixtures = ['lessons/tests/fixtures/useraccounts.json']

    def setUp(self):
        self.url = reverse('sign_up_child')

        self.admin = UserAccount.objects.get(email='bobby@example.org')

        self.student = UserAccount.objects.get(email='johndoe@example.org')

        self.form_input = {
            'first_name': 'Bobby',
            'last_name': 'Lee',
            'email': 'bobbylee@example.org',
            'gender': Gender.MALE,
            'new_password': 'Password123',
            'password_confirmation': 'Password123'
        }

    def test_sign_up_url(self):
        self.assertEqual(self.url,'/sign_up_child/')

    def test_get_sign_up_not_logged_in(self):
        redirect_url = reverse('home')
        before_count = UserAccount.objects.count()
        response = self.client.get(self.url,follow = True)
        after_count = UserAccount.objects.count()
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')
        self.assertEqual(after_count, before_count)

    def test_get_sign_up_not_logged_in(self):
        redirect_url = reverse('admin_feed')
        self.client.login(email=self.admin.email, password="Password123")
        before_count = UserAccount.objects.count()
        response = self.client.get(self.url,follow = True)
        after_count = UserAccount.objects.count()
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')
        self.assertEqual(after_count, before_count)

    def test_get_sign_up(self):
        self.client.login(email=self.student.email, password="Password123")
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up_child.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_unsuccesful_sign_up_of_child_user_incorrect_email(self):
        self.client.login(email=self.student.email, password="Password123")
        self.form_input['email'] = 'BAD_EMAIL.COM'
        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up_child.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_unsuccesful_sign_up_of_child_user_no_name(self):
        self.client.login(email=self.student.email, password="Password123")
        self.form_input['first_name'] = ''
        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up_child.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_succesful_sign_up_child_user(self):
        self.client.login(email=self.student.email, password="Password123")
        UserAccount.objects.get(email='bobbylee@example.org').delete()
        before_count = UserAccount.objects.count()

        response = self.client.post(self.url, self.form_input, follow=True)

        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count+1)
        response_url = reverse('student_feed')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        child_student = UserAccount.objects.get(email ='bobbylee@example.org')
        self.assertEqual(child_student.first_name, 'Bobby')
        self.assertEqual(child_student.last_name, 'Lee')
        self.assertEqual(child_student.gender, Gender.MALE.value)
        self.assertEqual(child_student.email, 'bobbylee@example.org')
        is_password_correct = check_password('Password123', child_student.password)
        self.assertTrue(is_password_correct)

        self.assertEqual(child_student.role,UserRole.STUDENT)
        self.assertFalse(child_student.is_parent)
        self.assertNotEqual(child_student.parent_of_user,None)
        parent_of_child = child_student.parent_of_user

        self.assertEqual(parent_of_child.first_name, self.student.first_name)
        self.assertEqual(parent_of_child.last_name, self.student.last_name)
        self.assertEqual(parent_of_child.gender, self.student.gender)
        is_password_correct = check_password('Password123', parent_of_child.password)
        self.assertTrue(is_password_correct)

        self.assertEqual(self.student.role,UserRole.STUDENT)
        self.assertEqual(parent_of_child.email,self.student.email)
        self.assertTrue(parent_of_child.is_parent)
        self.assertEqual(self.student.parent_of_user,None)

    def test_unsuccessfull_sign_up_of_child_user_copy(self):
        self.client.login(email=self.student.email, password="Password123")
        before_count = UserAccount.objects.count()

        response = self.client.post(self.url, self.form_input, follow=True)

        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up_child.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(str(messages_list[0]), 'These account details already exist for another child')
        self.assertEqual(messages_list[0].level, messages.ERROR)
