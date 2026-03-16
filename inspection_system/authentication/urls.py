from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'authentication'

urlpatterns = [
    path("login/", auth_views.LoginView.as_view(template_name="login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="/login/"), name="logout"),
    path("", auth_views.LoginView.as_view(template_name="login.html"), name="root_login"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("users/", views.user_list, name="user_list"),
    path("users/create/", views.user_create, name="user_create"),
    path("users/<int:pk>/edit/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/delete/", views.user_delete, name="user_delete"),
    path("projects/", views.project_list, name="project_list"),
    path("projects/create/", views.project_create, name="project_create"),
    path("projects/<int:pk>/", views.project_detail, name="project_detail"),
    path("roles/", views.role_list, name="role_list"),
    path("roles/create/", views.role_create, name="role_create"),
    path("roles/<int:pk>/edit/", views.role_edit, name="role_edit"),
    path("roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
    path("service-codes/", views.service_code_list, name="service_code_list"),
    path("service-codes/<int:pk>/edit/", views.service_code_edit, name="service_code_edit"),
    path("service-codes/<int:pk>/delete/", views.service_code_delete, name="service_code_delete"),
    path("api/service-code/<int:pk>/history/", views.service_code_history_api, name="service_code_history_api"),
    path("vehicles/", views.vehicle_list, name="vehicle_list"),
    path("vehicles/<int:pk>/edit/", views.vehicle_edit, name="vehicle_edit"),
    path("vehicles/<int:pk>/delete/", views.vehicle_delete, name="vehicle_delete"),
    path("api/vehicle/<int:pk>/location-history/", views.vehicle_location_history_api, name="vehicle_location_history_api"),
    path("districts/", views.district_list, name="district_list"),
    path("districts/<int:pk>/delete/", views.district_delete, name="district_delete"),
    path("reports/", views.reports_dashboard, name="reports"),
    path("settings/", views.settings_dashboard, name="settings_dashboard"),
    path("notifications/<int:notification_id>/read/", views.mark_notification_read, name="mark_notification_read"),
    path("notifications/read-all/", views.mark_all_read, name="mark_all_read"),
    path("login-audit/", views.login_audit_view, name="login_audit"),
    path("api-management/", views.api_management_view, name="api_management"),
    path("api/v1/export/", views.data_export_api, name="data_export_api"),
]
