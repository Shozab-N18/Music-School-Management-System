from django.contrib.auth.hashers import check_password
from django.test import TestCase
from django.urls import reverse
from lessons.forms import SignUpForm
from lessons.models import UserAccount, Gender

class SignUpViewTestCase(TestCase):
    """Tests of the sign up view."""

    def setUp(self):
        self.url = reverse('sign_up')

        self.form_input = {
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'janedoe@example.org',
            'gender': Gender.FEMALE,
            'new_password': 'Password123',
            'password_confirmation': 'Password123'
        }

    def test_sign_up_url(self):
        self.assertEqual(self.url,'/sign_up/')

    def test_get_sign_up(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertFalse(form.is_bound)

    def test_unsuccesful_sign_up(self):
        self.form_input['email'] = 'BAD_EMAIL.COM'
        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'sign_up.html')
        form = response.context['form']
        self.assertTrue(isinstance(form, SignUpForm))
        self.assertTrue(form.is_bound)
        #After we have LogInTester defined, uncomment
        #self.assertFalse(self._is_logged_in())


    def test_succesful_sign_up(self):
        before_count = UserAccount.objects.count()
        response = self.client.post(self.url, self.form_input, follow=True)
        after_count = UserAccount.objects.count()
        self.assertEqual(after_count, before_count+1)
        response_url = reverse('student_feed')
        self.assertRedirects(response, response_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'student_feed.html')

        student = UserAccount.objects.get(email ='janedoe@example.org')
        self.assertEqual(student.first_name, 'Jane')
        self.assertEqual(student.last_name, 'Doe')
        self.assertEqual(student.gender, Gender.FEMALE.value)
        self.assertEqual(student.email, 'janedoe@example.org')
        is_password_correct = check_password('Password123', student.password)
        self.assertTrue(is_password_correct)
        #After we have LogInTester defined, uncomment
        #self.assertTrue(self._is_logged_in())
