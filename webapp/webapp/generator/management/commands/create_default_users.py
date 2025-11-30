"""
Management command to create default users from environment variables.

Usage:
    python manage.py create_default_users

Environment variables:
    PILLARS_ADMIN_USERNAME - Admin username (default: 'sam')
    PILLARS_ADMIN_PASSWORD - Admin password (required)
    PILLARS_ADMIN_EMAIL    - Admin email (optional)

    PILLARS_DM_USERNAME    - DM username (default: 'dm')
    PILLARS_DM_PASSWORD    - DM password (required)
    PILLARS_DM_EMAIL       - DM email (optional)

If passwords are not set, the users will not be created.
"""
import os
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from webapp.generator.models import UserProfile


class Command(BaseCommand):
    help = 'Create default admin and DM users from environment variables'

    def handle(self, *args, **options):
        # Admin user
        admin_username = os.environ.get('PILLARS_ADMIN_USERNAME', 'sam')
        admin_password = os.environ.get('PILLARS_ADMIN_PASSWORD')
        admin_email = os.environ.get('PILLARS_ADMIN_EMAIL', '')

        if admin_password:
            user, created = User.objects.get_or_create(
                username=admin_username,
                defaults={'email': admin_email}
            )
            user.set_password(admin_password)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.roles = ['admin', 'dm']
            profile.save()

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created admin user '{admin_username}' with roles: admin, dm"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Updated admin user '{admin_username}'"
                ))
        else:
            self.stdout.write(self.style.WARNING(
                "PILLARS_ADMIN_PASSWORD not set, skipping admin user creation"
            ))

        # DM user
        dm_username = os.environ.get('PILLARS_DM_USERNAME', 'dm')
        dm_password = os.environ.get('PILLARS_DM_PASSWORD')
        dm_email = os.environ.get('PILLARS_DM_EMAIL', '')

        if dm_password:
            user, created = User.objects.get_or_create(
                username=dm_username,
                defaults={'email': dm_email}
            )
            user.set_password(dm_password)
            user.save()

            profile, _ = UserProfile.objects.get_or_create(user=user)
            profile.roles = ['dm']
            profile.save()

            if created:
                self.stdout.write(self.style.SUCCESS(
                    f"Created DM user '{dm_username}' with role: dm"
                ))
            else:
                self.stdout.write(self.style.SUCCESS(
                    f"Updated DM user '{dm_username}'"
                ))
        else:
            self.stdout.write(self.style.WARNING(
                "PILLARS_DM_PASSWORD not set, skipping DM user creation"
            ))
