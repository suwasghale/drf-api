from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.discounts.models import Discount
from apps.discounts.models_user_usage import DiscountRedemption

class DiscountValidationError(Exception):
    pass

class DiscountService:
    """
    Service layer that encapsulates coupon validation & application logic.
    """

    @staticmethod
    def get_discount_by_code(code: str) -> Discount:
        try:
            return Discount.objects.get(code__iexact=code)
        except Discount.DoesNotExist:
            raise DiscountValidationError("Invalid discount code")
