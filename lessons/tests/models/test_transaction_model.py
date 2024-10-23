from django.core.exceptions import ValidationError
from django.test import TestCase
from lessons.models import Transaction

class TransactionModelTesctCase(TestCase):

    # this test test all fields in transaction model
    # tested model: Transaction

    def setUp(self):
        self.transaction = Transaction.objects.create(
            Student_ID_transaction = '1111',
            transaction_amount = '77'
        )

    def _create_sencond_transaction(self):
        second_transaction = Transaction.objects.create(
            Student_ID_transaction = '1331',
            invoice_reference_transaction = '1331-001',


        )
        return second_transaction

    def _assert_transaction_is_valid(self):
        try:
            self.transaction.full_clean()
        except(ValidationError):
            self.fail('Test invoice should be valid')

    def _assert_transaction_is_invalid(self):
        with self.assertRaises(ValidationError):
            self.transaction.full_clean()


    def test_valid_transaction(self):
        self._assert_transaction_is_valid()


    def test_Student_ID_transaction_be_blank(self):
        self.transaction.Student_ID_transaction = ''
        self._assert_transaction_is_invalid()

    def test_Student_ID_transaction_can_be_30_characters_long(self):
        self.transaction.Student_ID_transaction = '4' * 30
        self._assert_transaction_is_valid()

    def test_Student_ID_transaction_cannot_be_over_30_characters_long(self):
        self.transaction.Student_ID_transaction = '4' * 31
        self._assert_transaction_is_invalid()

    def test_Student_ID_transaction_must_not_be_unique(self):
        second_transaction = self._create_sencond_transaction()
        self.transaction.Student_ID_transaction = second_transaction.Student_ID_transaction
        self._assert_transaction_is_valid()

    def test_Student_ID_transaction_must_only_contain_number(self):
        self.transaction.Student_ID_transaction = '45s'
        self._assert_transaction_is_invalid()


    def test_reference_number_can_be_blank(self):
        self.transaction.invoice_reference_transaction = ''
        self._assert_transaction_is_valid()

    def test_reference_number_can_be_30_characters_long(self):
        self.transaction.invoice_reference_transaction = '4' *14 + '-' + '5'*15
        self._assert_transaction_is_valid()

    def test_reference_number_cannot_be_over_30_characters_long(self):
        self.transaction.invoice_reference_transaction = '4' *14 + '-' + '5'*16
        self._assert_transaction_is_invalid()

    def test_reference_number_must_not_be_unique(self):
        second_transaction = self._create_sencond_transaction()
        self.transaction.invoice_reference_transaction = second_transaction.invoice_reference_transaction
        self._assert_transaction_is_valid()

    def test_reference_number_must_contain_hyphen_symbol_in_between(self):
        self.transaction.invoice_reference_transaction = '333344444'
        self._assert_transaction_is_invalid()

    def test_reference_number_must_contain_at_least_one_number_before_hyphen(self):
        self.transaction.invoice_reference_transaction = '-333344444'
        self._assert_transaction_is_invalid()

    def test_reference_number_must_contain_at_least_three_numbers_after_hyphen(self):
        self.transaction.invoice_reference_transaction = '3333-44'
        self._assert_transaction_is_invalid()

    def test_reference_number_must_contain_only_number_and_hyphen(self):
        self.transaction.invoice_reference_transaction = '33a-444'
        self._assert_transaction_is_invalid()


    def test_transaction_amount_cannot_be_blank(self):
        self.transaction.transaction_amount = ''
        self._assert_transaction_is_invalid()

    def test_default_value_of_transaction_amount_is_1(self):
        second_transaction = self._create_sencond_transaction()
        self.assertEqual(second_transaction.transaction_amount, 1)

    def test_value_of_transaction_amount_can_be_10000(self):
        self.transaction.transaction_amount = 10000
        self._assert_transaction_is_valid()

    def test_value_of_transaction_amount_can_be_1(self):
        self.transaction.transaction_amount = 1
        self._assert_transaction_is_valid()

    def test_value_of_transaction_amount_cannot_be_larger_than_10000(self):
        self.transaction.transaction_amount = 10001
        self._assert_transaction_is_invalid()

    def test_value_of_transaction_amount_cannot_be_smaller_than_1(self):
        self.transaction.transaction_amount = 0
        self._assert_transaction_is_invalid()

    def test_value_of_transaction_amount_must_not_be_unique(self):
        second_transaction = self._create_sencond_transaction()
        self.transaction.transaction_amount = second_transaction.transaction_amount
        self._assert_transaction_is_valid()

    def test_value_of_transaction_amount_must_only_contain_number(self):
        self.transaction.transaction_amount = '45s'
        self._assert_transaction_is_invalid()
