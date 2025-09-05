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
        total = sum(item.subtotal for item in self.items.all())
        return total