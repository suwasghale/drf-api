# apps/product/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from apps.product.models import Product

@receiver([post_save, post_delete], sender=Product)
def clear_product_cache(sender, instance, **kwargs):
    # delete detail cache key
    cache.delete(f"product_detail:{instance.slug}")
    # If you use redis and delete_pattern is available:
    try:
        cache.delete_pattern("product_list:*")
    except AttributeError:
        # fallback to clearing entire cache (use cautiously on large deployments)
        cache.clear()
    # Optionally, you can also clear the entire product list cache
    cache.delete("product_list")