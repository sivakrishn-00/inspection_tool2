from django.db import models
from django.contrib.auth.models import User

class ERCCenter(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ERCInspection(models.Model):
    center = models.ForeignKey(ERCCenter, on_delete=models.CASCADE, related_name='erc_inspections')
    inspector = models.ForeignKey(User, on_delete=models.CASCADE, related_name='erc_inspections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    overall_status = models.CharField(max_length=20, default='submitted')
    visual_layout_snapshot = models.TextField(blank=True, null=True, help_text="JSON snapshot of the grid state")

    def __str__(self):
        return f"{self.center.name} - {self.created_at.strftime('%Y-%m-%d')}"

class ERCCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "ERC Categories"

    def __str__(self):
        return self.name

class ERCItem(models.Model):
    ITEM_TYPES = [
        ('boolean', 'Good / Not Good'), 
        ('condition', 'Good / Damaged / Missing'),
        ('availability', 'Available / Not Available'),
    ]

    category = models.ForeignKey(ERCCategory, on_delete=models.CASCADE, related_name='items')
    text = models.CharField(max_length=255)
    item_type = models.CharField(max_length=50, choices=ITEM_TYPES, default='boolean')
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.category.name} - {self.text}"

class ERCResponse(models.Model):
    inspection = models.ForeignKey(ERCInspection, on_delete=models.CASCADE, related_name='responses')
    item = models.ForeignKey(ERCItem, on_delete=models.CASCADE)
    
    response = models.CharField(max_length=50)
    
    remarks = models.TextField(blank=True, null=True)
    photo = models.ImageField(upload_to='erc_evidence/%Y/%m/%d/', blank=True, null=True)

    def __str__(self):
        return f"{self.inspection} - {self.item.text}: {self.response}"

class ERCGridSection(models.Model):
    ICON_CHOICES = [
        ('chair', 'Chair'),
        ('monitor', 'Monitor'),
        ('bulb', 'Light Bulb'),
        ('ac', 'AC Unit'),
        ('fire', 'Fire Extinguisher'),
        ('door', 'Door'),
        ('headset', 'Headset'),
        ('battery', 'Battery'),
        ('water', 'Water Tap'),
        ('wifi', 'WiFi / Server'),
        ('cctv', 'CCTV Camera'),
    ]

    name = models.CharField(max_length=100) # e.g. "Server Room"
    slug = models.SlugField(unique=True) # e.g. "server_room"
    rows = models.IntegerField(default=3)
    cols = models.IntegerField(default=3)
    total_items = models.IntegerField(blank=True, null=True, help_text="Total items to render. If set, overrides rows*cols.")
    icon = models.CharField(max_length=50, choices=ICON_CHOICES, default='chair')
    prefix = models.CharField(max_length=10, default='S') # e.g. "S1", "S2"
    order = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

