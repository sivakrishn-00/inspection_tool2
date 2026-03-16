from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from .models import Project, UserProfile, Role, Inspection, ServiceCode, Vehicle, RolePermission, District, Mandal, ServiceCodeHistory, UserServiceCodeHistory, Notification, ProjectRoleDeadline
from django.db import models
from django.utils import timezone
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from ops_104.models import OpsInspection
from erc_104.models import ERCInspection
from django.db.models.functions import TruncDate
from datetime import timedelta
import json

@login_required
def dashboard(request):
    if request.user.is_superuser:
        projects = Project.objects.all()
        project_data = []
        ops_count = OpsInspection.objects.count()
        erc_count = ERCInspection.objects.count()
        legacy_count = Inspection.objects.count()
        total_inspections = ops_count + legacy_count + erc_count
        for project in projects:
            dashboard_url = '#'
            if 'ERC' in project.name:
                total = erc_count
                complaints = 0
                status_badge = "Active"
                dashboard_url = 'erc_104:dashboard'
            elif '104' in project.name:
                total = ops_count
                complaints = 0 
                status_badge = "Active"
                dashboard_url = 'ops_104:dashboard'
            elif '108' in project.name:
                from ops_108.models import OpsInspection as Ops108Inspection
                total = Ops108Inspection.objects.count()
                complaints = 0
                status_badge = "Active"
                dashboard_url = 'ops_108:dashboard'
            else:
                total = Inspection.objects.filter(project=project).count()
                complaints = Inspection.objects.filter(project=project, status__in=['failed', 'flagged']).count()
                status_badge = "Active"
            project_data.append({
                'project': project,
                'total_inspections': total,
                'complaints': complaints,
                'status': status_badge,
                'dashboard_url': dashboard_url
            })
        recent_ops = OpsInspection.objects.select_related('inspector', 'vehicle').order_by('-created_at')[:5]
        recent_activities = []
        for op in recent_ops:
            recent_activities.append({
                'user': op.inspector.username,
                'action': f"Inspected {op.vehicle.registration_number}",
                'time': op.created_at,
                'status': 'Completed'
            })
        context = {
            'project_data': project_data,
            'total_inspections': total_inspections,
            'pending_actions': Inspection.objects.filter(status='flagged').count(),
            'active_users': User.objects.count(),
            'recent_activities': recent_activities
        }
        return render(request, 'dashboard.html', context)
    else:
        try:
            profile = request.user.profile
            project = profile.assigned_project
            if not project:
                 messages.error(request, "You are not assigned to any project.")
                 return render(request, 'no_project.html')
            if 'ERC' in project.name:
                return redirect('erc_104:dashboard')
            elif '108' in project.name:
                return redirect('ops_108:dashboard')
            elif '104' in project.name:
                return redirect('ops_104:dashboard')

            context = {
                'project': project,
                'role': profile.role.name if profile.role else "Member",
            }
            return render(request, 'project_dashboard.html', context)
        except UserProfile.DoesNotExist:
             messages.error(request, "User profile not found.")
             return render(request, 'no_project.html')

@login_required
def user_list(request):
    if not request.user.is_superuser:
        return redirect('authentication:dashboard')
    users = User.objects.all().select_related('profile__assigned_project', 'profile__role').order_by('-date_joined')
    projects = Project.objects.all()
    roles = Role.objects.all()
    return render(request, 'authentication/user_list.html', {'users': users, 'projects': projects, 'roles': roles})

@login_required
def user_create(request):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        project_id = request.POST.get('project')
        role_id = request.POST.get('role')
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('authentication:user_list')
        user = User.objects.create_user(username=username, email=email, password=password)
        project = Project.objects.get(id=project_id) if project_id else None
        role = Role.objects.get(id=role_id) if role_id else None
        emp_id = request.POST.get('emp_id')
        UserProfile.objects.create(user=user, assigned_project=project, role=role, emp_id=emp_id)
        messages.success(request, f'User {username} created successfully')
        return redirect('authentication:user_list')
    return redirect('authentication:user_list')

@login_required
def role_list(request):
    if not request.user.is_superuser:
        return redirect('authentication:dashboard')
    
    # Ensure core roles exist
    Role.objects.get_or_create(name='manager')
    Role.objects.get_or_create(name='subordinate')
    Role.objects.get_or_create(name='inspection')
    
    roles = Role.objects.all()
    return render(request, 'authentication/role_list.html', {'roles': roles})

@login_required
def role_create(request):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if Role.objects.filter(name__iexact=name).exists():
             messages.error(request, 'Role name already exists')
             return redirect('authentication:role_list')
        is_exclusive = request.POST.get('is_exclusive') == 'on'
        is_single = request.POST.get('is_single') == 'on'
        Role.objects.create(
            name=name, 
            description=description, 
            is_exclusive_service_access=is_exclusive,
            is_single_service_code=is_single
        )
        messages.success(request, f'Role {name} created successfully')
        return redirect('authentication:role_list')
    return redirect('authentication:role_list')

