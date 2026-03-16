from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail
from django.conf import settings
from authentication.models import UserProfile, Notification, Inspection, ProjectRoleDeadline
from ops_104.models import OpsInspection as Ops104
from ops_108.models import OpsInspection as Ops108
from erc_104.models import ERCInspection as ERC104

class Command(BaseCommand):
    help = 'Checks for missed inspection deadlines for all projects (104, 108, ERC)'

    def add_arguments(self, parser):
        parser.add_argument('--project_id', type=int, help='Only check for a specific project')

    def handle(self, *args, **options):
        now = timezone.now()
        local_now = timezone.localtime(now)
        project_id = options.get('project_id')
        
        self.stdout.write("--- Inspection Deadline Monitor ---")
        if project_id:
            self.stdout.write(f"Project ID Filter: {project_id}")
        self.stdout.write(f"Checking at: {local_now.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Select all active users with their hierarchy and project context
        users_to_check = UserProfile.objects.filter(user__is_active=True).select_related('user', 'supervisor', 'role', 'assigned_project')
        
        if project_id:
            users_to_check = users_to_check.filter(assigned_project_id=project_id)
            
        total_alerts = 0

        for profile in users_to_check:
            user = profile.user
            if user.is_superuser:
                continue

            # Check for activity across all models
            last_basic = Inspection.objects.filter(inspector=user).order_by('-created_at').first()
            d1 = last_basic.created_at if last_basic else None

            last_ops_104 = Ops104.objects.filter(inspector=user).order_by('-created_at').first()
            d2 = last_ops_104.created_at if last_ops_104 else None

            last_ops_108 = Ops108.objects.filter(inspector=user).order_by('-created_at').first()
            d3 = last_ops_108.created_at if last_ops_108 else None

            last_erc = ERC104.objects.filter(inspector=user).order_by('-created_at').first()
            d4 = last_erc.created_at if last_erc else None

            last_activity = max([d for d in [d1, d2, d3, d4] if d]) if any([d1, d2, d3, d4]) else None
            last_date_str = last_activity.strftime('%Y-%m-%d %H:%M') if last_activity else "No Activity Recorded"

            # Determine deadline based on Role or Project-specific Role override
            d_days = 0
            d_hours = 0
            d_mins = 0
            
            if profile.role:
                prd = None
                if profile.assigned_project:
                    prd = ProjectRoleDeadline.objects.filter(project=profile.assigned_project, role=profile.role).first()
                
                if prd:
                    d_days = prd.inspection_deadline_days
                    d_hours = prd.inspection_deadline_hours
                    d_mins = prd.inspection_deadline_minutes
                else:
                    d_days = profile.role.inspection_deadline_days
                    d_hours = profile.role.inspection_deadline_hours
                    d_mins = profile.role.inspection_deadline_minutes
            
            if d_days == 0 and d_hours == 0 and d_mins == 0:
                continue # Skip check if no deadline is set
            
            threshold = now - timedelta(days=d_days, hours=d_hours, minutes=d_mins)

            is_missed = False
            time_since = None
            
            if not last_activity:
                # For new users, check from join date
                if user.date_joined < threshold:
                    is_missed = True
                    time_since = now - user.date_joined
            elif last_activity < threshold:
                is_missed = True
                time_since = now - last_activity

            if is_missed:
                self.stdout.write(self.style.WARNING(f"  [!] DEADLINE MISSED for {user.username} ({profile.assigned_project.name if profile.assigned_project else 'No Project'})"))
                
                effective_days_missed = time_since.days - d_days
                if effective_days_missed < 1: effective_days_missed = 1 

                current_escalator = profile.supervisor
                if not current_escalator:
                    continue

                escalation_level = 1
                limit_str = f"{d_days}d {d_hours}h {d_mins}m"

                # Escalation Chain
                while current_escalator and escalation_level <= (effective_days_missed + 1): 
                    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    already_handled = Notification.objects.filter(
                        recipient=current_escalator.user,
                        title__contains=f"L{escalation_level}",
                        message__contains=f"Escalation for {user.username}",
                        created_at__gte=today_start
                    ).exists()

                    if not already_handled:
                        # Ensure the notification is visible to the supervisor by tagging it correctly
                        # If the supervisor has a project assigned, we tag it with their project so it shows up in their filtered view.
                        # If the supervisor is global, project=None is fine.
                        notification_project = current_escalator.assigned_project
                        
                        title = f"Alert: L{escalation_level} Deadline Escalation | {profile.assigned_project.name if profile.assigned_project else 'General'}"
                        message = f"Escalation for {user.username}: No activity in {profile.assigned_project.name if profile.assigned_project else 'system'}. Limit: {limit_str}. Last activity: {last_date_str}."
                        
                        # Better link based on project
                        dashboard_link = "/dashboard/"
                        if profile.assigned_project:
                            p_name = profile.assigned_project.name.lower()
                            if 'erc' in p_name: dashboard_link = "/erc-104/dashboard/"
                            elif '104' in p_name: dashboard_link = "/ops-104/dashboard/"
                            elif '108' in p_name: dashboard_link = "/ops-108/dashboard/"

                        Notification.objects.create(
                            recipient=current_escalator.user,
                            project=notification_project,
                            title=title,
                            message=message,
                            type='alert' if escalation_level > 1 else 'warning',
                            link=dashboard_link
                        )

                        # Also notify the user themselves at L1
                        if escalation_level == 1:
                            Notification.objects.create(
                                recipient=user,
                                project=profile.assigned_project,
                                title="Warning: Inspection Deadline Missed",
                                message=f"You have missed your inspection deadline for {profile.assigned_project.name if profile.assigned_project else 'your project'}. Please perform an inspection immediately to avoid further escalation.",
                                type='warning',
                                link=dashboard_link
                            )

                        if current_escalator.user.email and settings.EMAIL_HOST_USER:
                            try:
                                mail_subject = f"ESCALATION LEVEL {escalation_level}: Missed Inspection Alert ({user.username})"
                                mail_body = f"Hello {current_escalator.user.username},\n\nAutomated Alert: A subordinate has exceeded their inspection deadline.\n\nUSER: {user.username}\nProject: {profile.assigned_project.name if profile.assigned_project else 'N/A'}\nLast Activity: {last_date_str}\nLimit: {limit_str}\n\nPlease follow up.\n\nRegards,\nInspection System Team"
                                send_mail(mail_subject, mail_body, settings.DEFAULT_FROM_EMAIL, [current_escalator.user.email], fail_silently=True)
                            except Exception:
                                pass
                        total_alerts += 1

                    current_escalator = current_escalator.supervisor
                    escalation_level += 1

        self.stdout.write(self.style.SUCCESS(f"Task Complete. Total Escalations Processed: {total_alerts}"))
