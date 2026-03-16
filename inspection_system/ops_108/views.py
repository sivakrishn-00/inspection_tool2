from django.shortcuts import render, redirect, get_object_or_404
from django.db import models
from django.contrib.auth.decorators import login_required
from authentication.models import Project, Inspection, Vehicle, ServiceCode, District, Notification
from .models import OpsInspection, InspectionCategory, InspectionAnswer, InspectionQuestion, Complaint
from django.utils import timezone
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User

@login_required
def dashboard(request):
    project = None
    profile = getattr(request.user, 'profile', None)
    if request.user.is_superuser:
        project = Project.objects.filter(name__icontains='108').first()
    else:
        try:
            project = profile.assigned_project if profile else None
        except:
            pass
    if not project and not request.user.is_superuser:
        return render(request, 'no_project.html')
    if request.user.is_superuser:
        if project:
            allowed_vehicles = Vehicle.objects.filter(project=project)
        else:
            allowed_vehicles = Vehicle.objects.all()
        inspections_qs = OpsInspection.objects.all().select_related('vehicle', 'inspector').order_by('-created_at')
        stats_qs = OpsInspection.objects.all()
    else:
        from authentication.models import ServiceCode
        allowed_service_codes = ServiceCode.objects.none()
        if profile.role:
            allowed_service_codes |= profile.role.service_codes.all()
        if profile.assigned_service_codes.exists():
            allowed_service_codes |= profile.assigned_service_codes.all()
        allowed_service_codes = allowed_service_codes.distinct()
        if project:
            allowed_service_codes = allowed_service_codes.filter(project=project)
            
        if allowed_service_codes.exists():
            allowed_vehicles = Vehicle.objects.filter(service_code__in=allowed_service_codes, project=project)
            # Personal list for table k
            inspections_qs = OpsInspection.objects.filter(
                vehicle__service_code__in=allowed_service_codes,
                inspector=request.user
            ).select_related('vehicle', 'inspector').order_by('-created_at')
            
            # Aggregate scope for KPI cards (dynamic oversight) k
            stats_qs = OpsInspection.objects.filter(
                vehicle__service_code__in=allowed_service_codes
            )
        else:
            allowed_vehicles = Vehicle.objects.none()
            inspections_qs = OpsInspection.objects.none()
            stats_qs = OpsInspection.objects.none()
    # Detect complaint roles
    user_role_name = (profile.role.name.lower() if profile and profile.role else '').strip()
    is_manager = user_role_name == 'manager'
    is_subordinate = user_role_name == 'subordinate'
    is_complaint_role = is_manager or is_subordinate
    
    # Calculate relevant stats
    today = timezone.localdate()
    total_vehicles = allowed_vehicles.count()
    total_inspections = inspections_qs.count()
    negative_responses = ['false', 'poor', 'not_operational', 'not_maintained', 'not_available', 'available_not_working']
    
    # Base complaint query for stats
    if is_manager:
        complaint_stats_qs = Complaint.objects.filter(category_manager=request.user)
    elif is_subordinate:
        complaint_stats_qs = Complaint.objects.filter(assignee=request.user)
    else:
        # User Specific k: show activity for THEIR inspections only in stats k
        complaint_stats_qs = Complaint.objects.filter(inspection__in=inspections_qs)

    comp_total = complaint_stats_qs.count()
    comp_resolved = complaint_stats_qs.filter(status='resolved').count()
    comp_pending = complaint_stats_qs.filter(status='raised').count()
    comp_closed = complaint_stats_qs.filter(status='closed').count()

    recent_inspections = inspections_qs.select_related('vehicle', 'inspector').prefetch_related('complaints__category')[:10]
    for inspection in recent_inspections:
        complaints = []
        complaint_statuses = set()
        for c in inspection.complaints.all():
            status_text = c.status.title()
            complaints.append(f"{c.category.name}: {status_text}")
            complaint_statuses.add(c.status)
        
        inspection.complaints_list = complaints
        
        # Determine overall display status based on complaints
        if not complaints:
            inspection.display_status = inspection.overall_status.title()
        elif 'raised' in complaint_statuses:
            inspection.display_status = 'Raised'
        elif 'resolved' in complaint_statuses:
            inspection.display_status = 'Resolved'
        else:
            inspection.display_status = 'Closed'
    
    map_data = []
    # ... (omit map data for complaint roles if not needed, but keeping for now)
    vehicles_with_loc = allowed_vehicles.select_related('district', 'service_code')
    for v in vehicles_with_loc:
        lat = v.latitude
        lng = v.longitude
        if not lat or not lng:
            if v.district and v.district.latitude and v.district.longitude:
                import random
                lat = v.district.latitude + (random.random() - 0.5) * 0.01
                lng = v.district.longitude + (random.random() - 0.5) * 0.01
        if lat and lng:
            map_data.append({
                'registration_number': v.registration_number,
                'lat': lat,
                'lng': lng,
                'service_code': v.service_code.code if v.service_code else 'N/A'
            })
            
    # Recent complaints for focused roles
    recent_complaints = complaint_stats_qs.select_related('category', 'inspection__vehicle').order_by('-created_at')[:5]

    context = {
        'page_title': f'{project.name if project else "All Operations"} Dashboard',
        'project_name': project.name if project else "All Operations",
        'user_role': profile.role.name if not request.user.is_superuser and profile.role else 'Administrator',
        'is_complaint_role': is_complaint_role,
        'stats': {
            'total_vehicles': total_vehicles,
            'total_inspections': total_inspections,
            'comp_total': comp_total,
            'comp_resolved': comp_resolved,
            'comp_pending': comp_pending,
            'comp_closed': comp_closed,
        },
        'recent_inspections': recent_inspections,
        'recent_complaints': recent_complaints,
        'map_data': map_data
    }
    return render(request, 'ops_108/dashboard.html', context)

