from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class District(models.Model):
    name = models.CharField(max_length=100, unique=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

class Mandal(models.Model):
    name = models.CharField(max_length=100)
    district = models.ForeignKey(District, on_delete=models.CASCADE, related_name='mandals')

    class Meta:
        ordering = ['name']
        unique_together = ('name', 'district')

    def __str__(self):
        return f"{self.name} ({self.district.name})"

class Project(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    scheduler_hour = models.IntegerField(default=10, help_text="Hour of the day to check deadlines (0-23)")
    scheduler_minute = models.IntegerField(default=0, help_text="Minute of the hour to check deadlines (0-59)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)
    service_codes = models.ManyToManyField('ServiceCode', blank=True, related_name='roles')
    is_exclusive_service_access = models.BooleanField(default=True, help_text="If true, users with this role see only unassigned codes.")
    is_single_service_code = models.BooleanField(default=False, help_text="If true, users can select only one code (Radio buttons). details")
    
    inspection_deadline_days = models.IntegerField(default=1, help_text="Days allowed before inspection is considered missed.")
    inspection_deadline_hours = models.IntegerField(default=0, help_text="Additional hours allowed.")
    inspection_deadline_minutes = models.IntegerField(default=0, help_text="Additional minutes allowed.")

    def __str__(self):
        return self.name

class ServiceCode(models.Model):
    code = models.CharField(max_length=20, unique=True, help_text="Service Code (e.g., K, A1)")
    description = models.TextField(blank=True, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='service_codes', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.code} - {self.description or 'No Description'}"

class Vehicle(models.Model):
    registration_number = models.CharField(max_length=50, unique=True)
    model_name = models.CharField(max_length=100)
    service_code = models.OneToOneField(ServiceCode, on_delete=models.SET_NULL, null=True, blank=True, related_name='current_vehicle')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    mandal = models.ForeignKey(Mandal, on_delete=models.SET_NULL, null=True, blank=True, related_name='vehicles')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='vehicles', null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.registration_number} ({self.model_name})"

class ServiceCodeHistory(models.Model):
    ACTION_CHOICES = [
        ('assigned', 'Assigned'),
        ('unassigned', 'Unassigned'),
    ]
    service_code = models.ForeignKey(ServiceCode, on_delete=models.CASCADE, related_name='history')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='assignment_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, default='assigned')
    
    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.service_code.code} -> {self.vehicle.registration_number} ({self.action}) at {self.timestamp.date()}"

class UserServiceCodeHistory(models.Model):
    ACTION_CHOICES = [
        ('assigned', 'Assigned'),
        ('unassigned', 'Unassigned'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='service_code_history')
    service_code = models.ForeignKey(ServiceCode, on_delete=models.CASCADE, related_name='user_assignment_history')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='actions_performed')

    class Meta:
        verbose_name_plural = "User Service Code Histories"
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.user.username} - {self.service_code.code} ({self.action}) at {self.timestamp.date()}"

class VehicleLocationHistory(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='location_history')
    service_code = models.ForeignKey(ServiceCode, on_delete=models.SET_NULL, null=True, blank=True)
    latitude = models.FloatField()
    longitude = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.vehicle.registration_number} at ({self.latitude}, {self.longitude}) on {self.timestamp}"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    assigned_project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, related_name='members')
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    assigned_service_codes = models.ManyToManyField('ServiceCode', blank=True, related_name='assigned_users')
    emp_id = models.CharField(max_length=50, blank=True, null=True, help_text="Employee ID (max 20k people)")
    supervisor = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates', help_text="The person this user reports to.")

    def __str__(self):
        role_name = self.role.name if self.role else 'No Role'
        project_name = self.assigned_project.name if self.assigned_project else 'No Project'
        return f"{self.user.username} - {role_name} in {project_name}"
        
    @property
    def filtered_notifications(self):
        if self.user.is_superuser:
            return self.user.notifications.all()
        if self.assigned_project:
            # We want to show notifications explicitly tied to their project OR global notifications (project__isnull=True)
            return self.user.notifications.filter(models.Q(project=self.assigned_project) | models.Q(project__isnull=True))
        return self.user.notifications.all()
        
    @property
    def unread_notifications_exists(self):
        return self.filtered_notifications.filter(is_read=False).exists()

class ProjectRoleDeadline(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='role_deadlines')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='project_deadlines')
    
    inspection_deadline_days = models.IntegerField(default=1, help_text="Days allowed before inspection is considered missed.")
    inspection_deadline_hours = models.IntegerField(default=0, help_text="Additional hours allowed.")
    inspection_deadline_minutes = models.IntegerField(default=0, help_text="Additional minutes allowed.")

    class Meta:
        unique_together = ('project', 'role')

    def __str__(self):
        return f"{self.project.name} - {self.role.name} Deadlines"

