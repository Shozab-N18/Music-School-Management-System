from django import forms
from lessons.forms import TermDatesForm
from django.test import TestCase
import datetime


class TermFormTestCase(TestCase):
    """Unit tests of the sign up form."""

    def setUp(self):
        self.form_input = {
            'term_number':2,
            'start_date':datetime.date(2022, 9,1),
            'end_date':datetime.date(2022, 10,21),
        }


    def test_valid_request_form(self):
        form = TermDatesForm(data = self.form_input)
        self.assertTrue(form.is_valid())

    def test_form_has_necessary_fields(self):
        form = TermDatesForm()
        self.assertIn('term_number', form.fields)
        self.assertIn('start_date', form.fields)
        self.assertIn('end_date', form.fields)
        start_date = form.fields['start_date']
        end_date = form.fields['end_date']
        self.assertTrue(isinstance(start_date, forms.DateField))
        self.assertTrue(isinstance(end_date, forms.DateField))