@login_required
def perform_inspection(request):
    profile = getattr(request.user, 'profile', None)
    vehicle = None
    allowed_service_codes = ServiceCode.objects.none()
    if profile:
        if profile.assigned_service_codes.exists():
            allowed_service_codes = profile.assigned_service_codes.all()
        elif profile.role:
            allowed_service_codes = profile.role.service_codes.all()
    allowed_service_codes = allowed_service_codes.distinct()
    if getattr(profile, 'assigned_project', None):
        allowed_service_codes = allowed_service_codes.filter(project=profile.assigned_project)
        
    available_vehicles = Vehicle.objects.none()
    if allowed_service_codes.exists():
        available_vehicles = Vehicle.objects.filter(
            service_code__in=allowed_service_codes, 
            project=profile.assigned_project
        ).select_related('district', 'service_code')
    elif request.user.is_superuser:
        project = Project.objects.filter(name__icontains='108').first()
        if project:
            available_vehicles = Vehicle.objects.filter(project=project).select_related('district', 'service_code')
        else:
            available_vehicles = Vehicle.objects.all().select_related('district', 'service_code')
    v_id = request.GET.get('vehicle_id') or request.POST.get('vehicle_id')
    vehicle = None
    if v_id:
        try:
            vehicle = available_vehicles.get(id=v_id)
        except (Vehicle.DoesNotExist, ValueError):
            vehicle = None
    is_readonly = False
    last_inspection = None
    next_allowed_date = None
    question_responses = {}
    active_complaints = Complaint.objects.none()
    
    if profile and profile.role:
        user_role = profile.role.name.strip().lower()
        if user_role in ['manager', 'subordinate']:
            messages.error(request, "Managers and subordinates do not perform inspections.")
            return redirect('ops_108:dashboard')

    if vehicle and not request.user.is_superuser and profile and profile.role:
        user_role = profile.role.name.strip().lower()
        
        # Check if any complaints are currently active for this vehicle (Raised, Assigned, or Resolved)
        all_active = Complaint.objects.filter(
            inspection__vehicle=vehicle
        ).exclude(status='closed').order_by('-inspection__created_at')
        
        # Determine read-only status based on role and active complaints
        if all_active.exists():
            if user_role == 'inspection':
                now = timezone.now()
                # Re-sort explicitly by complaint's own created_at field to get the absolute newest first
                for c in all_active.order_by('-created_at'):
                    key = f"q_{c.question_id}" if c.question_id else f"c_{c.category_id}"
                    if key not in seen_items:
                        seen_items.add(key)
                        
                        # Apply automatic 24-hour spoofing strictly for inspection role
                        c.display_created_at = c.created_at
                        raiser_role = (c.inspection.inspector.profile.role.name.lower() if hasattr(c.inspection.inspector, 'profile') and c.inspection.inspector.profile.role else '').strip()
                        if raiser_role != 'inspection' and (now - c.created_at).total_seconds() > 86400:
                            c.display_created_at = now - timezone.timedelta(hours=24)
                            
                        active_list.append(c)
                active_complaints = active_list
                is_readonly = False
            else:
                # other roles dont show at all k active complaints history
                active_complaints = Complaint.objects.none()
                is_readonly = True
                last_inspection = all_active.first().inspection
                answers = InspectionAnswer.objects.filter(inspection=last_inspection)
                question_responses = {ans.question_id: ans for ans in answers}
        
        all_active_count = all_active.count()
            
        if not is_readonly:
            deadline_days = profile.role.inspection_deadline_days
            last_inspection = OpsInspection.objects.filter(
                inspector=request.user,
                vehicle=vehicle
            ).order_by('-created_at').first()
            if last_inspection:
                # Handle calendar-day based daily option for inspection role
                if user_role == 'inspection' and deadline_days == 1:
                    last_date = timezone.localtime(last_inspection.created_at).date()
                    today = timezone.localdate()
                    if last_date == today:
                        is_readonly = True
                        next_allowed_date = today + timezone.timedelta(days=1)
                else:
                    cutoff_date = last_inspection.created_at + timezone.timedelta(days=deadline_days)
                    if timezone.now() < cutoff_date:
                        is_readonly = True
                        next_allowed_date = cutoff_date
                
                if is_readonly:
                    answers = InspectionAnswer.objects.filter(inspection=last_inspection)
                    question_responses = {ans.question_id: ans for ans in answers}

    if request.method == 'POST':
        if not vehicle:
            messages.error(request, "Vehicle must be selected.")
            return redirect('ops_108:inspection')

    if is_readonly and request.method == 'POST':
        messages.error(request, f"Inspection limit reached. Next inspection allowed after {next_allowed_date.strftime('%b %d, %Y')}.")
        return redirect('ops_108:inspection')

    if request.method == 'POST':
        if not vehicle:
            messages.error(request, "Vehicle must be selected.")
            return redirect('ops_108:inspection')
            
        questions = InspectionQuestion.objects.filter(is_active=True).select_related('category', 'category__manager')
        negative_responses = ['false', 'poor', 'not_operational', 'not_maintained', 'not_available', 'available_not_working']
        
        category_failures = {} # cat_id -> data
        responses_to_save = []
        
        for q in questions:
            response = request.POST.get(f'response_{q.id}')
            remarks = request.POST.get(f'remarks_{q.id}')
            photo = request.FILES.get(f'photo_{q.id}')
            
            if response:
                responses_to_save.append((q, response, remarks, photo))
                if response in negative_responses:
                    cat_id = q.category.id
                    if cat_id not in category_failures:
                        category_failures[cat_id] = {
                            'remarks': [],
                            'photos': [],
                            'category': q.category
                        }
                    category_failures[cat_id]['remarks'].append(f"{q.text}: {remarks or 'No remarks'}")
                    if photo:
                        category_failures[cat_id]['photos'].append(photo)

        # Granular block specifically for 'inspection' role
        # BLOCKING logic: An item ONLY blocks if it was raised by another inspector 
        # OR it was raised by another role (Admin/RM/etc) within the ACTUAL last 24 hours.
        now = timezone.now()
        active_items = Complaint.objects.filter(
            inspection__vehicle=vehicle,
            question__isnull=False
        ).exclude(status='closed').select_related('inspection__inspector__profile__role')
        
        blocking_ids = []
        persistent_ids = [] # To track old complaints from other roles for the notification
        
        user_role = (profile.role.name.lower() if profile and profile.role else '').strip()
        
        if user_role == 'inspection':
            for c in active_items:
                raiser_role = (c.inspection.inspector.profile.role.name.lower() if hasattr(c.inspection.inspector, 'profile') and c.inspection.inspector.profile.role else '').strip()
                if raiser_role == 'inspection' or (now - c.created_at).total_seconds() <= 86400:
                    blocking_ids.append(c.question_id)
                else:
                    persistent_ids.append(c.question_id)
            active_item_ids = blocking_ids
        else:
            active_item_ids = list(active_items.values_list('question_id', flat=True))

        # Create inspection and save answers
        inspection = OpsInspection.objects.create(
            vehicle=vehicle,
            inspector=request.user,
            district=vehicle.district,
            overall_status='Submitted'
        )
        for q, resp, rem, ph in responses_to_save:
            InspectionAnswer.objects.create(
                inspection=inspection,
                question=q,
                response=resp,
                remarks=rem,
                photo=ph
            )

        # Create individual item complaints
        newly_raised = []
        already_active = []
        for q, resp, rem, ph in responses_to_save:
            if resp in negative_responses:
                # If item is already active, non-admins skip. Admins create a SEPARATE record to maintain audit trail.
                is_currently_active = q.id in active_item_ids
                if is_currently_active and not request.user.is_superuser:
                    already_active.append(q.text)
                    continue
                
                timestamp = timezone.localtime(timezone.now()).strftime('%Y%m%d%H%M%S')
                tracking_id = f"CMP-{vehicle.registration_number}-{timestamp}-{q.id}"
                
                is_re_raised = (user_role == 'inspection' and q.id in persistent_ids)
                Complaint.objects.create(
                    inspection=inspection,
                    question=q,
                    category=q.category,
                    category_manager=q.category.manager,
                    tracking_id=tracking_id,
                    status='raised',
                    is_remarked=is_re_raised,
                    description=rem or f"Failure reported for {q.text}",
                    inspector_photo=ph,
                    created_by=request.user,
                    item_name=q.text
                )

                # Notify Manager
                if q.category.manager:
                    is_re_raised = (user_role == 'inspection' and q.id in persistent_ids)
                    title = f"New Complaint: {q.text}" if not is_re_raised else f"RE-RAISED Complaint: {q.text}"
                    Notification.objects.create(
                        recipient=q.category.manager,
                        project=vehicle.project,
                        title=title,
                        message=f"A complaint has been {'re-' if is_re_raised else ''}raised for vehicle {vehicle.registration_number} ({q.category.name}). Tracking ID: {tracking_id}",
                        type='alert',
                        link=f"/ops-108/complaints/"
                    )

                # Notify Inspector as confirmation
                Notification.objects.create(
                    recipient=request.user,
                    project=vehicle.project,
                    title=f"Complaint Recorded: {q.text}",
                    message=f"You successfully recorded a complaint for {vehicle.registration_number}. Tracking ID: {tracking_id}",
                    type='success',
                    link=f"/ops-108/complaints/"
                )

                newly_raised.append(q.text)
                if is_currently_active:
                    already_active.append(q.text)
                elif user_role == 'inspection' and q.id in persistent_ids:
                    # Specific requirement: re-raising an old complaint from another role
                    messages.info(request, f"Already raised this complaint for '{q.text}' by another person, but we are marking it again for this audit.")

        if not newly_raised and not already_active:
            messages.success(request, "Inspection submitted successfully. All components are in good condition.")
        else:
            if newly_raised:
                messages.success(request, f"Inspection submitted successfully. New complaints raised for: {', '.join(newly_raised)}.")
            else:
                messages.success(request, "Inspection submitted successfully.")

            if already_active:
                # Prioritize Admin complaint for the skip note
                admin_skipped = Complaint.objects.filter(
                    inspection__vehicle=vehicle,
                    question__text__in=already_active,
                    inspection__inspector__is_superuser=True
                ).exclude(status='closed').order_by('-inspection__created_at').first()
                
                latest_skipped = admin_skipped if admin_skipped else Complaint.objects.filter(
                    inspection__vehicle=vehicle,
                    question__text__in=already_active
                ).exclude(status='closed').order_by('-inspection__created_at').first()
                
                if latest_skipped:
                    skipped_label = latest_skipped.question.text if latest_skipped.question else latest_skipped.category.name
                    tracking_id_text = f" ({latest_skipped.tracking_id})"
                    messages.warning(request, f"Please note: '{skipped_label}' or other items were already reported recently{tracking_id_text}. Your report has been noted under the existing complaints, acknowledging you also reported them.")

        return redirect('ops_108:dashboard')
    categories = []
    if vehicle:
        categories_qs = InspectionCategory.objects.filter(is_active=True).prefetch_related('questions').order_by('order')
        categories = list(categories_qs)
        if is_readonly:
            for cat in categories:
                for q in cat.questions.all():
                    if q.id in question_responses:
                        q.existing_response = question_responses[q.id]
        ICON_DEFS = {
            'default': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle></svg>',
            'truck': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="3" width="15" height="13"></rect><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"></polygon><circle cx="5.5" cy="18.5" r="2.5"></circle><circle cx="18.5" cy="18.5" r="2.5"></circle></svg>',
            'heart': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 14c1.49-1.46 3-3.21 3-5.5A5.5 5.5 0 0 0 16.5 3c-1.76 0-3 .5 4.5 2-1.5 1.5-2.74 3-4.22 3-6.5A5.5 5.5 0 0 0 2 8.5c0 2.3 1.5 4.05 3 5.5l7 7Z"></path></svg>',
            'computer': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="8" y1="21" x2="16" y2="21"></line><line x1="12" y1="17" x2="12" y2="21"></line></svg>',
            'clipboard': '<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"></path><rect x="8" y="2" width="8" height="4" rx="1" ry="1"></rect></svg>',
            'smartphone': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="5" y="2" width="14" height="20" rx="2" ry="2"></rect><line x1="12" y1="18" x2="12.01" y2="18"></line></svg>',
            'laptop': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="3" width="20" height="14" rx="2" ry="2"></rect><line x1="2" y1="20" x2="22" y2="20"></line></svg>',
            'cpu': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#6366f1" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="4" width="16" height="16" rx="2" ry="2"></rect><rect x="9" y="9" width="6" height="6"></rect><line x1="9" y1="1" x2="9" y2="4"></line><line x1="15" y1="1" x2="15" y2="4"></line><line x1="9" y1="20" x2="9" y2="23"></line><line x1="15" y1="20" x2="15" y2="23"></line><line x1="20" y1="9" x2="23" y2="9"></line><line x1="20" y1="14" x2="23" y2="14"></line><line x1="1" y1="9" x2="4" y2="9"></line><line x1="1" y1="14" x2="4" y2="14"></line></svg>',
            'zap': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fbbf24" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon></svg>',
            'flask': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 2v7.31"></path><path d="M14 2v7.31"></path><path d="M8.5 2h7"></path><path d="M14 9.3a6.5 6.5 0 1 1-4 0V2"></path></svg>',
            'activity': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"></polyline></svg>',
            'flame': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#f97316" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.1.2-2.2.5-3.3a9 9 0 0 0 3 3.3z"></path></svg>',
            'droplet': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2.69l5.74 5.74a8 8 0 1 1-11.31 0z"></path></svg>',
            'thermometer': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 14.76V3.5a2.5 2.5 0 0 0-5 0v11.26a4.5 4.5 0 1 0 5 0z"></path></svg>',
            'wind': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.59 4.59A2 2 0 1 1 11 8H2m10.59 11.41A2 2 0 1 0 14 16H2m15.73-8.27A2.5 2.5 0 1 1 19.5 12H2"></path></svg>',
            'scissors': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#64748b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="6" cy="6" r="3"></circle><circle cx="6" cy="18" r="3"></circle><line x1="20" y1="4" x2="8.12" y2="15.88"></line><line x1="14.47" y1="14.48" x2="20" y2="20"></line><line x1="8.12" y1="8.12" x2="12" y2="12"></line></svg>',
            'box': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#a855f7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>',
            'map': '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="3 6 9 3 15 6 21 3 21 18 15 21 9 18 3 21 3 6"></polygon><line x1="9" y1="3" x2="9" y2="18"></line><line x1="15" y1="6" x2="15" y2="21"></line></svg>',
        }
        for cat in categories:
            cat.icon = ICON_DEFS['default']
            cn = cat.name.lower()
            if 'vehicle' in cn: cat.icon = ICON_DEFS['truck']
            elif 'emergency' in cn: cat.icon = ICON_DEFS['heart']
            elif 'it ' in cn: cat.icon = ICON_DEFS['computer']
            elif 'document' in cn: cat.icon = ICON_DEFS['clipboard']
            for q in cat.questions.all():
                q.icon = ICON_DEFS['default']
                txt = q.text.lower()
                if 'cardiac' in txt or 'monitor' in txt or 'ecg' in txt: q.icon = ICON_DEFS['activity']
                elif 'oxygen' in txt or 'flow' in txt: q.icon = ICON_DEFS['wind']
                elif 'cylinder' in txt: q.icon = ICON_DEFS['wind']
                elif 'mobile' in txt or 'phone' in txt: q.icon = ICON_DEFS['smartphone']
                elif 'laptop' in txt or 'tab' in txt: q.icon = ICON_DEFS['laptop']
                elif 'gps' in txt: q.icon = ICON_DEFS['map']
                elif 'inverter' in txt or 'battery' in txt or 'power' in txt: q.icon = ICON_DEFS['zap']
                elif 'analysis' in txt or 'analyser' in txt or 'biochem' in txt: q.icon = ICON_DEFS['cpu']
                elif 'microscope' in txt or 'scope' in txt or 'torch' in txt: q.icon = ICON_DEFS['flask']
                elif 'fire' in txt: q.icon = ICON_DEFS['flame']
                elif 'blood' in txt or 'glucom' in txt or 'hemo' in txt: q.icon = ICON_DEFS['droplet']
                elif 'thermometer' in txt or 'temp' in txt: q.icon = ICON_DEFS['thermometer']
                elif 'scissor' in txt or 'cutter' in txt: q.icon = ICON_DEFS['scissors']
                elif 'bin' in txt or 'tray' in txt or 'box' in txt or 'kit' in txt: q.icon = ICON_DEFS['box']
                elif 'bag' in txt: q.icon = ICON_DEFS['box']
                if 'stethoscope' in txt: q.icon = ICON_DEFS['activity']
                if 'incuba' in txt: q.icon = ICON_DEFS['box']
    context = {
        'categories': categories,
        'vehicle': vehicle,
        'available_vehicles': available_vehicles,
        'today_date': timezone.localdate(),
        'is_readonly': is_readonly,
        'last_inspection': last_inspection,
        'next_allowed_date': next_allowed_date,
        'active_complaints': active_complaints,
        'user_role': profile.role.name.strip().lower() if profile and profile.role else None,
        'all_active_count': all_active_count if 'all_active_count' in locals() else 0
    }
    return render(request, 'ops_108/inspection_form.html', context)

