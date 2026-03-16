from django.db.models.signals import post_migrate
from django.contrib.auth.models import User
from django.dispatch import receiver

@receiver(post_migrate)
def create_default_admin(sender, **kwargs):
    # Only run for this app to avoid multiple calls if multiple apps have signals
    if sender.name == 'authentication':
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser(
                username='admin',
                email='admin@example.com',
                password='admin'
            )
            print("Default superuser 'admin' created with password 'admin'")