class Notification(models.Model):
    TYPE_CHOICES = [
        ('alert', 'Alert'),
        ('warning', 'Warning'),
        ('info', 'Info'),
        ('success', 'Success'),
    ]
    
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, null=True, blank=True, related_name='project_notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default='info')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    link = models.CharField(max_length=255, blank=True, null=True, help_text="Optional link to action")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type.upper()}: {self.title} -> {self.recipient.username}"


class Inspection(models.Model):
    STATUS_CHOICES = [
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('flagged', 'Flagged (Complaint Raised)'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='inspections')
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='inspections', null=True, blank=True)
    inspector = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='inspections_conducted')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='passed')
    details = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Inspection #{self.id} - {self.project.name} ({self.status})"

class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    feature_code = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    is_enabled = models.BooleanField(default=False)

    class Meta:
        unique_together = ('role', 'feature_code')

    def __str__(self):
        return f"{self.role.name} - {self.feature_code}: {self.is_enabled}"

class SystemSetting(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.key}: {self.value}"
from django.db import models

from django.contrib.auth.models import User

from django.contrib.auth.signals import user_logged_in

from django.dispatch import receiver



class LoginRecord(models.Model):

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_records')

    ip_address = models.CharField(max_length=50, blank=True, null=True)

    user_agent = models.CharField(max_length=255, blank=True, null=True)

    timestamp = models.DateTimeField(auto_now_add=True)
    logout_timestamp = models.DateTimeField(null=True, blank=True)



    class Meta:

        ordering = ['-timestamp']



    def __str__(self):

        return f"{self.user.username} logged in from {self.ip_address} at {self.timestamp}"



@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    # 1. Try to get client-side IP from cookie (set by JS in login.html)
    ip = request.COOKIES.get('client_network_ip')
    
    if not ip or ip in ['127.0.0.1', '::1', 'unknown']:
        # 2. Fallback to robust header checking
        possible_headers = [
            'HTTP_X_FORWARDED_FOR',
            'HTTP_X_REAL_IP',
            'HTTP_CF_CONNECTING_IP',
            'HTTP_CLIENT_IP',
            'HTTP_X_FORWARDED',
            'HTTP_X_CLUSTER_CLIENT_IP',
            'HTTP_FORWARDED_FOR',
            'HTTP_FORWARDED',
        ]
        
        for header in possible_headers:
            val = request.META.get(header)
            if val:
                ips = [i.strip() for i in val.split(',')]
                for candidate in ips:
                    if candidate and candidate not in ['127.0.0.1', '::1', 'unknown']:
                        ip = candidate
                        break
                if ip:
                    break
                    
    # 3. Last fallback to REMOTE_ADDR
    if not ip:
        ip = request.META.get('REMOTE_ADDR')
                
    user_agent = request.META.get('HTTP_USER_AGENT', '')[:255]
    
    LoginRecord.objects.create(
        user=user,
        ip_address=ip or 'Unknown',
        user_agent=user_agent
    )
    print(f"DEBUG: Login from {user.username} - Final IP: {ip}")


from django.contrib.auth.signals import user_logged_out

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        # Update the most recent login record with the logout timestamp
        latest_record = LoginRecord.objects.filter(user=user).order_by('-timestamp').first()
        if latest_record:
            latest_record.logout_timestamp = timezone.now()
            latest_record.save()
            print(f"DEBUG: Logout for {user.username} at {latest_record.logout_timestamp}")



import uuid
import secrets

class APIKey(models.Model):
    name = models.CharField(max_length=100)
    key = models.CharField(max_length=64, unique=True, default=secrets.token_urlsafe)
    project = models.ForeignKey(Project, on_delete=models.SET_NULL, null=True, blank=True, help_text="If set, restricts access to this project. If null, allows access to all data.")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_api_keys')
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.key[:8]}..."

class APIKeyHistory(models.Model):
    ACTION_CHOICES = [
        ('created', 'Created'),
        ('revoked', 'Revoked'),
        ('shared', 'Shared'),
    ]
    api_key = models.ForeignKey(APIKey, on_delete=models.CASCADE, related_name='history')
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    performed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    shared_with = models.CharField(max_length=255, blank=True, null=True, help_text="Information on who an API key was shared with")
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.api_key.name} - {self.action} at {self.timestamp}"

