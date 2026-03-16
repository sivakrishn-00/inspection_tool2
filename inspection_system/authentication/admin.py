from django.contrib import admin
from .models import District, Project, Role, ServiceCode, Vehicle, UserProfile

admin.site.register(District)
admin.site.register(Project)
@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_exclusive_service_access')
admin.site.register(ServiceCode)
admin.site.register(Vehicle)
admin.site.register(UserProfile)
