from django.db import models
from apps.users.models import Country
def get_default_country():
    # This queries the database for the country by its code,
    # which is more stable than relying on a specific ID.
    try:
        return Country.objects.get(code='NP')
    except Country.DoesNotExist:
        # If the country doesn't exist, create it.
        return Country.objects.create(name='Nepal', code='NP')