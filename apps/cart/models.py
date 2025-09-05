from django.db import models
from django.conf import settings
from apps.product.models import Product 

USER = settings.AUTH_USER_MODEL
# Create your models
class Cart(models.Model):
    user = models.OneToOneField(USER, on_delete=models.CASCADE, related_name='cart')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Cart of {self.user.username}"
    
    @property 
    def total_price(self):
        """
        How it works: The total_price method in the Cart model is decorated with @property. This means you can access the total price of the cart like a simple attribute (my_cart.total_price) instead of calling it as a method (my_cart.total_price()).
        Benefits: This calculation is performed dynamically whenever the total_price attribute is accessed. This avoids having to store and constantly update a total_price field in the database, which would be an expensive operation every time an item is added, removed, or has its quantity changed.
        """
        total = sum(item.subtotal for item in self.items.all())
        return total
    
# The relationship between Cart and CartItem:
"""
NOTE: Cart has a related_name='items' on its reverse relationship from CartItem. This makes it easy to access all of a cart's items from the Cart object using the attribute my_cart.items.all().
Each CartItem is linked back to a specific Cart. This structure is efficient for managing the items within each user's cart.
"""

# cart items
class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        """
        NOTE: How it works: The unique_together = ("cart", "product") line tells Django to enforce that no two CartItem objects can exist with the same cart and product combination.
        Benefits: This is a crucial data integrity measure for a shopping cart. It prevents a user from adding the same product to their cart twice as separate line items. Instead, the logic would need to update the quantity of the existing CartItem for that product. This is more efficient and avoids confusion.
        """
        unique_together = ("cart", "product")

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def subtotal(self):
        """
        How it works: It multiplies the price of the related Product (self.product.price) by the quantity of the item (self.quantity) to get the subtotal for that specific line item.
        Benefits: This value is always computed on the fly. You don't need to save the subtotal in the database, reducing redundancy and ensuring consistency if the product's price changes.
        """
        return self.product.price * self.quantity