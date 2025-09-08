from django.db import transaction 
from apps.orders.models import Order, OrderItem
from apps.cart.models import CartItem
from apps.cart.services import get_or_create_cart

@transaction.atomic 
def create_order_from_cart(user):
    cart = get_or_create_cart(user)
    cart_items = CartItem.objects.filter(cart = cart)
    if not cart_items.exists():
        raise ValueError("Cart is empty")
    
    order = Order.objects.create(user = user, status = 'pending')
    total = 0 

    for item in cart_items:
        line_total = item.product.price * item.quantity
        total += line_total 
        OrderItem.objects.create(
            order = order,
            product = item.product,
            quantity = item.quantity,
            price = item.product.price
        )
    order.total_price = total 
    order.save()

    # clear the cart after creating the order
    cart.items.all().delete()

    return order