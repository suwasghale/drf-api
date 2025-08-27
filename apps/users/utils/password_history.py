from apps.users.models import PasswordHistory
from django.db import transaction
from django.contrib.auth.hashers import check_password


def save_password_history(user, old_hashed_password):
    """saves the old hashed passwords to the history table"""

     # Use transaction.atomic() to ensure this operation is atomic
    with transaction.atomic():
        # Step 1: Get the primary keys of the most recent passwords.
        # This is a separate, valid query.
        recent_pks = list(PasswordHistory.objects.filter(user=user)
                                                 .order_by('-timestamp')
                                                 .values_list('pk', flat=True)[:10])
        #  PasswordHistory.objects.filter(user=user).order_by('timestamp').exclude(
        #     pk__in=PasswordHistory.objects.filter(user=user).order_by('-timestamp').values_list('pk', flat=True)[:5]
        # ).delete() This line is unsupported by mysql in older version so.

        # Step 2: Delete older passwords not in the recent_pks list.
        # This avoids the unsupported subquery.
        PasswordHistory.objects.filter(user=user).exclude(pk__in=recent_pks).delete()

        # Create the new history entry.
        PasswordHistory.objects.create(user=user, password_hash=old_hashed_password)


def check_password_history(user, raw_password, limit = 10):
    """
    Prevents reuse of the last `limit` passwords by checking against history.
    Returns True if the password has been used before, False otherwise.
    """
    last_passwords = PasswordHistory.objects.filter(user=user).order_by('-timestamp')[:limit]
    for pw_hist in last_passwords:
        # check against the stored password_hash.
        if check_password(raw_password, pw_hist.password_hash):
            return True
    return False