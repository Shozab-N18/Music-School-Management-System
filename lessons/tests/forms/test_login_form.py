
from django import forms
from django.test import TestCase
from lessons.forms import LogInForm
from lessons.models import UserAccount

class LogInFormTestCase(TestCase):
    """Unit tests for the login form."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']
    def setUp(self):
        self.form_input = {'email' : 'johndoe@example.org', 'password' : 'Password123'}
        self.student = UserAccount.objects.get(email = 'johndoe@example.org')

    def test_form_contains_required_fields(self):
        form = LogInForm()
        self.assertIn('email', form.fields)
        self.assertIn('password', form.fields)
        password_field = form.fields['password']
        self.assertTrue(isinstance(password_field.widget,forms.PasswordInput))

    def test_form_accepts_valid_input(self):
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_rejects_blank_email_input(self):
        self.form_input['email'] = ''
        form = LogInForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_rejects_blank_password_input(self):
        self.form_input['password'] = ''
        form = LogInForm(data=self.form_input)
        self.assertFalse(form.is_valid())

    def test_form_accepts_incorrect_email(self):
        self.form_input['email'] = 'johndoe'
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_accepts_incorrect_password(self):
        self.form_input['password'] = 'i'
        form = LogInForm(data=self.form_input)
        self.assertTrue(form.is_valid())
