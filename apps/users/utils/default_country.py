from django.apps import apps

def get_default_country():
    """
    Returns the default Country object, creating it if necessary.
    Uses apps.get_model() to prevent circular import issues.
    """
    try:
        # apps.get_model() safely gets the model at runtime
        Country = apps.get_model('users', 'Country')
        return Country.objects.get(code='NP')
    except Country.DoesNotExist:
        return Country.objects.create(name='Nepal', code='NP')