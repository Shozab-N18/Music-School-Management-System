from django.test import TestCase
from django.urls import reverse
from lessons.models import Term
from lessons.models import UserAccount,Gender
from django.contrib import messages

import datetime

class TermManagementTestCases(TestCase):
    """Tests for the director_manage_roles view."""

    def setUp(self):


        self.admin = UserAccount.objects.create_admin(
                first_name='Petra',
                last_name='Pickles',
                email= 'petra.pickles@example.org',
                password='Password123',
                gender = Gender.FEMALE,
            )


        self.url = reverse('term_management')



        self.term1 = Term.objects.create(
            term_number=1,
            start_date = datetime.date(2022, 9,1),
            end_date = datetime.date(2022, 10,21),
        )

        self.term2 = Term.objects.create(
            term_number=2,
            start_date = datetime.date(2022, 10,31),
            end_date = datetime.date(2022, 12,16),
        )

        self.term4 = Term.objects.create(
            term_number=4,
            start_date = datetime.date(2023, 2,20),
            end_date = datetime.date(2023, 3,31),
        )

        self.term5 = Term.objects.create(
            term_number=5,
            start_date = datetime.date(2023, 4,17),
            end_date = datetime.date(2023, 5,26),
        )

        self.form_input = {
            'term_number' : 3,
            'start_date' : datetime.date(2023, 1,3),
            'end_date' : datetime.date(2023, 2,10),
        }

        self.form_input_with_already_existing_term_number = {
            'term_number' : 1,
            'start_date' : datetime.date(2023, 1,3),
            'end_date' : datetime.date(2023, 2,10),
        }

        self.form_input_with_dates_overlapping = {
            'term_number' : 3,
            'start_date' : datetime.date(2023, 3,3),
            'end_date' : datetime.date(2023, 2,10),
        }

        self.form_input_with_dates_overlap_with_another_term = {
            'term_number' : 3,
            'start_date' : datetime.date(2022, 10,25),
            'end_date' : datetime.date(2022, 11,1),
        }

        self.form_input_with_dates_overlapping2 = {
            'term_number' : 5,
            'start_date' : datetime.date(2023, 3,3),
            'end_date' : datetime.date(2023, 2,10),
        }

    def test_term_management_page_url(self):
        self.assertEqual(self.url,'/term_management')

    # Test terms deletion works as required
    def test_delete_term(self):

        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.delete_term_url = reverse('delete_term', args=[self.term5.term_number])
        response = self.client.get(self.delete_term_url, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before-1,term_count_after)

        self.assertEqual(len(Term.objects.filter(term_number=self.term5.term_number)),0)

        redirect_url = reverse('term_management')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'term_management.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_cant_delete_non_existing_term(self):

        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.delete_term_url = reverse('delete_term', args=['6'])
        response = self.client.get(self.delete_term_url, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before,term_count_after)

        redirect_url = reverse('term_management')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'term_management.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

     # Test term creation works as required

    def test_successful_create_term(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.create_term_url = reverse('create_term')
        response = self.client.post(self.create_term_url,self.form_input, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before+1,term_count_after)

        self.assertEqual(len(Term.objects.filter(term_number=self.form_input['term_number'])),1)

        redirect_url = reverse('term_management')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'term_management.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_unsuccessful_create_term_due_to_unique_term_number_constraint(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.create_term_url = reverse('create_term')
        response = self.client.post(self.create_term_url,self.form_input_with_already_existing_term_number, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before,term_count_after)

        # should be one because there already exists a term with this number
        self.assertEqual(len(Term.objects.filter(term_number=self.form_input_with_already_existing_term_number['term_number'])),1)

        self.assertTemplateUsed(response, 'create_term_form.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_unsuccessful_create_term_due_to_dates_overlapping_with_each_other(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.create_term_url = reverse('create_term')
        response = self.client.post(self.create_term_url,self.form_input_with_dates_overlapping, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before,term_count_after)

        self.assertEqual(len(Term.objects.filter(term_number=self.form_input_with_dates_overlapping['term_number'])),0)

        self.assertTemplateUsed(response, 'create_term_form.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    def test_unsuccessful_create_term_due_to_dates_overlapping_with_another(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.create_term_url = reverse('create_term')
        response = self.client.post(self.create_term_url,self.form_input_with_dates_overlap_with_another_term, follow = True)
        term_count_after = Term.objects.count()
        self.assertEqual(term_count_before,term_count_after)

        self.assertEqual(len(Term.objects.filter(term_number=self.form_input_with_dates_overlap_with_another_term['term_number'])),0)

        self.assertTemplateUsed(response, 'create_term_form.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)

    #Test term editing works as required
    def test_successfully_edit_term(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.update_term_url = reverse('update_term_details', args=[self.term5.term_number])

        response = self.client.post(self.update_term_url,self.form_input, follow = True)
        term_count_after = Term.objects.count()

        self.assertEqual(term_count_before,term_count_after)
        updated_term = Term.objects.get(term_number=self.form_input['term_number'])

        self.assertEqual(len(Term.objects.filter(term_number=self.form_input['term_number'])),1)

        self.assertEqual(updated_term.term_number, self.form_input.get('term_number'))
        self.assertEqual(updated_term.start_date, self.form_input.get('start_date'))
        self.assertEqual(updated_term.end_date, self.form_input.get('end_date'))

        redirect_url = reverse('term_management')
        self.assertRedirects(response, redirect_url, status_code=302, target_status_code=200)
        self.assertTemplateUsed(response, 'term_management.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.SUCCESS)

    def test_unsuccessfully_edit_term(self):
        self.client.login(email=self.admin.email, password="Password123")

        term_count_before = Term.objects.count()
        self.update_term_url = reverse('update_term_details', args=[self.term5.term_number])

        response = self.client.post(self.update_term_url,self.form_input_with_dates_overlapping2, follow = True)
        term_count_after = Term.objects.count()

        self.assertEqual(term_count_before,term_count_after)
        updated_term = Term.objects.get(term_number=self.form_input_with_dates_overlapping2['term_number'])

        self.assertEqual(updated_term.term_number, self.form_input_with_dates_overlapping2.get('term_number'))
        self.assertNotEqual(updated_term.start_date, self.form_input_with_dates_overlapping2.get('start_date'))
        self.assertNotEqual(updated_term.end_date, self.form_input_with_dates_overlapping2.get('end_date'))

        self.assertTemplateUsed(response, 'edit_term_form.html')

        messages_list = list(response.context['messages'])
        self.assertEqual(messages_list[0].level, messages.ERROR)
