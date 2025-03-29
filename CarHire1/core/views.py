from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import F
from django.views.decorators.http import require_http_methods

from cars.models import Car, CarCategory

def home_view(request):
    """
    Home page view with featured cars and categories
    """
    # Get featured cars (first 6 cars that have available units)
    featured_cars = Car.objects.filter(
        booked_units__lt=F('quantity')  # Use F() directly
    )[:6]
    
    # Get car categories
    categories = CarCategory.objects.all()

    context = {
        'featured_cars': featured_cars,
        'categories': categories,
        'title': 'Welcome to Car Hire Service'
    }
    return render(request, 'core/home.html', context)

def about_view(request):
    """
    About page view
    """
    context = {
        'title': 'About Us',
        'company_info': {
            'name': 'Car Hire Solutions',
            'founded': 2024,
            'mission': 'Providing convenient and affordable car rental services.'
        }
    }
    return render(request, 'core/aboutus.html', context)

@require_http_methods(["GET", "POST"])
def contact_view(request):
    """
    Contact page with form submission
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        message = request.POST.get('message')

        # Basic validation
        if not all([name, email, message]):
            messages.error(request, 'Please fill out all fields.')
            return render(request, 'core/contact.html')

        try:
            # Send email
            send_mail(
                f'Contact Form Submission from {name}',
                f'From: {name}\nEmail: {email}\n\nMessage:\n{message}',
                settings.DEFAULT_FROM_EMAIL,
                [settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            messages.success(request, 'Your message has been sent successfully!')
            return redirect('contact')
        except Exception as e:
            messages.error(request, 'An error occurred. Please try again later.')
            # Log the error in a real-world scenario
            print(f"Email sending error: {e}")

    return render(request, 'core/contact.html', {'title': 'Contact Us'})

def services_view(request):
    return render(request, 'core/services.html')

def terms_view(request):
    """
    Terms of Service page
    """
    context = {
        'title': 'Terms of Service',
        'last_updated': '2024-03-27'
    }
    return render(request, 'core/terms.html', context)

def privacy_view(request):
    """
    Privacy Policy page
    """
    context = {
        'title': 'Privacy Policy',
        'last_updated': '2024-03-27'
    }
    return render(request, 'core/privacy.html', context)

def faq_view(request):
    """
    Frequently Asked Questions page
    """
    faqs = [
        {
            'question': 'How old do I need to be to rent a car?',
            'answer': 'You must be at least 21 years old and have a valid driver\'s license.'
        },
        {
            'question': 'What documents do I need to rent a car?',
            'answer': 'You need a valid driver\'s license, passport or government ID, and a credit card.'
        },
        {
            'question': 'Can I cancel my booking?',
            'answer': 'Yes, you can cancel up to 24 hours before your rental start time with no penalty.'
        }
    ]

    context = {
        'title': 'Frequently Asked Questions',
        'faqs': faqs
    }
    return render(request, 'core/faq.html', context)