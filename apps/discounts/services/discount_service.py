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


    @staticmethod
    def apply_discount_to_order(discount: Discount, order, user=None):
        """
        Applies discount to given order – this function expects `order` to have:
            - total_price or total (Decimal)
            - a place to store discount amount (we return computed details, do NOT mutate order here)
        Returns a tuple (discount_amount, final_total)
        If you want to persist usage & redemptions, call `commit_redemption`.
        """
        order_total = Decimal(getattr(order, "total_price", getattr(order, "total", 0)))
        discount_amount = discount.calculate_discount_amount(order_total)
        final_total = (order_total - discount_amount).quantize(Decimal("0.01"))
        return discount_amount, final_total

    @staticmethod
    @transaction.atomic
    def commit_redemption(discount: Discount, user, order, applied_amount: Decimal):
        """
        Record the redemption and increment global usage atomically.
        Use select_for_update on discount to avoid race conditions.
        """
        # Lock discount row
        discount = Discount.objects.select_for_update().get(pk=discount.pk)

        # Double-check limits
        if discount.usage_limit is not None and discount.used_count >= discount.usage_limit:
            raise DiscountValidationError("This discount has reached its usage limit (concurrent).")

        # If per-user limit exists, check it
        if discount.per_user_limit is not None:
            user_uses = DiscountRedemption.objects.filter(discount=discount, user=user).count()
            if user_uses >= discount.per_user_limit:
                raise DiscountValidationError("User per-coupon limit reached.")

        # Create redemption record
        redemption = DiscountRedemption.objects.create(
            discount=discount,
            user=user,
            order=order,
            amount=applied_amount,
        )

        # increment used_count
        discount.used_count = discount.used_count + 1
        discount.save(update_fields=["used_count"])

        return redemption