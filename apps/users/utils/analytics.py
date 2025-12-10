from django.db.models import Count
from django.db.models.functions import TruncDay
from apps.users.models import User, UserActivityLog
from django.utils import timezone
from datetime import timedelta

def signups_last_n_days(n_days=30):
    since = timezone.now() - timedelta(days=n_days)
    qs = User.objects.filter(date_joined__gte=since)
    data = (
        qs.annotate(day=TruncDay("date_joined"))
          .values("day")
          .annotate(count=Count("id"))
          .order_by("day")
    )
    # return list of dicts or convert to day->count mapping
    return list(data)