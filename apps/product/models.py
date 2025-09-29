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
class Product (models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField(default=0)
    image = models.FileField(upload_to='uploads/', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)    
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name