@login_required
def project_list(request):
    if not request.user.is_superuser:
        return redirect('authentication:dashboard')
    projects = Project.objects.all().order_by('-created_at')
    return render(request, 'authentication/project_list.html', {'projects': projects})

@login_required
def project_create(request):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        if Project.objects.filter(name=name).exists():
             messages.error(request, 'Project name already exists')
             return redirect('authentication:project_list')
        Project.objects.create(name=name, description=description)
        messages.success(request, f'Project {name} created successfully')
        return redirect('authentication:project_list')
    return redirect('authentication:project_list')

@login_required
def project_detail(request, pk):
    if not request.user.is_superuser:
        return redirect('authentication:dashboard')
    project = get_object_or_404(Project, pk=pk)
    team_members = UserProfile.objects.filter(assigned_project=project).select_related('user', 'role')
    all_roles = Role.objects.all()
    if request.method == 'POST':
        if 'update_role' in request.POST:
            profile_id = request.POST.get('profile_id')
            new_role_id = request.POST.get('role')
            profile = get_object_or_404(UserProfile, id=profile_id, assigned_project=project)
            new_role = get_object_or_404(Role, id=new_role_id)
            profile.role = new_role
            profile.save()
            messages.success(request, 'Role updated successfully.')
            return redirect('authentication:project_detail', pk=pk)
        elif 'remove_member' in request.POST:
            profile_id = request.POST.get('profile_id')
            profile = get_object_or_404(UserProfile, id=profile_id, assigned_project=project)
            profile.assigned_project = None
            profile.role = None
            profile.save()
            messages.warning(request, 'Member removed from project.')
            return redirect('authentication:project_detail', pk=pk)
    active_inspections = 0
    if 'ERC' in project.name:
        active_inspections = ERCInspection.objects.count()
    elif '104' in project.name:
        active_inspections = OpsInspection.objects.count()
    elif '108' in project.name:
        from ops_108.models import OpsInspection as Ops108Inspection
        active_inspections = Ops108Inspection.objects.count()
    else:
        active_inspections = Inspection.objects.filter(project=project).count()
    context = {
        'project': project,
        'team_members': team_members,
        'roles': all_roles,
        'active_inspections': active_inspections,
    }
    return render(request, 'authentication/project_detail.html', context)


