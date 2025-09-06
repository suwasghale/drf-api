from django.shortcuts import get_object_or_404
from .models import Cart, CartItem
from apps.product.models import Product 
from django.db import transaction

def get_or_create_cart(user):
    cart, _ = Cart.objects.get_or_create(user = user)
    return cart

@transaction.atomic # NOTE: 
def add_to_cart(user, product_id, quantity=1):
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

def remove_from_cart(user, product_id):
    cart = get_or_create_cart(user)
    CartItem.objects.filter(cart = cart, product_id = product_id).delete()

def clear_cart(user):
    cart = get_or_create_cart(user)
    cart.items.all().delete()