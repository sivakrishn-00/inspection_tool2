from django.db import models
from django.contrib.auth.models import User
from authentication.models import Vehicle, District

class OpsInspection(models.Model):
    vehicle = models.ForeignKey(Vehicle, on_delete=models.CASCADE, related_name='ops_inspections')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ops_inspections')
    district = models.ForeignKey(District, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    overall_status = models.CharField(max_length=20, default='submitted')

    def __str__(self):
        return f"{self.vehicle.registration_number} - {self.created_at.strftime('%Y-%m-%d')}"

class InspectionCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_categories')

    class Meta:
        verbose_name_plural = "Inspection Categories"

    def __str__(self):
        return self.name

class InspectionQuestion(models.Model):
    QUESTION_TYPES = [
        ('boolean', 'Good / Not Good'), # Interior/Exterior
        ('condition', 'Good / Average / Poor / Not Operational'), # Components
        ('maintenance', 'Maintained / Partially / Not Maintained / Not Available'), # Registers/Drugs
        ('equipment', 'Equipment (Available/Working/Not Working/Not Available)'), # Equipment List
    ]

    category = models.ForeignKey(InspectionCategory, on_delete=models.CASCADE, related_name='questions')
    text = models.CharField(max_length=255)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPES)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.text}"

class InspectionAnswer(models.Model):
    inspection = models.ForeignKey(OpsInspection, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(InspectionQuestion, on_delete=models.CASCADE)
    response = models.CharField(max_length=50)
    
    remarks = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='inspection_evidence/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f"{self.inspection} - {self.question.text}: {self.response}"

class Complaint(models.Model):
    STATUS_CHOICES = [
        ('raised', 'Raised'),
        ('assigned', 'Assigned'), # Kept for backward compatibility/status flow
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]
    
    inspection = models.ForeignKey(OpsInspection, on_delete=models.CASCADE, related_name='complaints')
    tracking_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='raised_complaints')
    item_name = models.CharField(max_length=255, null=True, blank=True, help_text="Name of the question or category for easy DB identification")
    
    # Now optional as it represents a group of failures in a category
    question = models.ForeignKey(InspectionQuestion, on_delete=models.CASCADE, null=True, blank=True)
    category = models.ForeignKey(InspectionCategory, on_delete=models.CASCADE)
    
    category_manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='category_complaints')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='raised')
    is_remarked = models.BooleanField(default=False, help_text="True if this was previously raised by someone else/past turn")
    
    description = models.TextField(blank=True, null=True) # Combined remarks
    inspector_photo = models.ImageField(upload_to='complaint_evidence/inspector/', blank=True, null=True)
    
    resolution_remarks = models.TextField(blank=True, null=True)
    resolution_proof = models.ImageField(upload_to='complaint_evidence/resolution/', blank=True, null=True)
    
    closure_remarks = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.item_name or self.category.name} ({self.status}) - ID: {self.id}"
