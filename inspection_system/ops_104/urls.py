from django.urls import path
from . import views

app_name = 'ops_104'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inspection/', views.perform_inspection, name='inspection'),
    path('manage/', views.manage_checklist, name='manage_checklist'),
    
    # Complaints Workflow
    path('complaints/', views.complaint_list, name='complaint_list'),
    path('complaints/resolve/<int:complaint_id>/', views.resolve_complaint, name='resolve_complaint'),
    path('complaints/close/<int:complaint_id>/', views.close_complaint, name='close_complaint'),
]
