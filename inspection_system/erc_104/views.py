from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from authentication.models import Project
from .models import ERCInspection, ERCCenter, ERCCategory, ERCItem, ERCResponse, ERCGridSection
from django.db import models
from django.utils.text import slugify

@login_required
def manage_checklist(request):
    if not request.user.is_superuser:
        messages.error(request, "Access denied.")
        return redirect('erc_104:dashboard')

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add_category':
            name = request.POST.get('name')
            if name:
                slug = slugify(name)
                counter = 1
                while ERCCategory.objects.filter(slug=slug).exists():
                    slug = f"{slug}-{counter}"
                    counter += 1
                
                last_order = ERCCategory.objects.aggregate(models.Max('order'))['order__max'] or 0
                ERCCategory.objects.create(
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
                cat = get_object_or_404(ERCCategory, id=cat_id)
                cat.name = name
                cat.save()
                messages.success(request, "Category updated successfully.")
            else:
                 messages.error(request, "Missing required fields.")
        elif action == 'delete_category':
            cat_id = request.POST.get('category_id')
            if cat_id:
                cat = get_object_or_404(ERCCategory, id=cat_id)
                cat.is_active = False
                cat.save()
                messages.success(request, "Category removed successfully.")

        elif action == 'edit_category':
            cat_id = request.POST.get('category_id')
            name = request.POST.get('name')
            if cat_id and name:
                cat = get_object_or_404(ERCCategory, id=cat_id)
                cat.name = name
                cat.save()
                messages.success(request, "Category updated successfully.")
            else:
                 messages.error(request, "Missing required fields.")
        elif action == 'delete_category':
            cat_id = request.POST.get('category_id')
            if cat_id:
                cat = get_object_or_404(ERCCategory, id=cat_id)
                cat.is_active = False
                cat.save()
                messages.success(request, "Category removed successfully.")

        elif action == 'add':
            cat_id = request.POST.get('category')
            text = request.POST.get('text')
            item_type = request.POST.get('type')
            
            if cat_id and text and item_type:
                category = get_object_or_404(ERCCategory, id=cat_id)
                last_order = ERCItem.objects.filter(category=category).aggregate(models.Max('order'))['order__max'] or 0
                
                ERCItem.objects.create(
                    category=category,
                    text=text,
                    item_type=item_type,
                    order=last_order + 1,
                    is_active=True
                )
                messages.success(request, "Item added successfully.")
            else:
                 messages.error(request, "Missing required fields.")

        elif action == 'delete':
            item_id = request.POST.get('item_id')
            if item_id:
                item = get_object_or_404(ERCItem, id=item_id)
                item.is_active = False
                item.save()
                messages.success(request, "Item removed (deactivated).")

        elif action == 'edit':
            item_id = request.POST.get('item_id')
            cat_id = request.POST.get('category')
            text = request.POST.get('text')
            item_type = request.POST.get('type')

            if item_id and cat_id and text and item_type:
                item = get_object_or_404(ERCItem, id=item_id)
                category = get_object_or_404(ERCCategory, id=cat_id)
                
                item.category = category
                item.text = text
                item.item_type = item_type
                item.save()
                messages.success(request, "Item updated successfully.")
            else:
                 messages.error(request, "Missing required fields for update.")
        
        elif action == 'add_grid':
            name = request.POST.get('name')
            rows = request.POST.get('rows')
            cols = request.POST.get('cols')
            icon = request.POST.get('icon')
            prefix = request.POST.get('prefix')

            if name and rows and cols:
                slug = slugify(name)
                if ERCGridSection.objects.filter(slug=slug).exists():
                     slug = f"{slug}-{timezone.now().timestamp()}"

                last_order = ERCGridSection.objects.aggregate(models.Max('order'))['order__max'] or 0
                
                total_items_val = request.POST.get('total_items')
                total_items = int(total_items_val) if total_items_val else None

                ERCGridSection.objects.create(
                    name=name,
                    slug=slug,
                    rows=int(rows),
                    cols=int(cols),
                    total_items=total_items,
                    icon=icon,
                    prefix=prefix,
                    order=last_order + 1
                )
                messages.success(request, "Grid Room added successfully.")
            else:
                messages.error(request, "Missing required fields for Grid.")

        elif action == 'edit_grid':
            section_id = request.POST.get('section_id')
            name = request.POST.get('name')
            rows = request.POST.get('rows')
            cols = request.POST.get('cols')
            icon = request.POST.get('icon')
            prefix = request.POST.get('prefix')
            
            total_items_val = request.POST.get('total_items')
            total_items = int(total_items_val) if total_items_val else None

            if section_id and name and rows and cols:
                section = get_object_or_404(ERCGridSection, id=section_id)
                section.name = name
                section.rows = int(rows)
                section.cols = int(cols)
                section.total_items = total_items
                section.icon = icon
                section.prefix = prefix
                section.save()
                messages.success(request, "Grid Room updated successfully.")
            else:
                messages.error(request, "Missing required fields for update.")
        
        elif action == 'delete_grid':
            section_id = request.POST.get('section_id')
            if section_id:
                section = get_object_or_404(ERCGridSection, id=section_id)
                section.delete()
                messages.success(request, "Grid Room deleted.")

        return redirect('erc_104:manage_checklist')

    categories = ERCCategory.objects.filter(is_active=True).prefetch_related(
        models.Prefetch('items', queryset=ERCItem.objects.filter(is_active=True).order_by('order'))
    ).order_by('order')
    
    grid_sections = ERCGridSection.objects.filter(is_active=True).order_by('order')
    question_types = ERCItem.ITEM_TYPES
    icon_choices = ERCGridSection.ICON_CHOICES

    context = {
        'categories': categories,
        'grid_sections': grid_sections,
        'question_types': question_types,
        'icon_choices': icon_choices
    }
    return render(request, 'erc_104/manage_checklist.html', context)

@login_required
def dashboard(request):
    project_name = "ERC"
    if request.user.is_superuser:
        base_qs = ERCInspection.objects.all()
    else:
        profile = getattr(request.user, 'profile', None)
        if hasattr(profile, 'assigned_project') and profile.assigned_project:
             project_name = profile.assigned_project.name
        base_qs = ERCInspection.objects.filter(inspector=request.user)
    today = timezone.now().date()
    total_inspections = base_qs.count()
    inspections_today = base_qs.filter(created_at__date=today).count()
    
    recent_inspections = base_qs.select_related('center', 'inspector').order_by('-created_at')[:10]
    recent_defects = ERCResponse.objects.filter(inspection__in=base_qs).exclude(
        response__in=['good', 'true', 'available', 'good']
    ).select_related('inspection', 'inspection__center', 'item').order_by('-inspection__created_at')[:5]

    context = {
        'page_title': 'ERC Dashboard',
        'project_name': project_name,
        'stats': {
            'total_inspections': total_inspections,
            'today': inspections_today,
            'centers': ERCCenter.objects.count()
        },
        'recent_inspections': recent_inspections,
        'recent_defects': recent_defects
    }
    return render(request, 'erc_104/dashboard.html', context)

@login_required
def perform_inspection(request):
    centers = ERCCenter.objects.all()
    target_center_id = request.GET.get('center_id') or (request.POST.get('center_id') if request.method == 'POST' else None)
    
    selected_center = None
    if target_center_id:
        try:
            selected_center = ERCCenter.objects.get(id=target_center_id)
        except (ERCCenter.DoesNotExist, ValueError):
            selected_center = None
           
    is_readonly = False
    last_inspection = None
    next_allowed_date = None
    item_responses = {}
    
    profile = getattr(request.user, 'profile', None)

    if profile and profile.role:
        user_role = profile.role.name.strip().lower()
        if user_role in ['manager', 'subordinate']:
            messages.error(request, "Managers and subordinates do not perform inspections.")
            return redirect('erc_104:dashboard')
    
    if selected_center and not request.user.is_superuser and profile and profile.role:
        deadline_days = profile.role.inspection_deadline_days
        user_role = profile.role.name.strip().lower()
        last_inspection = ERCInspection.objects.filter(
            inspector=request.user,
            center=selected_center
        ).order_by('-created_at').first()

        if last_inspection:
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
                responses = ERCResponse.objects.filter(inspection=last_inspection)
                item_responses = {resp.item_id: resp for resp in responses}
    
    if is_readonly and request.method == 'POST':
        messages.error(request, f"Inspection limit reached. Next inspection allowed after {next_allowed_date.strftime('%b %d, %Y')}.")
        return redirect(f"{redirect('erc_104:inspection').url}?center_id={selected_center.id}")

    if request.method == 'POST' and selected_center:
        visual_layout_data = request.POST.get('visual_layout_data')
        inspection = ERCInspection.objects.create(
            center=selected_center,
            inspector=request.user,
            overall_status='Submitted',
            visual_layout_snapshot=visual_layout_data
        )

        issues_found = []
        items = ERCItem.objects.filter(is_active=True)
        for item in items:
            resp_key = f'response_{item.id}'
            rem_key = f'remarks_{item.id}'
            pic_key = f'photo_{item.id}'
            val = request.POST.get(resp_key)
            remarks = request.POST.get(rem_key)
            photo = request.FILES.get(pic_key)
            if val:
                ERCResponse.objects.create(
                    inspection=inspection,
                    item=item,
                    response=val,
                    remarks=remarks,
                    photo=photo
                )
                if val in ['Not Good', 'Damaged', 'Missing', 'Not Available']:
                    issues_found.append(item.text)

        # Handle Notifications
        from authentication.models import Notification, User, Project
        erc_project = Project.objects.filter(name__icontains='ERC').first()
        
        # Notify Inspector
        Notification.objects.create(
            recipient=request.user,
            project=erc_project,
            title="ERC Inspection Submitted",
            message=f"Inspection for {selected_center.name} has been successfully recorded.",
            type='success',
            link=f"/erc-104/dashboard/"
        )

        # Notify Admins if issues found
        if issues_found:
            admins = User.objects.filter(is_superuser=True)
            for admin in admins:
                Notification.objects.create(
                    recipient=admin,
                    project=erc_project,
                    title=f"ERC Issues Reported: {selected_center.name}",
                    message=f"Issues were reported for: {', '.join(issues_found[:3])}{'...' if len(issues_found) > 3 else ''}",
                    type='warning',
                    link=f"/authentication/reports/?project_id={erc_project.id if erc_project else ''}"
                )

        messages.success(request, 'ERC Inspection submitted successfully.')
        return redirect('erc_104:dashboard')

    categories = []
    grid_sections = []
    grid_config = {}

    if selected_center:
        categories = ERCCategory.objects.filter(is_active=True).prefetch_related('items').order_by('order')
        if is_readonly:
            for cat in categories:
                for item in cat.items.all():
                    if item.id in item_responses:
                        item.existing_response = item_responses[item.id]

        grid_sections = ERCGridSection.objects.filter(is_active=True).order_by('order')
        for section in grid_sections:
            grid_config[section.slug] = {
                'rows': section.rows,
                'cols': section.cols,
                'total_items': section.total_items,
                'prefix': section.prefix,
                'name': section.name,
                'icon': section.icon
            }

    context = {
        'centers': centers,
        'selected_center': selected_center,
        'categories': categories,
        'grid_sections': grid_sections,
        'grid_config': grid_config,
        'today_date': timezone.now().date(),
        'is_readonly': is_readonly,
        'last_inspection': last_inspection,
        'next_allowed_date': next_allowed_date
    }
    return render(request, 'erc_104/inspection_form.html', context)
