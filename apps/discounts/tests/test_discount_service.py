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


