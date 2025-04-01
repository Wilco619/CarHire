import datetime
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone

class CarCategory(models.Model):
    """Model for car categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = 'Car Categories'

class Car(models.Model):
    """Model for individual cars"""
    TRANSMISSION_CHOICES = [
        ('auto', 'Automatic'),
        ('manual', 'Manual')
    ]

    FUEL_CHOICES = [
        ('petrol', 'Petrol'),
        ('diesel', 'Diesel'),
        ('hybrid', 'Hybrid'),
        ('electric', 'Electric')
    ]

    name = models.CharField(max_length=200)
    make = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    category = models.ForeignKey(CarCategory, on_delete=models.CASCADE)
    year = models.IntegerField(
        validators=[
            MinValueValidator(1990),
            MaxValueValidator(2025)
        ]
    )
    transmission = models.CharField(max_length=10, choices=TRANSMISSION_CHOICES)
    fuel_type = models.CharField(max_length=10, choices=FUEL_CHOICES)
    seats = models.IntegerField()
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='car_images/', null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1, help_text="Total number of units")
    booked_units = models.PositiveIntegerField(default=0, help_text="Number of currently booked units")

    @property
    def available_units(self):
        """Calculate number of available units"""
        return max(0, self.quantity - self.booked_units)

    @property
    def is_available(self):
        """Check if car has any available units"""
        return self.available_units > 0

    def __str__(self):
        return f"{self.year} {self.make} {self.model}"

    def is_available_for_dates(self, start_date, end_date):
        """Check if car is available for given date range"""
        overlapping_bookings = self.booking_set.filter(
            status__in=['pending', 'confirmed'],
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exists()
        
        return self.is_available and not overlapping_bookings

    def update_availability(self):
        """Update booked units count"""
        active_bookings = self.booking_set.filter(
            status__in=['pending', 'confirmed', 'active'],
            end_date__gte=timezone.now().date()
        ).count()
        self.booked_units = min(self.quantity, active_bookings)
        self.save()

    def handle_booking_cancellation(self):
        """Update car status when a booking is cancelled"""
        self.booked_units = max(0, self.booked_units - 1)
        self.save()
        self.update_availability()

    def get_rate(self, rental_type):
        """Get the appropriate rate based on rental type"""
        return self.hourly_rate if rental_type == 'hourly' else self.daily_rate

class Booking(models.Model):
    """Model for car bookings"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='bookings'  # Add this line
    )
    car = models.ForeignKey(Car, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    actual_return_date = models.DateTimeField(null=True, blank=True)
    total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    booking_date = models.DateTimeField(auto_now_add=True)
    is_late = models.BooleanField(default=False)
    late_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    penalty_paid = models.BooleanField(default=False)

    def calculate_late_fees(self):
        """Calculate late fees if car is returned after due date"""
        if not self.actual_return_date:
            return 0
        
        if self.actual_return_date > self.end_date:
            days_late = (self.actual_return_date.date() - self.end_date.date()).days
            daily_penalty = float(self.car.daily_rate) * 0.5
            return daily_penalty * days_late
        return 0

    def mark_as_returned(self, actual_return_date):
        """Process car return and calculate penalties"""
        self.actual_return_date = actual_return_date
        self.late_fees = self.calculate_late_fees()
        
        if self.late_fees > 0:
            self.is_late = True
            self.status = 'overdue'
        else:
            self.status = 'completed'
        
        self.save()
        self.car.update_availability()

    def __str__(self):
        return f"Booking #{self.id} - {self.car.name}"

class UserProfile(models.Model):
    """Extended user profile"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=15)
    address = models.TextField()
    driver_license = models.CharField(max_length=50)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.user.username


