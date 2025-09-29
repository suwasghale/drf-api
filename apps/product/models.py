from django.db import models
from rest_framework.permissions import AllowAny
from django.utils.text import slugify

# Create your models here.
# category
class Category(models.Model):
    """
    Represents a product category (e.g., Laptops, Headphones, Mobiles).
    Supports nested categories using self-referencing 'parent'.
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, 
        related_name="children", null=True, blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name}"


# product 
class Product(models.Model):
    """
    Core product model representing a single sellable item.
    """
    sku = models.CharField(max_length=100, unique=True, null=True, blank=True)
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products")

    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField(blank=True)
    
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.PositiveIntegerField(default=0)

    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    brand = models.CharField(max_length=100, blank=True, null=True)
    warranty = models.CharField(max_length=255, blank=True, null=True)
    free_shipping = models.BooleanField(default=True)

    image = models.ImageField(upload_to='products/', blank=True, null=True)
    gallery = models.JSONField(default=list, blank=True)  # for multiple images

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name