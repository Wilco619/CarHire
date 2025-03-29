from django.core.management.base import BaseCommand
from django.utils import timezone
from cars.models import Booking
from cars.utils import send_late_return_notification

class Command(BaseCommand):
    help = 'Check for overdue car rentals and update their status'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Get active bookings past their return date
        overdue_bookings = Booking.objects.filter(
            status='active',
            end_date__lt=now,
            actual_return_date__isnull=True
        )
        
        for booking in overdue_bookings:
            booking.status = 'overdue'
            booking.is_late = True
            booking.save()
            
            # Send notification
            send_late_return_notification(booking)
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Found {overdue_bookings.count()} overdue rentals'
            )
        )