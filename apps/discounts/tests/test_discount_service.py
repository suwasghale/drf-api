from decimal import Decimal
from django.test import TestCase
from django.contrib.auth import get_user_model
from apps.discounts.models import Discount
from apps.discounts.services.discount_service import DiscountService, DiscountValidationError

User = get_user_model()

class DiscountServiceTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="u", password="p")
        self.discount = Discount.objects.create(
            code="TEST10",
            discount_type=Discount.DISCOUNT_PERCENTAGE,
            amount=10,
            is_active=True
        )

    def test_calculate_percentage_discount(self):
        discount_amount, final_total = DiscountService.apply_discount_to_order(self.discount, type("O", (), {"total_price": Decimal("100.00")}))
        self.assertEqual(discount_amount, Decimal("10.00"))
        self.assertEqual(final_total, Decimal("90.00"))

    def test_validate_invalid_code(self):
        with self.assertRaises(DiscountValidationError):
            DiscountService.get_discount_by_code("NOPE")
