from unittest import TestCase

from ua_banktools.core import IPN
from ua_banktools.core.ipn import IPNValidationError


class IPNTests(TestCase):
    CODE = "3123456789"

    def test_equal_to_same_code_as_ipn_or_string(self):
        self.assertEqual(IPN(self.CODE), IPN(self.CODE))
        self.assertEqual(IPN(self.CODE), self.CODE)
        self.assertEqual(self.CODE, IPN(self.CODE))

    def test_not_equal_to_ints_or_unrelated_objects(self):
        # An int comparison would drop leading zeros, so it is deliberately absent.
        self.assertNotEqual(IPN(self.CODE), int(self.CODE))
        self.assertNotEqual(IPN(self.CODE), None)
        self.assertNotIn(IPN(self.CODE), [1, None, "other"])

    def test_hash_agrees_with_equality(self):
        self.assertEqual(len({IPN(self.CODE), IPN(self.CODE), self.CODE}), 1)

    def test_validation_error_is_a_value_error(self):
        # So pydantic validators surface it as a ValidationError.
        with self.assertRaises(ValueError):
            IPN("0123456789")
        self.assertTrue(issubclass(IPNValidationError, ValueError))
