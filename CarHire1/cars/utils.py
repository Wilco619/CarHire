from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.html import strip_tags

def send_html_email(subject, template_name, context, recipient_email):
    """Send HTML email using template"""
    # Add site_url to context
    context['site_url'] = settings.SITE_URL
    
    # Render HTML content
    html_message = render_to_string(template_name, context)
    # Create plain text version
    plain_message = strip_tags(html_message)
    
    # Send email
    return send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient_email],
        html_message=html_message
    )

def send_booking_confirmation_email(booking):
    """Send booking confirmation email"""
    context = {
        'booking': booking,
    }
    send_html_email(
        subject=f'Booking Confirmation - #{booking.id}',
        template_name='emails/booking_confirmation.html',
        context=context,
        recipient_email=booking.user.email
    )

def send_late_return_notification(booking):
    """Send late return notification"""
    context = {
        'booking': booking,
        'days_late': (booking.actual_return_date - booking.end_date).days
    }
    send_html_email(
        subject=f'Late Return Notice - Booking #{booking.id}',
        template_name='emails/late_return_notice.html',
        context=context,
        recipient_email=booking.user.email
    )