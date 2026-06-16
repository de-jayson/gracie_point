"""
Accounts Models
Custom User model with role-based access control
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Extended User model with church-specific roles.
    Replaces Django's default User model.
    """

    class Role(models.TextChoices):
        CHURCH_ADMIN = 'church_admin', 'Church Administrator'
        PASTOR = 'pastor', 'Pastor'
        FINANCE_OFFICER = 'finance_officer', 'Finance Officer'
        SECRETARY = 'secretary', 'Secretary'


    church = models.ForeignKey(
        "organizations.Church",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="users",
    )


    role = models.CharField(
        max_length=50,
        choices=Role.choices,
        default=Role.SECRETARY,
        help_text="User's role determines their access level",
    )


    full_name = models.CharField(max_length=255, blank=True)

    phone = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )


    # ----------------------------
    # Role Permission Helpers
    # ----------------------------

    @property
    def is_admin_user(self):
        return self.role == self.Role.CHURCH_ADMIN


    @property
    def is_pastor(self):
        return self.role == self.Role.PASTOR


    @property
    def is_finance_officer(self):
        return self.role == self.Role.FINANCE_OFFICER


    @property
    def is_secretary(self):
        return self.role == self.Role.SECRETARY



    # ----------------------------
    # Prevent multiple church admins
    # ----------------------------

    def save(self, *args, **kwargs):

        if self.role == self.Role.CHURCH_ADMIN:

            existing_admin = CustomUser.objects.filter(
                church=self.church,
                role=self.Role.CHURCH_ADMIN
            ).exclude(
                id=self.id
            ).exists()


            if existing_admin:
                raise ValueError(
                    "This church already has a Church Administrator."
                )


        super().save(*args, **kwargs)



    def __str__(self):
        return (
            f"{self.get_full_name() or self.username}"
            f" ({self.get_role_display()})"
        )


    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'