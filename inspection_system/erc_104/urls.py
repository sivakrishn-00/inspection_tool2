from django.urls import path
from . import views

app_name = 'erc_104'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('inspection/', views.perform_inspection, name='inspection'),
    path('manage/', views.manage_checklist, name='manage_checklist'),

]
