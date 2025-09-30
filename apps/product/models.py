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
    Represents a single product in the store.
    Includes SKU, name, pricing, stock, media, warranty, etc.
    """

    # 🏷️ Identification
    sku = models.CharField(max_length=100, unique=True)  # e.g., MU12146
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)

    # 🧠 Core Info
    description = models.TextField(blank=True)
    brand = models.CharField(max_length=100)
    category = models.ForeignKey(
        "Category",
        on_delete=models.CASCADE,
        related_name="products"
    )

    # 💰 Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    old_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.PositiveIntegerField(default=0)

    # 📦 Inventory & Availability
    stock = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)

    # 🛡️ Warranty & Shipping
    warranty = models.CharField(max_length=255, null=True, blank=True)
    free_shipping = models.BooleanField(default=True)
    expected_delivery = models.CharField(max_length=255, default="2-3 working days")

    # 🖼️ Media
    thumbnail = models.ImageField(upload_to="products/thumbnails/", blank=True, null=True)
    images = models.JSONField(default=list, blank=True)  # e.g. ["img1.jpg", "img2.jpg"]

    # 🕒 Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

     # ⚙️ Options
    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["sku", "slug"]),
            models.Index(fields=["category", "is_available"]),
        ]

    def save(self, *args, **kwargs):
        """Automatically generate slug if missing."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.sku})"


    # 🧮 Dynamic Calculations
    @property
    def discount_amount(self):
        """Calculate discount value dynamically."""
        if self.old_price and self.old_price > self.price:
            return self.old_price - self.price
        elif self.discount_percentage > 0:
            return (self.price * self.discount_percentage) / 100
        return 0

    @property
    def final_price(self):
        """Get the price after discount."""
        return self.price - self.discount_amount
    
# product specification model
class ProductSpecification(models.Model):
    """
    Stores technical or descriptive specifications for each product.
    Example: CPU = Ryzen 7 7735HS, RAM = 16GB DDR5, Display = 165Hz
    """

    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="specifications"
    )
    key = models.CharField(max_length=255)     # Example: "CPU", "RAM", "Display"
    value = models.TextField()                 # Example: "Ryzen 7 7735HS"

    class Meta:
        indexes = [
            models.Index(fields=["product", "key"]),
        ]
        verbose_name = "Product Specification"
        verbose_name_plural = "Product Specifications"
        ordering = ["product", "key"]

    def __str__(self):
        return f"{self.product.name} - {self.key}: {self.value}"


class Review(models.Model):
    """
    Represents a user review for a specific product.
    Includes rating, text feedback, optional media, and moderation fields.
    """

    # 👤 User who made the review
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="product_reviews"
    )

    # 🎯 Product being reviewed
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="reviews"
    )

    # ⭐ Rating: integer 1–5
    rating = models.PositiveSmallIntegerField(
        choices=[(i, str(i)) for i in range(1, 6)],
        help_text="Rating from 1 (worst) to 5 (best)"
    )

    # 💬 Optional review text
    comment = models.TextField(blank=True)

    # 🖼️ Optional review images (like product photos)
    images = models.JSONField(default=list, blank=True)  # e.g. ["review1.jpg", "review2.png"]

    # ✅ Moderation / status
    is_approved = models.BooleanField(default=True)
    is_verified_purchase = models.BooleanField(default=False)

    # 📅 Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["product", "rating"]),
            models.Index(fields=["user", "created_at"]),
        ]
        unique_together = ("user", "product")  # Each user can review a product only once

    def __str__(self):
        return f"{self.product.name} - {self.user.username} ({self.rating}⭐)"

    @property
    def short_comment(self):
        """Truncate comment for admin or preview."""
        return (self.comment[:60] + "...") if self.comment and len(self.comment) > 60 else self.comment

    @property
    def stars(self):
        """Return star icons for UI rendering."""
        return "★" * self.rating + "☆" * (5 - self.rating)

