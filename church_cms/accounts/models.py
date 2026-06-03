"""
Accounts Models
Custom User model with role-based access control
"""

from django.contrib.auth.models import AbstractUser


class CustomUser(AbstractUser):
    """
    Extended User model with church-specific roles.
    Replaces Django's default User model.
    """

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        PASTOR = 'pastor', 'Pastor'
        FINANCE_OFFICER = 'finance_officer', 'Finance Officer'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.ADMIN,
        help_text="User's role determines their access level"
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profiles/', blank=True, null=True
    )

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Role helper properties ---

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN

    @property
    def is_pastor(self):
        return self.role == self.Role.PASTOR

    @property
    def is_finance_officer(self):
        return self.role == self.Role.FINANCE_OFFICER

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