@login_required
def role_edit(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        role.description = request.POST.get('description')
        role.is_exclusive_service_access = request.POST.get('is_exclusive') == 'on'
        role.is_single_service_code = request.POST.get('is_single') == 'on'
        role.save()
        messages.success(request, 'Role updated.')
        return redirect('authentication:role_list')
    return render(request, 'authentication/role_edit.html', {'role': role})

@login_required
def user_edit(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    target_user = get_object_or_404(User, pk=pk)
    try:
        profile = target_user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=target_user)
    if profile.assigned_project:
        all_service_codes = ServiceCode.objects.filter(project=profile.assigned_project).order_by('code')
    else:
        all_service_codes = ServiceCode.objects.all().order_by('code')
    all_roles = Role.objects.all()
    all_projects = Project.objects.all()
    role_data = {role.id: role.is_exclusive_service_access for role in all_roles}
    role_single_data = {role.id: role.is_single_service_code for role in all_roles}
    role_hierarchy = ['pm', 'rm', 'DM', 'OE', 'user']
    role_ranking = {name: i for i, name in enumerate(role_hierarchy)}
    role_rank_by_id = {str(role.id): role_ranking.get(role.name, 99) for role in all_roles}
    rank_to_name = {i: name for i, name in enumerate(role_hierarchy)}
    code_owner_map = {}
    profiles_with_codes = UserProfile.objects.exclude(user=target_user).select_related('user', 'role').prefetch_related('assigned_service_codes')
    allocations = {}
    for p in profiles_with_codes:
        if p.role:
            role_id_str = str(p.role.id)
            for code in p.assigned_service_codes.all():
                code_id_str = str(code.id)
                if code_id_str not in code_owner_map:
                    code_owner_map[code_id_str] = {}
                code_owner_map[code_id_str][role_id_str] = {
                    'id': p.id,
                    'name': p.user.username,
                    'role': p.role.name
                }
                if code.id not in allocations:
                    allocations[code.id] = []
                allocations[code.id].append(p.role.id)
    if request.method == 'POST':
        target_user.username = request.POST.get('username')
        target_user.email = request.POST.get('email')
        target_user.save()
        role_id = request.POST.get('role')
        project_id = request.POST.get('project')
        emp_id = request.POST.get('emp_id')
        profile.role_id = role_id if role_id else None
        profile.assigned_project_id = project_id if project_id else None
        profile.emp_id = emp_id if emp_id else None
        supervisor_id = request.POST.get('supervisor')
        profile.supervisor_id = supervisor_id if supervisor_id else None
        selected_codes_ids = [int(cid) for cid in request.POST.getlist('service_codes')]
        is_single = False
        if role_id:
             try:
                 r = Role.objects.get(id=role_id)
                 is_single = r.is_single_service_code
             except Role.DoesNotExist:
                 pass
        if is_single and len(selected_codes_ids) > 1:
             messages.warning(request, "This role allows only one service code. The first one was selected.")
             selected_codes_ids = selected_codes_ids[:1]
        current_codes_ids = list(profile.assigned_service_codes.values_list('id', flat=True))
        to_add = set(selected_codes_ids) - set(current_codes_ids)
        to_remove = set(current_codes_ids) - set(selected_codes_ids)
        for sc_id in to_remove:
            last_log = UserServiceCodeHistory.objects.filter(user=target_user, service_code_id=sc_id).first()
            if not last_log or last_log.action != 'unassigned':
                UserServiceCodeHistory.objects.create(
                    user=target_user,
                    service_code_id=sc_id,
                    action='unassigned',
                    performed_by=request.user
                )
        for sc_id in to_add:
            last_log = UserServiceCodeHistory.objects.filter(user=target_user, service_code_id=sc_id).first()
            if not last_log or last_log.action != 'assigned':
                UserServiceCodeHistory.objects.create(
                    user=target_user,
                    service_code_id=sc_id,
                    action='assigned',
                    performed_by=request.user
                )
        profile.assigned_service_codes.set(selected_codes_ids)
        profile.save()
        messages.success(request, f'User {target_user.username} updated successfully.')
        return redirect('authentication:user_list')
    current_assignments = profile.assigned_service_codes.all()
    for sc in current_assignments:
        if not UserServiceCodeHistory.objects.filter(user=target_user, service_code=sc).exists():
            UserServiceCodeHistory.objects.create(
                user=target_user,
                service_code=sc,
                action='assigned',
                performed_by=None
            )
    # Ensure superusers and managers have profiles for the supervisor dropdown
    for admin_user in User.objects.filter(is_superuser=True):
        UserProfile.objects.get_or_create(user=admin_user)
    
    manager_role = Role.objects.filter(name='manager').first()
    if manager_role:
        for manager_user in User.objects.filter(profile__role=manager_role):
            UserProfile.objects.get_or_create(user=manager_user)

    # Fetch potential supervisors based on roles (passing profiles for correct ID mapping)
    admins = UserProfile.objects.filter(user__is_superuser=True).select_related('user').order_by('user__username')
    managers = UserProfile.objects.filter(role=manager_role).select_related('user').order_by('user__username') if manager_role else UserProfile.objects.none()

    return render(request, 'authentication/user_edit.html', {
        'target_user': target_user,
        'profile': profile,
        'all_service_codes': all_service_codes,
        'all_roles': all_roles,
        'all_projects': all_projects,
        'role_data': role_data,
        'role_single_data': role_single_data,
        'allocations': allocations,
        'code_owner_map': code_owner_map,
        'role_rank_by_id': role_rank_by_id,
        'rank_to_name': rank_to_name,
        'assignment_history': profile.user.service_code_history.all().select_related('service_code', 'performed_by').order_by('-timestamp')[:5],
        'admins': admins,
        'managers': managers,
    })

@login_required
def user_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('authentication:dashboard')
    target_user = get_object_or_404(User, pk=pk)
    if target_user.is_superuser:
        messages.error(request, 'Cannot delete superuser accounts.')
        return redirect('authentication:user_list')
    if request.method == 'POST':
        username = target_user.username
        target_user.delete()
        messages.success(request, f'User {username} deleted successfully.')
        return redirect('authentication:user_list')
    return redirect('authentication:user_list')

from django.db.models import Count, Q

REQUIRED_PERMISSIONS = {
    'view_reports': 'View Report Analytics',
    'view_settings': 'Access System Settings',
    'export_data': 'Export Data Buttons',
    'manage_users': 'Create/Edit Users',
}

@login_required
def settings_dashboard(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('authentication:dashboard')
        
    roles = Role.objects.all().order_by('id')
    projects = Project.objects.all().order_by('name')
    
    project_id = request.GET.get('project_id') or request.POST.get('project_id')
    selected_project = None
    role_deadlines = {}
    
    if project_id:
        selected_project = get_object_or_404(Project, id=project_id)
        for pd in ProjectRoleDeadline.objects.filter(project=selected_project):
            role_deadlines[pd.role_id] = pd
            
    role_deadlines_data = []
    if selected_project:
        for role in roles:
            deadline = role_deadlines.get(role.id)
            role_deadlines_data.append({
                'role': role,
                'days': deadline.inspection_deadline_days if deadline else 0,
                'hours': deadline.inspection_deadline_hours if deadline else 0,
                'mins': deadline.inspection_deadline_minutes if deadline else 0,
            })

    perm_map = {}
    for perm in RolePermission.objects.all():
        if perm.role_id not in perm_map:
            perm_map[perm.role_id] = {}
        perm_map[perm.role_id][perm.feature_code] = perm.is_enabled
        
    from . import scheduler

    # Get current scheduler time (Legacy check - now project specific)
    current_hour = 10
    current_minute = 0
    if selected_project:
        current_hour = selected_project.scheduler_hour
        current_minute = selected_project.scheduler_minute

    if request.method == 'POST':
        # Scheduler Setting Saving (Project Specific)
        if selected_project:
            new_hour = request.POST.get('scheduler_hour')
            new_minute = request.POST.get('scheduler_minute')
            if new_hour is not None and new_minute is not None:
                 selected_project.scheduler_hour = int(new_hour)
                 selected_project.scheduler_minute = int(new_minute)
                 selected_project.save()
                 # Trigger Dynamic Restart/Reschedule
                 scheduler.restart()

        if selected_project:
            for role in roles:
                days_key = f"deadline_days_{role.id}"
                hours_key = f"deadline_hours_{role.id}"
                mins_key = f"deadline_mins_{role.id}"
                if days_key in request.POST or hours_key in request.POST or mins_key in request.POST:
                    try:
                        pd, created = ProjectRoleDeadline.objects.get_or_create(project=selected_project, role=role)
                        pd.inspection_deadline_days = int(request.POST.get(days_key, 0))
                        pd.inspection_deadline_hours = int(request.POST.get(hours_key, 0))
                        pd.inspection_deadline_minutes = int(request.POST.get(mins_key, 0))
                        pd.save()
                    except ValueError:
                        pass
                        
        # Global permissions loop
        for role in roles:
            for code, desc in REQUIRED_PERMISSIONS.items():
                form_key = f"perm_{role.id}_{code}"
                is_checked = request.POST.get(form_key) == 'on'
                RolePermission.objects.update_or_create(
                    role=role,
                    feature_code=code,
                    defaults={
                        'is_enabled': is_checked,
                        'description': desc
                    }
                )
        messages.success(request, 'Configuration saved successfully.')
        if selected_project:
            return redirect(f"{reverse('authentication:settings_dashboard')}?project_id={selected_project.id}")
        return redirect('authentication:settings_dashboard')
        
    return render(request, 'authentication/settings.html', {
        'roles': roles,
        'features': REQUIRED_PERMISSIONS,
        'perm_map': perm_map,
        'projects': projects,
        'selected_project': selected_project,
        'role_deadlines_data': role_deadlines_data,
        'scheduler_hour': current_hour,
        'scheduler_minute': current_minute
    })

@login_required
def reports_dashboard(request):
    project_id = request.GET.get('project')
    selected_project = None
    show_ops = False
    show_erc = False
    ops_title = 'Global Operations'
    
    # Calculate 7-day date range for trends
    today = timezone.localdate()
    date_objs_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    dates_7_labels = [d.strftime('%b %d') for d in date_objs_7_days]
    
    # Helper for trend calculation in Python to bypass DB timezone issues
    def get_trend_values(queryset, dates):
        counts = {d: 0 for d in dates}
        if not queryset: return [0] * len(dates)
        from datetime import datetime, time
        start_dt = timezone.make_aware(datetime.combine(dates[0], time.min))
        # Get all created_at in range
        for dt in queryset.filter(created_at__gte=start_dt).values_list('created_at', flat=True):
            d = timezone.localtime(dt).date()
            if d in counts:
                counts[d] += 1
        return [counts[d] for d in dates]

    from ops_104.models import OpsInspection as Ops104
    from ops_108.models import OpsInspection as Ops108
    from erc_104.models import ERCInspection
    from datetime import datetime, time

    ops_104_stats = {}
    ops_108_stats = {}
    erc_stats = {}

    show_104 = False
    show_108 = False
    show_erc = False

    if project_id:
        selected_project = get_object_or_404(Project, id=project_id)
        p_name = selected_project.name.lower()
        if 'erc' in p_name:
            show_erc = True
        elif '108' in p_name:
            show_108 = True
            ops_title = '108 Ops Project'
        else:
            show_104 = True
            ops_title = '104 Ops Project'
    else:
        # Global view: Show all
        show_104 = True
        show_108 = True
        show_erc = True
        selected_project = None

    # Common Issue Filter
    negative_responses = ['poor', 'not_operational', 'not_maintained', 'not_available', 'available_not_working', 'false']
    negative_responses_erc = ['not_good', 'damaged', 'missing', 'not_available', 'false', 'poor']

    from ops_104.models import Complaint as C104, OpsInspection as Ops104
    from ops_108.models import Complaint as C108, OpsInspection as Ops108

    def process_ops_data(model_cls, date_objs):
        trend = get_trend_values(model_cls.objects, date_objs)
        total = model_cls.objects.count()
        recent = model_cls.objects.select_related('vehicle', 'district', 'inspector', 'inspector__profile', 'inspector__profile__role').prefetch_related('complaints').order_by('-created_at')[:50]
        
        table_data = []
        for ops in recent:
            issues = []
            for c in ops.complaints.all():
                status_label = f"({c.status})" if c.status != 'raised' else ""
                re_label = " [RE-RAISED]" if getattr(c, 'is_remarked', False) else ""
                issues.append(f"{c.item_name or c.category.name}{status_label}{re_label}")
            
            p = getattr(ops.inspector, 'profile', None)
            table_data.append({
                'date': ops.created_at,
                'vehicle': ops.vehicle.registration_number,
                'inspector': ops.inspector.username,
                'role': p.role.name if p and p.role else "N/A",
                'emp_id': p.emp_id if p else "N/A",
                'district': ops.district.name if ops.district else '-',
                'issues_count': len(issues),
                'issues_list': issues
            })
        
        top_insp = model_cls.objects.values('inspector__username', 'inspector__profile__role__name').annotate(count=Count('id')).order_by('-count')[:5]
        
        return {
            'total': total,
            'trend_values': json.dumps(trend),
            'trend_labels': json.dumps(dates_7_labels),
            'table_data': table_data,
            'top_inspectors': top_insp
        }

    if show_104:
        ops_104_stats = process_ops_data(Ops104, date_objs_7_days)

    if show_108:
        ops_108_stats = process_ops_data(Ops108, date_objs_7_days)

    if show_erc:
        erc_total = ERCInspection.objects.count()
        erc_trend_values = get_trend_values(ERCInspection.objects, date_objs_7_days)
        
        recent_erc = ERCInspection.objects.select_related('center', 'inspector', 'inspector__profile', 'inspector__profile__role').prefetch_related('responses', 'responses__item').order_by('-created_at')[:50]
        erc_table_data = []
        
        for erc in recent_erc:
            issues = []
            for resp in erc.responses.all():
                if str(resp.response).lower() in negative_responses_erc:
                    issues.append(f"{resp.item.text} ({resp.response})")
            
            p = getattr(erc.inspector, 'profile', None)
            erc_table_data.append({
                'date': erc.created_at,
                'center': erc.center.name,
                'inspector': erc.inspector.username,
                'role': p.role.name if p and p.role else "N/A",
                'emp_id': p.emp_id if p else "N/A",
                'issues_count': len(issues),
                'issues_list': issues
            })

        erc_stats = {
            'total': erc_total, 
            'by_center': ERCInspection.objects.values('center__name').annotate(count=Count('id')).order_by('-count')[:10], 
            'table_data': erc_table_data,
            'trend_labels': json.dumps(dates_7_labels),
            'trend_values': json.dumps(erc_trend_values)
        }

    context = {
        'all_projects': Project.objects.all(),
        'selected_project_id': int(project_id) if project_id else None,
        'show_104': show_104,
        'show_108': show_108,
        'show_erc': show_erc,
        'ops_104_stats': ops_104_stats,
        'ops_108_stats': ops_108_stats,
        'erc_stats': erc_stats,
        'ops_title': ops_title
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def service_code_list(request):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    if request.method == 'POST':
        code = request.POST.get('code')
        desc = request.POST.get('description')
        project_id = request.POST.get('project_id')
        if ServiceCode.objects.filter(code=code).exists():
             messages.error(request, 'Code exists')
        else:
             project = Project.objects.get(id=project_id) if project_id else None
             ServiceCode.objects.create(code=code, description=desc, project=project)
             messages.success(request, 'Service Code created')
        return redirect('authentication:service_code_list')
    codes = ServiceCode.objects.all().select_related('project', 'current_vehicle').order_by('code')
    project_filter = request.GET.get('project_id')
    if project_filter:
        codes = codes.filter(project_id=project_filter)
    projects = Project.objects.all()
    return render(request, 'authentication/service_code_list.html', {
        'service_codes': codes, 
        'projects': projects,
        'selected_project': project_filter
    })

@login_required
def vehicle_list(request):
    districts = District.objects.all().order_by('name')
    service_codes = ServiceCode.objects.all().order_by('code')
    projects = Project.objects.all()
    if request.user.is_superuser:
        vehicles = Vehicle.objects.all().select_related('service_code', 'district', 'project').order_by('-created_at')
    else:
        profile = getattr(request.user, 'profile', None)
        allowed_service_codes = ServiceCode.objects.none()
        if profile:
             if profile.assigned_service_codes.exists():
                 allowed_service_codes = profile.assigned_service_codes.all()
             elif profile.role:
                 allowed_service_codes = profile.role.service_codes.all()
        vehicles = Vehicle.objects.filter(service_code__in=allowed_service_codes).select_related('service_code', 'district', 'project')
    
    project_filter = request.GET.get('project_id')
    if project_filter:
        vehicles = vehicles.filter(project_id=project_filter)
    if request.method == 'POST':
        if not request.user.is_superuser:
            messages.error(request, 'Permission denied')
            return redirect('authentication:vehicle_list')
        reg = request.POST.get('registration_number')
        model = request.POST.get('model_name')
        sc_id = request.POST.get('service_code')
        district_id = request.POST.get('district_id')
        project_id = request.POST.get('project_id')
        lat = request.POST.get('latitude')
        lng = request.POST.get('longitude')
        if Vehicle.objects.filter(registration_number=reg).exists():
            messages.error(request, 'Vehicle already exists')
        else:
            sc = None
            if sc_id:
                sc = get_object_or_404(ServiceCode, id=sc_id)
                if Vehicle.objects.filter(service_code=sc).exists():
                    messages.error(request, f"Service Code {sc.code} is already assigned to another vehicle.")
                    return redirect('authentication:vehicle_list')
            project = Project.objects.get(id=project_id) if project_id else None
            v = Vehicle.objects.create(
                registration_number=reg,
                model_name=model,
                service_code=sc,
                district_id=district_id,
                project=project,
                latitude=lat,
                longitude=lng
            )
            if sc:
                ServiceCodeHistory.objects.create(service_code=sc, vehicle=v, action='assigned')
            if lat and lng:
                from authentication.models import VehicleLocationHistory
                VehicleLocationHistory.objects.create(
                    vehicle=v,
                    service_code=sc,
                    latitude=lat,
                    longitude=lng,
                    updated_by=request.user
                )
            messages.success(request, 'Vehicle added successfully')
        return redirect('authentication:vehicle_list')
    return render(request, 'authentication/vehicle_list.html', {
        'vehicles': vehicles,
        'service_codes': service_codes,
        'districts': districts,
        'projects': projects,
        'selected_project': project_filter,
        'user_is_superuser': request.user.is_superuser
    })

@login_required
def district_list(request):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    if request.method == 'POST':
        name = request.POST.get('name')
        if District.objects.filter(name__iexact=name).exists():
             messages.error(request, 'District already exists')
        else:
             District.objects.create(name=name)
             messages.success(request, 'District created')
        return redirect('authentication:district_list')
    districts = District.objects.all().order_by('name')
    return render(request, 'authentication/district_list.html', {'districts': districts})

@login_required
def role_delete(request, pk):
    if not request.user.is_superuser:
        messages.error(request, 'Permission denied')
        return redirect('authentication:dashboard')
    role = get_object_or_404(Role, pk=pk)
    if request.method == 'POST':
        role.delete()
        messages.success(request, 'Role deleted successfully.')
    return redirect('authentication:role_list')

@login_required
def service_code_delete(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    sc = get_object_or_404(ServiceCode, pk=pk)
    if request.method == 'POST':
        sc.delete()
        messages.success(request, 'Service Code deleted.')
    return redirect('authentication:service_code_list')

@login_required
def service_code_edit(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    sc = get_object_or_404(ServiceCode, pk=pk)
    if request.method == 'POST':
        sc.code = request.POST.get('code')
        sc.description = request.POST.get('description')
        project_id = request.POST.get('project_id')
        sc.project_id = project_id if project_id else None
        sc.save()
        messages.success(request, 'Service Code updated.')
        return redirect('authentication:service_code_list')
    projects = Project.objects.all()
    return render(request, 'authentication/service_code_edit.html', {'service_code': sc, 'projects': projects})

@login_required
def vehicle_delete(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.delete()
        messages.success(request, 'Vehicle deleted.')
    return redirect('authentication:vehicle_list')

@login_required
def vehicle_edit(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    vehicle = get_object_or_404(Vehicle, pk=pk)
    if request.method == 'POST':
        vehicle.registration_number = request.POST.get('registration_number')
        vehicle.model_name = request.POST.get('model_name')
        new_service_code_id = request.POST.get('service_code')
        district_id = request.POST.get('district_id')
        project_id = request.POST.get('project_id')
        from authentication.models import VehicleLocationHistory
        new_lat = request.POST.get('latitude')
        new_lng = request.POST.get('longitude')
        vehicle.district_id = district_id
        vehicle.project_id = project_id if project_id else None
        vehicle.mandal_id = request.POST.get('mandal_id')
        old_service_code = vehicle.service_code
        new_service_code = None
        if new_service_code_id:
             new_service_code = get_object_or_404(ServiceCode, id=new_service_code_id)
        location_changed = (str(vehicle.latitude) != str(new_lat)) or (str(vehicle.longitude) != str(new_lng))
        if new_lat and new_lng:
            vehicle.latitude = float(new_lat)
            vehicle.longitude = float(new_lng)
            if old_service_code != new_service_code or location_changed:
                VehicleLocationHistory.objects.create(
                    vehicle=vehicle,
                    service_code=new_service_code,
                    latitude=vehicle.latitude,
                    longitude=vehicle.longitude,
                    updated_by=request.user
                )
        if old_service_code != new_service_code:
            if old_service_code:
                ServiceCodeHistory.objects.create(
                    service_code=old_service_code,
                    vehicle=vehicle,
                    action='unassigned'
                )
            if new_service_code:
                already_assigned = Vehicle.objects.filter(service_code=new_service_code).exclude(pk=vehicle.pk).exists()
                if already_assigned:
                    messages.error(request, f"Service Code {new_service_code.code} is already assigned to another vehicle.")
                    return redirect('authentication:vehicle_list')
                vehicle.service_code = new_service_code
                ServiceCodeHistory.objects.create(
                    service_code=new_service_code,
                    vehicle=vehicle,
                    action='assigned'
                )
            else:
                vehicle.service_code = None
        vehicle.save()
        messages.success(request, 'Vehicle updated.')
        return redirect('authentication:vehicle_list')
    return redirect('authentication:vehicle_list')

@login_required
def district_delete(request, pk):
    if not request.user.is_superuser:
         return redirect('authentication:dashboard')
    district = get_object_or_404(District, pk=pk)
    if request.method == 'POST':
        district.delete()
        messages.success(request, 'District deleted.')
    return redirect('authentication:district_list')

from django.http import JsonResponse
@login_required
def service_code_history_api(request, pk):
    sc = get_object_or_404(ServiceCode, pk=pk)
    history = sc.history.all().order_by('-timestamp')[:5]
    data = []
    for h in history:
        data.append({
            'vehicle': h.vehicle.registration_number,
            'timestamp': h.timestamp.isoformat(),
            'action': h.action
        })
    return JsonResponse({'history': data})

@login_required
def vehicle_location_history_api(request, pk):
    from .models import VehicleLocationHistory
    vehicle = get_object_or_404(Vehicle, pk=pk)
    history = vehicle.location_history.all().select_related('service_code', 'updated_by')[:5]
    data = []
    for h in history:
        data.append({
            'latitude': h.latitude,
            'longitude': h.longitude,
            'service_code': h.service_code.code if h.service_code else 'N/A',
            'timestamp': h.timestamp.isoformat(),
            'updated_by': h.updated_by.username if h.updated_by else 'System'
        })
    return JsonResponse({'history': data})

@login_required
@require_POST
def mark_notification_read(request, notification_id):
    try:
        notification = Notification.objects.get(id=notification_id, recipient=request.user)
        notification.is_read = True
        notification.save()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'}, status=404)

@login_required
@require_POST
def mark_all_read(request):
    Notification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'status': 'success'})

from .models import LoginRecord
from django.core.paginator import Paginator

@login_required
def login_audit_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('authentication:dashboard')
    
    records_list = LoginRecord.objects.all().select_related('user')
    paginator = Paginator(records_list, 15)
    page_number = request.GET.get('page')
    records = paginator.get_page(page_number)
    
    return render(request, 'authentication/login_audit.html', {'records': records})

from .models import APIKey, APIKeyHistory
import secrets
from django.views.decorators.csrf import csrf_exempt

@login_required
def api_management_view(request):
    if not request.user.is_superuser:
        messages.error(request, 'Access denied. Superuser only.')
        return redirect('authentication:dashboard')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'create':
            name = request.POST.get('name')
            project_id = request.POST.get('project')
            project = Project.objects.filter(id=project_id).first() if project_id else None
            
            api_key = APIKey.objects.create(
                name=name,
                project=project,
                created_by=request.user
            )
            APIKeyHistory.objects.create(
                api_key=api_key,
                action='created',
                performed_by=request.user
            )
            messages.success(request, f'API Key "{name}" generated successfully. The token is: {api_key.key}')
        elif action == 'revoke':
            key_id = request.POST.get('key_id')
            api_key = get_object_or_404(APIKey, id=key_id)
            api_key.is_active = False
            api_key.save()
            APIKeyHistory.objects.create(
                api_key=api_key,
                action='revoked',
                performed_by=request.user
            )
            messages.success(request, f'API Key "{api_key.name}" revoked successfully.')
        elif action == 'share':
             key_id = request.POST.get('key_id')
             shared_with = request.POST.get('shared_with')
             api_key = get_object_or_404(APIKey, id=key_id)
             APIKeyHistory.objects.create(
                  api_key=api_key,
                  action='shared',
                  performed_by=request.user,
                  shared_with=shared_with
             )
             messages.success(request, f'API Key shared with {shared_with} recorded successfully.')
        
        return redirect('authentication:api_management')
        
    keys = APIKey.objects.all().order_by('-created_at')
    projects = Project.objects.all()
    history = APIKeyHistory.objects.all().select_related('api_key', 'performed_by').order_by('-timestamp')[:50]
    
    return render(request, 'authentication/api_management.html', {
        'api_keys': keys,
        'projects': projects,
        'history': history,
        'host_url': request.build_absolute_uri('/')[:-1]
    })


@csrf_exempt
def data_export_api(request):
    auth_header = request.headers.get('Authorization')
    token = request.GET.get('api_key')
    
    if auth_header and auth_header.startswith('Api-Key '):
        token = auth_header.split(' ')[1]
        
    if not token:
        return JsonResponse({'error': 'Authentication credentials were not provided.'}, status=401)
        
    api_key = APIKey.objects.filter(key=token, is_active=True).first()
    if not api_key:
        return JsonResponse({'error': 'Invalid or inactive API Key.'}, status=401)
        
    api_key.last_used_at = timezone.now()
    api_key.save(update_fields=['last_used_at'])
    
    data = {
         'inspections': {
              'ops_104': [],
              'ops_108': [],
              'erc_104': []
         }
    }
    
    project_filter = api_key.project
    
    # 104 Ops
    if not project_filter or '104' in project_filter.name.lower():
        from ops_104.models import OpsInspection as Ops104Insp
        qs = Ops104Insp.objects.all().select_related('vehicle', 'inspector').prefetch_related('answers', 'answers__question', 'complaints', 'complaints__category', 'complaints__question')
        res = []
        for insp in qs:
             complaints_data = []
             for c in insp.complaints.all():
                 complaints_data.append({
                     'id': c.id,
                     'tracking_id': c.tracking_id,
                     'category': c.category.name,
                     'question': c.question.text if c.question else None,
                     'status': c.status,
                     'description': c.description,
                     'created_at': c.created_at.isoformat(),
                     'resolved_at': c.resolved_at.isoformat() if c.resolved_at else None,
                     'closed_at': c.closed_at.isoformat() if c.closed_at else None
                 })
                 
             answers_data = []
             for a in insp.answers.all():
                 answers_data.append({
                     'question': a.question.text,
                     'response': a.response,
                     'remarks': a.remarks
                 })

             res.append({
                 'id': insp.id,
                 'vehicle': insp.vehicle.registration_number,
                 'inspector': insp.inspector.username,
                 'created_at': insp.created_at.isoformat(),
                 'status': insp.overall_status,
                 'answers': answers_data,
                 'complaints': complaints_data,
             })
        data['inspections']['ops_104'] = res
        
    # 108 Ops
    if not project_filter or '108' in project_filter.name.lower():
        from ops_108.models import OpsInspection as Ops108Insp
        qs = Ops108Insp.objects.all().select_related('vehicle', 'inspector').prefetch_related('answers', 'answers__question', 'complaints', 'complaints__category', 'complaints__question')
        res = []
        for insp in qs:
             complaints_data = []
             for c in insp.complaints.all():
                 complaints_data.append({
                     'id': c.id,
                     'tracking_id': c.tracking_id,
                     'category': c.category.name,
                     'question': c.question.text if c.question else None,
                     'status': c.status,
                     'description': c.description,
                     'created_at': c.created_at.isoformat(),
                     'resolved_at': c.resolved_at.isoformat() if c.resolved_at else None,
                     'closed_at': c.closed_at.isoformat() if c.closed_at else None
                 })
                 
             answers_data = []
             for a in insp.answers.all():
                 answers_data.append({
                     'question': a.question.text,
                     'response': a.response,
                     'remarks': a.remarks
                 })

             res.append({
                 'id': insp.id,
                 'vehicle': insp.vehicle.registration_number,
                 'inspector': insp.inspector.username,
                 'created_at': insp.created_at.isoformat(),
                 'status': insp.overall_status,
                 'answers': answers_data,
                 'complaints': complaints_data,
             })
        data['inspections']['ops_108'] = res
        
    # ERC 104
    if not project_filter or 'erc' in project_filter.name.lower():
        from erc_104.models import ERCInspection
        qs = ERCInspection.objects.all().select_related('center', 'inspector').prefetch_related('responses', 'responses__item')
        res = []
        for insp in qs:
             responses_data = []
             for r in insp.responses.all():
                 responses_data.append({
                     'item': r.item.text,
                     'response': r.response,
                     'remarks': r.remarks
                 })
                 
             res.append({
                 'id': insp.id,
                 'center': insp.center.name,
                 'inspector': insp.inspector.username,
                 'created_at': insp.created_at.isoformat(),
                 'status': insp.overall_status,
                 'responses': responses_data,
             })
        data['inspections']['erc_104'] = res
        
    return JsonResponse(data)