@login_required
def manage_checklist(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('ops_108:dashboard')
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add_category':
            name = request.POST.get('name')
            if name:
                from django.utils.text import slugify
                base_slug = slugify(name)
                slug = base_slug
                counter = 1
                while InspectionCategory.objects.filter(slug=slug).exists():
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                
                last_order = InspectionCategory.objects.aggregate(models.Max('order'))['order__max'] or 0
                InspectionCategory.objects.create(
                    name=name,
                    slug=slug,
                    order=last_order + 1
                )
                messages.success(request, "Category added successfully.")
            else:
                 messages.error(request, "Category name is required.")
        elif action == 'edit_category':
            cat_id = request.POST.get('category_id')
            name = request.POST.get('name')
            if cat_id and name:
                cat = get_object_or_404(InspectionCategory, id=cat_id)
                cat.name = name
                cat.save()
                messages.success(request, "Category updated successfully.")
            else:
                 messages.error(request, "Missing required fields.")
        elif action == 'delete_category':
            cat_id = request.POST.get('category_id')
            if cat_id:
                cat = get_object_or_404(InspectionCategory, id=cat_id)
                cat.is_active = False
                cat.save()
                messages.success(request, "Category removed successfully.")
        elif action == 'add':
            cat_id = request.POST.get('category')
            text = request.POST.get('text')
            q_type = request.POST.get('type')
            if cat_id and text and q_type:
                category = get_object_or_404(InspectionCategory, id=cat_id)
                last_order = InspectionQuestion.objects.filter(category=category).aggregate(models.Max('order'))['order__max'] or 0
                InspectionQuestion.objects.create(
                    category=category,
                    text=text,
                    question_type=q_type,
                    order=last_order + 1,
                    is_active=True
                )
                messages.success(request, "Item added successfully.")
            else:
                 messages.error(request, "Missing required fields.")
        elif action == 'delete':
            q_id = request.POST.get('question_id')
            if q_id:
                q = get_object_or_404(InspectionQuestion, id=q_id)
                q.is_active = False
                q.save()
                messages.success(request, "Item removed (deactivated).")
        elif action == 'update_manager':
            cat_id = request.POST.get('category_id')
            manager_id = request.POST.get('manager_id')
            if cat_id:
                cat = get_object_or_404(InspectionCategory, id=cat_id)
                cat.manager_id = manager_id if manager_id else None
                cat.save()
                messages.success(request, f"Manager updated for {cat.name}.")
        return redirect('ops_108:manage_checklist')
    categories = InspectionCategory.objects.filter(is_active=True).prefetch_related(
        models.Prefetch('questions', queryset=InspectionQuestion.objects.filter(is_active=True).order_by('order'))
    ).select_related('manager').order_by('order')
    question_types = InspectionQuestion.QUESTION_TYPES
    
    # Ensure roles exist and filter users for category management
    from authentication.models import Role
    manager_role, _ = Role.objects.get_or_create(name='manager')
    Role.objects.get_or_create(name='subordinate') # Ensure subordinate role exists
    Role.objects.get_or_create(name='inspection') # Ensure inspection role exists
    
    all_users = User.objects.filter(profile__role=manager_role).order_by('username')
    
    context = {
        'categories': categories,
        'question_types': question_types,
        'all_users': all_users
    }
    return render(request, 'ops_108/manage_checklist.html', context)

@login_required
def complaint_list(request):
    user = request.user
    
    # Manager view: All complaints in categories they manage
    managed_complaints = Complaint.objects.filter(category_manager=user).order_by('-status', '-created_at')
    
    # Subordinate view: Complaints in categories managed by their supervisor
    assigned_complaints = Complaint.objects.none()
    if hasattr(user, 'profile') and user.profile.supervisor:
        supervisor_user = user.profile.supervisor.user
        assigned_complaints = Complaint.objects.filter(category_manager=supervisor_user)

    # Inspector view: Complaints raised from their inspections
    my_raised_complaints = Complaint.objects.filter(inspection__inspector=user).order_by('-created_at')
    
    context = {
        'managed_complaints': managed_complaints,
        'assigned_complaints': assigned_complaints,
        'my_raised_complaints': my_raised_complaints,
    }
    return render(request, 'ops_108/complaint_list.html', context)


@login_required
@require_POST
def resolve_complaint(request, complaint_id):
    profile = getattr(request.user, 'profile', None)
    if profile and profile.supervisor:
        # Subordinate: can resolve if their supervisor manages the category
        supervisor_user = profile.supervisor.user
        complaint = get_object_or_404(Complaint, id=complaint_id, category_manager=supervisor_user)
    elif request.user.is_superuser:
        # Admin: can resolve anything
        complaint = get_object_or_404(Complaint, id=complaint_id)
    else:
        # Manager: can resolve their own categories
        complaint = get_object_or_404(Complaint, id=complaint_id, category_manager=request.user)
    remarks = request.POST.get('remarks')
    proof = request.FILES.get('proof')
    
    if proof:
        complaint.resolution_remarks = remarks
        complaint.resolution_proof = proof
        complaint.status = 'resolved'
        complaint.resolved_at = timezone.now()
        complaint.save()
        
        # Notify Manager (if not the person resolving it)
        from authentication.models import Notification
        if complaint.category_manager and complaint.category_manager != request.user:
            Notification.objects.create(
                recipient=complaint.category_manager,
                project=complaint.inspection.vehicle.project,
                title=f"Complaint Resolved: {complaint.question.text if complaint.question else complaint.category.name}",
                message=f"A complaint for {complaint.inspection.vehicle.registration_number} has been resolved by {request.user.username}.",
                type='info',
                link=f"/ops-108/complaints/"
            )
        
        # Notify Inspector
        Notification.objects.create(
            recipient=complaint.inspection.inspector,
            project=complaint.inspection.vehicle.project,
            title=f"Complaint Resolved: {complaint.id}",
            message=f"Your complaint for {complaint.inspection.vehicle.registration_number} has been resolved.",
            type='success',
            link=f"/ops-108/complaints/"
        )
        
        messages.success(request, "Complaint marked as resolved. Waiting for manager closure.")
    else:
        messages.error(request, "Photo proof is required to resolve a complaint.")
        
    return redirect('ops_108:complaint_list')

@login_required
@require_POST
def close_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, category_manager=request.user)
    remarks = request.POST.get('remarks')
    complaint.closure_remarks = remarks
    complaint.status = 'closed'
    complaint.closed_at = timezone.now()
    complaint.save()
    
    # Notify Inspector
    from authentication.models import Notification
    Notification.objects.create(
        recipient=complaint.inspection.inspector,
        project=complaint.inspection.vehicle.project,
        title=f"Complaint Closed: {complaint.id}",
        message=f"A manager has closed the complaint for {complaint.inspection.vehicle.registration_number}.",
        type='success',
        link=f"/ops-108/complaints/"
    )
    
    messages.success(request, "Complaint closed successfully.")
    return redirect('ops_108:complaint_list')
