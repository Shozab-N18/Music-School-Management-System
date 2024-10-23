from django.test import TestCase
from lessons.tests.helpers import LogInTester, reverse_with_next
from django.urls import reverse
from lessons.views import promote_admin, promote_director
from lessons.models import UserAccount,UserRole
from django.contrib import messages


class DirectorRoleChangesTestCase(TestCase):
    """Tests for the director_manage_roles view."""

    fixtures = ['lessons/tests/fixtures/useraccounts.json']

    def setUp(self):
        self.url = reverse('director_manage_roles')

        # This is the current user we log in with to access the page
        self.current = UserAccount.objects.create_superuser(
            first_name='Ahmed',
            last_name='Pedro',
            email='apedro@example.org',
            password='Password123',
            gender = 'M',
        )

        self.admin = UserAccount.objects.get(email='janedoe@example.org')
        self.director = UserAccount.objects.get(email='jsmith@example.org')

    def test_change_role_page_url(self):
        self.assertEqual(self.url,'/director_manage_roles/')


    def test_get_director_role_page_redirects_when_not_logged_in(self):
        redirect_url = reverse_with_next('home', self.url)
        response = self.client.get(self.url,follow = True)
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'home.html')


    # tests assigning and unsigning super-admin privileges to a regular admin account

    def test_promote_admin_to_director(self):

        self.client.login(email=self.current.email, password="Password123")

        # Change an admin into a director
        self.promote_director_url = reverse('promote_director', args=[self.admin.email])
        director_count_before = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        response = self.client.get(self.promote_director_url, follow = True)
        director_count_after = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        self.assertEqual(director_count_before+1,director_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    def test_cant_promote_non_existant_user_to_director(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try promote a user that does not exist
        user_count_before = UserAccount.objects.count()
        self.promote_director_url = reverse('promote_director', args=["unknownemail@example.org"])
        response = self.client.get(self.promote_director_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)


    def test_demote_director_to_admin(self):

        self.client.login(email=self.current.email, password="Password123")

        # Change a director into admin
        self.promote_admin_url = reverse('promote_admin', args=[self.director.email])
        director_count_before = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        response = self.client.get(self.promote_admin_url, follow = True)
        director_count_after = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        self.assertEqual(director_count_before-1,director_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    def test_cant_demote_current_director_to_admin(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try change currently logged in director into an admin
        self.promote_admin_url = reverse('promote_admin', args=[self.current.email])
        director_count_before = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        response = self.client.get(self.promote_admin_url, follow = True)
        director_count_after = UserAccount.objects.filter(role = UserRole.DIRECTOR).count()
        self.assertEqual(director_count_before,director_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)


    def test_cant_demote_non_existant_user_to_admin(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try to demote a non existent director into admin
        user_count_before = UserAccount.objects.count()
        self.promote_admin_url = reverse('promote_admin', args=["unknownemail@example.org"])
        response = self.client.get(self.promote_admin_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)


    # Test the actions that can be done on every director/admin

    def test_disable_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Disable an admin account
        active_user_count_before = UserAccount.objects.filter(is_active = True).count()
        self.disable_user_url = reverse('disable_user', args=[self.admin.email])
        response = self.client.get(self.disable_user_url, follow = True)
        active_user_count_after = UserAccount.objects.filter(is_active = True).count()
        self.assertEqual(active_user_count_before-1,active_user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    def test_cant_disable_current_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try to disable current director account
        active_user_count_before = UserAccount.objects.filter(is_active = True).count()
        self.disable_user_url = reverse('disable_user', args=[self.current.email])
        response = self.client.get(self.disable_user_url, follow = True)
        active_user_count_after = UserAccount.objects.filter(is_active = True).count()
        self.assertEqual(active_user_count_before,active_user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_cant_disable_non_existant_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try to disable a user that does not exist
        user_count_before = UserAccount.objects.count()
        self.disable_user_url = reverse('disable_user', args=["unknownemail@example.org"])
        response = self.client.get(self.disable_user_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)


    def test_delete_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Delete an admin account
        user_count_before = UserAccount.objects.count()
        self.delete_user_url = reverse('delete_user', args=[self.admin.email])
        response = self.client.get(self.delete_user_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before-1,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)


    def test_cant_delete_current_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try to delete the current director account
        user_count_before = UserAccount.objects.count()
        self.delete_user_url = reverse('delete_user', args=[self.current.email])
        response = self.client.get(self.delete_user_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_cant_delete_non_existant_user(self):

        self.client.login(email=self.current.email, password="Password123")

        # Try to delete an account that does not exist
        user_count_before = UserAccount.objects.count()
        self.delete_user_url = reverse('delete_user', args=["unknownemail@example.org"])
        response = self.client.get(self.delete_user_url, follow = True)
        user_count_after = UserAccount.objects.count()
        self.assertEqual(user_count_before,user_count_after)

        redirect_url = reverse('director_manage_roles')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'director_manage_roles.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)
