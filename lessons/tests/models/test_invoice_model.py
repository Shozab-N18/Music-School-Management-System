"""Unit tests for the Invoice model"""
from django.core.exceptions import ValidationError
from django.test import TestCase
from lessons.models import Invoice, InvoiceStatus, LessonDuration

class InvoiceModelTestCase(TestCase):

    fixtures = ['lessons/tests/fixtures/invoices.json']
    def setUp(self):
        self.invoice = Invoice.objects.get(reference_number='111-001')

    def _create_paid_invoice(self):
        invoice = Invoice.objects.create(
            reference_number = '222-012',
            student_ID = '222',
            fees_amount = '85',
            lesson_ID = '4567',
            invoice_status = InvoiceStatus.PAID,
            
        )
        return invoice

    def _assert_invoice_is_valid(self):
        try:
            self.invoice.full_clean()
        except(ValidationError):
            self.fail('Test invoice should be valid')

    def _assert_invoice_is_invalid(self):      
        with self.assertRaises(ValidationError):
            self.invoice.full_clean()


    def test_valid_invoice(self):
        self._assert_invoice_is_valid()


    def test_reference_number_cannot_be_blank(self):
        self.invoice.reference_number = ''
        self._assert_invoice_is_invalid()

    def test_reference_number_can_be_30_characters_long(self):
        self.invoice.reference_number = '4' *14 + '-' + '5'*15
        self._assert_invoice_is_valid()

    def test_reference_number_cannot_be_over_30_characters_long(self):
        self.invoice.reference_number = '4' *14 + '-' + '5'*16
        self._assert_invoice_is_invalid()

    def test_reference_number_must_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.reference_number = second_invoice.reference_number
        self._assert_invoice_is_invalid()

    def test_reference_number_must_contain_hyphen_symbol_in_between(self):
        self.invoice.reference_number = '333344444'
        self._assert_invoice_is_invalid()

    def test_reference_number_must_contain_at_least_one_number_before_hyphen(self):
        self.invoice.reference_number = '-333344444'
        self._assert_invoice_is_invalid()

    def test_reference_number_must_contain_at_least_three_numbers_after_hyphen(self):
        self.invoice.reference_number = '3333-44'
        self._assert_invoice_is_invalid()

    def test_reference_number_must_contain_only_number_and_hyphen(self):
        self.invoice.reference_number = '33a-444'
        self._assert_invoice_is_invalid()


    def test_student_id_cannot_be_blank(self):
        self.invoice.student_ID = ''
        self._assert_invoice_is_invalid()

    def test_student_id_can_be_30_characters_long(self):
        self.invoice.student_ID = '4' * 30 
        self._assert_invoice_is_valid()

    def test_student_id_cannot_be_over_30_characters_long(self):
        self.invoice.student_ID = '4' * 31
        self._assert_invoice_is_invalid()

    def test_student_id_must_not_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.student_ID = second_invoice.student_ID
        self._assert_invoice_is_valid()

    def test_student_id_must_only_contain_number(self):
        self.invoice.student_ID = '45s'
        self._assert_invoice_is_invalid()


    def test_fees_amount_cannot_be_blank(self):
        self.invoice.fees_amount = ''
        self._assert_invoice_is_invalid()

    def test_fees_amount_cannot_be_larger_than_10000(self):
        self.invoice.fees_amount = 10001
        self._assert_invoice_is_invalid()

    def test_fees_amount_can_be_10000(self):
        self.invoice.fees_amount = 10000
        self._assert_invoice_is_valid()
    
    def test_fees_amount_can_be_1(self):
        self.invoice.fees_amount = 1
        self._assert_invoice_is_valid()

    def test_fees_amount_cannot_be_smaller_than_1(self):
        self.invoice.fees_amount = -1
        self._assert_invoice_is_invalid()

    def test_fees_amount_must_not_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.fees_amount = second_invoice.fees_amount
        self._assert_invoice_is_valid()

    def test_fees_amount_must_only_contain_number(self):
        self.invoice.fees_amount = '45s'
        self._assert_invoice_is_invalid()

    
    def test_invoice_status_cannot_be_blank(self):
        self.invoice.invoice_status = ''
        self._assert_invoice_is_invalid()

    def test_invoice_status_value_can_only_be_one_of_the_choices_PAID(self):
        self.invoice.invoice_status = 'PAID'
        self._assert_invoice_is_valid()
    
    def test_invoice_status_value_can_only_be_one_of_the_choices_UNPAID(self):
        self.invoice.invoice_status = 'UNPAID'
        self._assert_invoice_is_valid()

    def test_invoice_status_value_can_only_be_one_of_the_choices_PARTIALLY_PAID(self):
        self.invoice.invoice_status = 'PARTIALLY_PAID'
        self._assert_invoice_is_valid()

    def test_invoice_status_value_can_only_be_one_of_the_choices_PARTIALLY_PAID(self):
        self.invoice.invoice_status = 'DELETED'
        self._assert_invoice_is_valid()

    def test_invoice_status_value_can_only_be_one_of_the_choices_wrong_choice(self):
        self.invoice.invoice_status = 'DAWD'
        self._assert_invoice_is_invalid()

    def test_invoice_status_must_not_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.invoice_status = second_invoice.invoice_status
        self._assert_invoice_is_valid()

    def test_fees_amount_cannot_be_any_other_values_outside_choices(self):
        self.invoice.invoice_status = '45s'
        self._assert_invoice_is_invalid()


    def test_amounts_need_to_pay_cannot_be_blank(self):
        self.invoice.amounts_need_to_pay = ''
        self._assert_invoice_is_invalid()

    def test_default_value_of_amounts_need_to_pay_is_0(self):
        self.assertEqual(self.invoice.amounts_need_to_pay, 0)

    def test_value_of_amounts_need_to_pay_can_be_10000(self):
        self.invoice.amounts_need_to_pay = 10000
        self._assert_invoice_is_valid()

    def test_value_of_amounts_need_to_pay_can_be_0(self):
        self.invoice.amounts_need_to_pay = 0
        self._assert_invoice_is_valid()

    def test_value_of_amounts_need_to_pay_cannot_be_larger_than_10000(self):
        self.invoice.amounts_need_to_pay = 10001
        self._assert_invoice_is_invalid()

    def test_value_of_amounts_need_to_pay_cannot_be_smaller_than_0(self):
        self.invoice.amounts_need_to_pay = -1
        self._assert_invoice_is_invalid()

    def test_value_of_amounts_need_to_pay_must_not_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.amounts_need_to_pay = second_invoice.amounts_need_to_pay
        self._assert_invoice_is_valid()

    def test_value_of_amounts_need_to_pay_must_only_contain_number(self):
        self.invoice.amounts_need_to_pay = '45s'
        self._assert_invoice_is_invalid()


    def test_lesson_ID_can_be_blank(self):
        self.invoice.lesson_ID = ''
        self._assert_invoice_is_valid()

    def test_lesson_ID_can_be_30_characters_long(self):
        self.invoice.lesson_ID = '4' * 30 
        self._assert_invoice_is_valid()

    def test_lesson_ID_cannot_be_over_30_characters_long(self):
        self.invoice.lesson_ID = '4' * 31
        self._assert_invoice_is_invalid()

    def test_lesson_ID_must_not_be_unique(self):
        second_invoice = self._create_paid_invoice()
        self.invoice.lesson_ID = second_invoice.lesson_ID
        self._assert_invoice_is_valid()

    def test_lesson_ID_must_only_contain_number(self):
        self.invoice.lesson_ID = '45s'
        self._assert_invoice_is_invalid()


    def test_generate_reference_number_function_gives_correct_return_1(self):
        temp_refer = Invoice.generate_new_invoice_reference_number('111', 0)
        self.assertEqual(temp_refer, '111-001')

    def test_generate_reference_number_function_gives_correct_return_2(self):
        temp_refer = Invoice.generate_new_invoice_reference_number('111', 10)
        self.assertEqual(temp_refer, '111-011')

    def test_generate_reference_number_function_gives_correct_return_3(self):
        temp_refer = Invoice.generate_new_invoice_reference_number('111', 99)
        self.assertEqual(temp_refer, '111-100')

    
    def test_fees_amount_calculator_gives_correct_return_Thirty(self):
        temp_fees = Invoice.calculate_fees_amount(LessonDuration.THIRTY) 
        self.assertEqual(temp_fees, '15')

    def test_fees_amount_calculator_gives_correct_return_Fourty_Five(self):
        temp_fees = Invoice.calculate_fees_amount(LessonDuration.FOURTY_FIVE) 
        self.assertEqual(temp_fees, '18')

    def test_fees_amount_calculator_gives_correct_return_1_hour(self):
        temp_fees = Invoice.calculate_fees_amount(LessonDuration.HOUR)
        self.assertEqual(temp_fees, '20')



