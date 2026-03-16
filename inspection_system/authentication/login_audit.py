from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver

class LoginRecord(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_records')
    ip_address = models.CharField(max_length=50, blank=True, null=True)
    user_agent = models.CharField(max_length=255, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} logged in from {self.ip_address} at {self.timestamp}"

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # Try different headers to get the real IP address
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('HTTP_X_REAL_IP')
        if not ip:
            ip = request.META.get('REMOTE_ADDR')
        
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255] # Limit length
    
    LoginRecord.objects.create(
        user=user,
        ip_address=ip,
        user_agent=user_agent
    )
