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

    @staticmethod
    def validate_for_order(discount: Discount, order_total: Decimal, user=None):
        now = timezone.now()
        if not discount.is_within_validity(now):
            raise DiscountValidationError("This discount is not active or expired.")
        if discount.min_order_value and order_total < discount.min_order_value:
            raise DiscountValidationError(f"Order must be at least {discount.min_order_value} to use this coupon.")
        if discount.usage_limit is not None and discount.used_count >= discount.usage_limit:
            raise DiscountValidationError("This discount has reached its usage limit.")
        if user and discount.per_user_limit is not None:
            user_uses = DiscountRedemption.objects.filter(discount=discount, user=user).count()
            if user_uses >= discount.per_user_limit:
                raise DiscountValidationError("You have already used this coupon the maximum number of times.")

        return True

