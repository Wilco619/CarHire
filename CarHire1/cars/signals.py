from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Booking

@receiver(post_save, sender=Booking)
def update_car_availability(sender, instance, **kwargs):
    """Update car availability when a booking is created or updated"""
    instance.car.update_availability()