"""Tests for the profile view."""
from django.contrib import messages
from django.test import TestCase
from django.urls import reverse
from lessons.forms import CreateAdminForm
from lessons.models import UserAccount
from lessons.tests.helpers import reverse_with_next
from django.contrib.auth.hashers import check_password

class DirectorUpdateUserTest(TestCase):
    """Unit tests of the update_user view."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']

    def setUp(self):

        self.current = UserAccount.objects.create_superuser(
            first_name='Ahmed',
            last_name='Pedro',
            email='apedro@example.org',
            password='Password123',
            gender = 'M',
        )

        self.admin = UserAccount.objects.get(email='janedoe@example.org')

        self.url = reverse('create_admin_page')

        self.form_input = {
            'first_name': 'Jane2',
            'last_name': 'Doe2',
            'email': 'thenewjanedoe@example.org',
            'gender': 'M',
            'new_password': 'NewPassword123',
            'password_confirmation': 'NewPassword123',
        }

    def test_create_admin_page_url(self):
        self.assertEqual(self.url,'/create_admin_page')

    def test_get_create_admin_page_when_not_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url,follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')


    def test_succesful_user_update(self):

        self.client.login(email=self.current.email, password="Password123")

        # Update an admin account with new details
        user_count_before = UserAccount.objects.count()
        self.update_user_url = reverse('update_user', args=[self.admin.id])
        response = self.client.post(self.update_user_url,self.form_input ,follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        # After sucessful change
        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

        # Ensures user fields on database has changed
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Jane2')
        self.assertEqual(self.admin.last_name, 'Doe2')
        self.assertEqual(self.admin.email, 'thenewjanedoe@example.org')
        self.assertEqual(self.admin.gender, 'M')
        is_password_correct = check_password('NewPassword123', self.admin.password)
        self.assertTrue(is_password_correct)


    def test_succesful_current_user_update_(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try update the current director account with new details
        user_count_before = UserAccount.objects.count()
        self.update_user_url = reverse('update_user', args=[self.current.id])
        response = self.client.post(self.update_user_url,self.form_input ,follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        # Check current user is logged out
        response_url = reverse('home')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')

        # Ensures user fields on database has changed
        self.current.refresh_from_db()
        self.assertEqual(self.current.first_name, 'Jane2')
        self.assertEqual(self.current.last_name, 'Doe2')
        self.assertEqual(self.current.email, 'thenewjanedoe@example.org')
        self.assertEqual(self.current.gender, 'M')
        is_password_correct = check_password('NewPassword123', self.current.password)
        self.assertTrue(is_password_correct)


    def test_unsuccesful_user_update(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try update the an admin account with new details
        user_count_before = UserAccount.objects.count()
        self.update_user_url = reverse('update_user', args=[self.admin.id])
        self.form_input['email'] = 'BAD_EMAIL'
        response = self.client.post(self.update_user_url,self.form_input ,follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        # Ensures user fields on database has not changed
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Jane')
        self.assertEqual(self.admin.last_name, 'Doe')
        self.assertEqual(self.admin.email, 'janedoe@example.org')
        self.assertEqual(self.admin.gender, 'F')
        is_password_correct = check_password('Password123', self.admin.password)
        self.assertTrue(is_password_correct)


    def test_unsuccesful_current_user_update_due_to_used_email(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try update the an admin account with an already used emails
        user_count_before = UserAccount.objects.count()
        self.update_user_url = reverse('update_user', args=[self.admin.id])
        self.form_input['email'] = 'apedro@example.org'
        response = self.client.post(self.update_user_url,self.form_input ,follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        # Ensures user fields on database has not changed
        self.admin.refresh_from_db()
        self.assertEqual(self.admin.first_name, 'Jane')
        self.assertEqual(self.admin.last_name, 'Doe')
        self.assertEqual(self.admin.email, 'janedoe@example.org')
        self.assertEqual(self.admin.gender, 'F')
        is_password_correct = check_password('Password123', self.admin.password)
        self.assertTrue(is_password_correct)
