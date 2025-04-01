from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    """
    Extended User model with all necessary fields
    """
    USER_TYPE_CHOICES = (
        ('customer', 'Customer'),
        ('admin', 'Admin'),
        ('staff', 'Staff')
    )
    
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    # Basic Information
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='customer')
    email = models.EmailField(_('email address'), unique=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    is_verified = models.BooleanField(default=False)

    # Contact Information
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(validators=[phone_regex], max_length=17, blank=True)

    # Address Information
    street_address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=10, blank=True)
    country = models.CharField(max_length=100, blank=True)

    # Driver Information
    license_number = models.CharField(max_length=50, blank=True)
    license_country = models.CharField(max_length=100, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    license_image = models.ImageField(upload_to='licenses/', null=True, blank=True)
    has_international_permit = models.BooleanField(default=False)
    international_permit_number = models.CharField(max_length=50, blank=True)
    international_permit_expiry = models.DateField(null=True, blank=True)

    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def __str__(self):
        return self.email

    @property
    def is_customer(self):
        return self.user_type == 'customer'

    @property
    def is_car_admin(self):
        return self.user_type == 'admin' or self.is_superuser

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def has_valid_license(self):
        from django.utils import timezone
        if not self.license_number or not self.license_expiry:
            return False
        return self.license_expiry > timezone.now().date()


class UserProfile(models.Model):
    """
    Additional profile information for users
    """
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other')
    ]

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    address = models.TextField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    driver_license_number = models.CharField(max_length=50, blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='profile_pics/', 
        null=True, 
        blank=True
    )
    driving_license = models.CharField(max_length=50, blank=True)
    license_expiry = models.DateField(null=True, blank=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=15, blank=True)

    class Meta:
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')

    def __str__(self):
        return f"{self.user.username}'s Profile"