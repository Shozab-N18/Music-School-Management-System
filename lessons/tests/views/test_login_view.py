
from django.contrib.auth.hashers import check_password
from django.test import TestCase
from lessons.tests.helpers import LogInTester, reverse_with_next
from django.urls import reverse
from django.contrib import messages
from lessons.forms import LogInForm
from lessons.models import UserAccount, Gender

class LogInTestCase(TestCase,LogInTester):
    """Tests for the login up view."""
    
    def setUp(self):
        self.url = reverse('home')
        self.student = UserAccount.objects.create_student(
            first_name='John',
            last_name='Doe',
            email='johndoe@example.org',
            password='Password123',
            gender = 'M',
        )
        self.admin = UserAccount.objects.create_admin(
            first_name='Jane',
            last_name='Doe',
            email='janedoe@example.org',
            password='Password123',
            gender = 'F',
        )

        self.director = UserAccount.objects.create_superuser(
            first_name='Jack',
            last_name='Smith',
            email='jsmith@example.org',
            password='Password123',
            gender = 'M',
        )

        self.student_form_input = {'email' : 'johndoe@example.org', 'password' : 'Password123'}
        self.admin_form_input = {'email' : 'janedoe@example.org', 'password' : 'Password123'}
        self.director_form_input = {'email' : 'jsmith@example.org', 'password' : 'Password123'}

    def create_child_student(self):
        self.child = UserAccount.objects.create_child_student(
            first_name = 'Bobby',
            last_name = 'Lee',
            email = 'bobbylee@example.org',
            password = 'Password123',
            gender = Gender.MALE,
            parent_of_user = self.student,
        )

        self.child_form_input = {'email' : 'bobbylee@example.org', 'password' : 'Password123'}

    def test_log_in_url(self):
        self.assertEqual(self.url,'/')

    def test_get_log_in(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        next = response.context['next']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(next)


    def test_get_log_in_with_redirect(self):
        destination_url = reverse('student_feed')
        self.url = reverse_with_next('home', destination_url)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        next = response.context['next']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertTrue(next)
        self.assertEqual(next, destination_url)


    # test logged in users redirect to log in page login for roles
    def test_get_log_in_with_redirect_when_logged_in_student(self):
        self.client.login(username = self.student.email, password="Password123")
        response = self.client.get(self.url,follow=True)
        response_url = reverse('student_feed')
        self.assertRedirects(response,response_url,302,target_status_code = 200)
        self.assertTemplateUsed(response,'student_feed.html')

    def test_get_log_in_with_redirect_when_logged_in_student(self):
        self.client.login(username = self.admin.email, password="Password123")
        response = self.client.get(self.url,follow=True)
        response_url = reverse('admin_feed')
        self.assertRedirects(response,response_url,302,target_status_code = 200)
        self.assertTemplateUsed(response,'admin_feed.html')

    def test_get_log_in_with_redirect_when_logged_in_student(self):
        self.client.login(username = self.director.email, password="Password123")
        response = self.client.get(self.url,follow=True)
        response_url = reverse('director_feed')
        self.assertRedirects(response,response_url,302,target_status_code = 200)
        self.assertTemplateUsed(response,'director_feed.html')

    # These tests check if user is redirected to the correct feed based on their roles
    def test_successful_student_login(self):
        response = self.client.post(self.url, self.student_form_input,follow=True)
        self.assertTrue(self._is_logged_in())
        response_url = reverse('student_feed')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)

    def test_successful_student_login_with_redirect(self):
        self.student = UserAccount.objects.create_student(
            first_name='John',
            last_name='Do',
            email='johndo@example.org',
            password='Password123',
            gender = 'M',
        )
        redirect_url = reverse('student_feed')
        form_input = { 'email' : 'johndo@example.org', 'password': 'Password123', 'next' : redirect_url}
        response = self.client.post(self.url, form_input,follow=True)
        self.assertTrue(self._is_logged_in())
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)


    def test_successful_admin_login(self):
        response = self.client.post(self.url, self.admin_form_input,follow=True)
        self.assertTrue(self._is_logged_in())
        response_url = reverse('admin_feed')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'admin_feed.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)

    def test_successful_director_login(self):
        response = self.client.post(self.url, self.director_form_input,follow=True)
        self.assertTrue(self._is_logged_in())
        response_url = reverse('director_feed')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_feed.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)


    # test unsucessful login for roles
    def test_unsucessful_student_log_in(self):
        self.student_form_input = {'email' : 'WrongEmail', 'password' : 'WrongPass'}
        response = self.client.post(self.url, self.student_form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        self.assertEqual(messages_list[0].level,messages.ERROR)


    def test_unsucessful_admin_log_in(self):
        self.admin_form_input = {'email' : 'WrongEmail', 'password' : 'WrongPass'}
        response = self.client.post(self.url, self.admin_form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        self.assertEqual(messages_list[0].level,messages.ERROR)


    def test_unsucessful_director_log_in(self):
        self.director_form_input = {'email' : 'WrongEmail', 'password' : 'WrongPass'}
        response = self.client.post(self.url, self.director_form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        self.assertEqual(messages_list[0].level,messages.ERROR)

    def test_child_log_in_is_invalid(self):
        self.create_child_student()
        response = self.client.post(self.url,self.child_form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        self.assertEqual(messages_list[0].level,messages.ERROR)
        self.assertEqual(str(messages_list[0]), 'Child credentials cannot be used to access the application')

    def test_succesful_log_in_after_child_log_in_is_invalid(self):
        self.create_child_student()
        response = self.client.post(self.url,self.child_form_input)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'home.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, LogInForm))
        self.assertFalse(form.is_bound)
        self.assertFalse(self._is_logged_in())
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        self.assertEqual(messages_list[0].level,messages.ERROR)
        self.assertEqual(str(messages_list[0]), 'Child credentials cannot be used to access the application')

        destination_url = reverse('student_feed')
        self.url = reverse_with_next('home', destination_url)
        response_after = self.client.get(self.url)
        self.assertEqual(response_after.status_code,200)
        self.assertTemplateUsed(response_after,'home.html')
        form = response_after.context['form']
        next = response_after.context['next']
        self.assertTrue(isinstance(form,LogInForm))
        self.assertFalse(form.is_bound)
        self.assertEqual(next, destination_url)
        messages_list = list(response_after.context['messages'])
        self.assertEqual(len(messages_list),0)


    #test that invalid users can not log into system
    def test_invalid_log_in_by_inactive_user(self):
        self.student.is_active = False
        self.student.save()
        response = self.client.post(self.url, self.student_form_input, follow = True)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,'home.html')
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),1)
        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level,messages.ERROR)

    #test if we can get login view with a redirect parameter
    def test_get_log_in_with_redirect_student(self):
        destination_url = reverse('student_feed')
        self.url = reverse_with_next('home', destination_url)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code,200)
        self.assertTemplateUsed(response,'home.html')
        form = response.context['form']
        next = response.context['next']
        self.assertTrue(isinstance(form,LogInForm))
        self.assertFalse(form.is_bound)
        self.assertEqual(next, destination_url)
        messages_list = list(response.context['messages'])
        self.assertEqual(len(messages_list),0)
