from django.core.management.base import BaseCommand
#from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


class Command(BaseCommand):

    def handle(self, *args, **options):

        User = get_user_model()

        if not User.objects.filter(user_username="nimda").exists():
            User.objects.create_superuser("nimda@papr.co", "nimda", "ScienceFax3k")
