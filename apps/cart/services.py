from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from apps.product.models import Product 

def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user = user)
    return cart

def add_to_cart(user, product_id, quantity):
    cart = get_or_create_cart(user)
    product = get_object_or_404(Product, id=product_id)
    item, created_at = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created_at:
        item.quantity += quantity
        item.save()
    else:
        item.quantity = quantity
        item.save()
    return item