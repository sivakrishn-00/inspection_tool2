from django.contrib import admin
from .models import InspectionCategory, InspectionQuestion, OpsInspection, InspectionAnswer

@admin.register(InspectionCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order',)

@admin.register(InspectionQuestion)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'category', 'question_type')
    list_filter = ('category', 'question_type', 'is_active')

admin.site.register(OpsInspection)
admin.site.register(InspectionAnswer)
