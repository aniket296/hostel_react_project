from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class UsernameOrPhoneBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get("username")

        if not username or not password:
            return None

        user = None

        # Try phone number first
        try:
            user = User.objects.get(phone_number=username)
        except User.DoesNotExist:
            pass

        # Try username if phone not found
        if user is None:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return None

        if user.is_locked and user.role != "admin":
            return None

        if user.check_password(password):
            return user

        return None