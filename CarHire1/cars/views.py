from datetime import datetime
import logging
from django.core.exceptions import FieldError
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone

from users.models import CustomUser
from .models import Car, Booking, CarCategory
from .forms import CarForm
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import CarCategoryForm
from .utils import send_booking_confirmation_email, send_late_return_notification

# Set up logger
logger = logging.getLogger(__name__)

# Update the home_view to use available_units
def home_view(request):
    """Home page view with featured cars"""
    try:
        logger.debug("Fetching all cars")
        cars = Car.objects.all().order_by('-id')
        
        featured_cars = []
        logger.debug("Starting to filter available cars")
        
        for car in cars:
            try:
                logger.debug(f"Processing car: {car.id} - {car.name}")
                logger.debug(f"Available units: {car.available_units}")
                
                if car.available_units > 0 and len(featured_cars) < 6:
                    featured_cars.append(car)
                    logger.debug(f"Added car {car.id} to featured cars")
            except Exception as e:
                logger.error(f"Error processing car {car.id}: {str(e)}")
                continue
        
        context = {
            'featured_cars': featured_cars,
            'categories': CarCategory.objects.all()
        }
        
        return render(request, 'core/home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home_view: {str(e)}")
        return render(request, 'core/home.html', {
            'error_message': 'Unable to load featured cars at this time.',
            'featured_cars': [],
            'categories': CarCategory.objects.all()
        })

def car_list_view(request):
    """List all available cars with filtering and pagination"""
    cars = Car.objects.all()
    
    # Get only cars with available units
    available_cars = [car for car in cars if car.available_units > 0]
    
    # Handle filters
    category = request.GET.get('category')
    price_range = request.GET.get('price_range')
    
    if category:
        available_cars = [car for car in available_cars if car.category_id == int(category)]
    
    if price_range:
        if price_range == '0-5000':
            available_cars = [car for car in available_cars if car.daily_rate < 5000]
        elif price_range == '5000-10000':
            available_cars = [car for car in available_cars if 5000 <= car.daily_rate < 10000]
        elif price_range == '10000+':
            available_cars = [car for car in available_cars if car.daily_rate >= 10000]
    
    # Pagination
    paginator = Paginator(available_cars, 9)
    page = request.GET.get('page')
    cars = paginator.get_page(page)
    
    return render(request, 'cars/car_list.html', {
        'cars': cars,
        'categories': CarCategory.objects.all(),
        'selected_category': category,
        'is_paginated': True if cars.paginator.num_pages > 1 else False
    })

def car_detail_view(request, car_id):
    car = get_object_or_404(Car, pk=car_id)
    
    # Get requested dates from query parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    has_available_units = car.available_units > 0
    if start_date and end_date:
        try:
            start_date = timezone.datetime.strptime(start_date, '%Y-%m-%d').date()
            end_date = timezone.datetime.strptime(end_date, '%Y-%m-%d').date()
            has_available_units = car.available_units > 0
        except ValueError:
            messages.error(request, 'Invalid date format')
    
    context = {
        'car': car,
        'has_available_units': has_available_units,
        'start_date': start_date,
        'end_date': end_date,
    }
    return render(request, 'cars/car_detail.html', context)

@login_required
def book_car_view(request, car_id):
    """Car booking view"""
    car = get_object_or_404(Car, pk=car_id)
    
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        
        # Basic validation
        if not start_date or not end_date:
            messages.error(request, 'Please select start and end dates')
            return redirect('car_detail', car_id=car.id)
        
        # Calculate total cost
        start = timezone.datetime.strptime(start_date, '%Y-%m-%d')
        end = timezone.datetime.strptime(end_date, '%Y-%m-%d')
        days = (end - start).days
        total_cost = car.daily_rate * days
        
        if car.available_units > 0:
            # Create booking
            booking = Booking.objects.create(
                user=request.user,
                car=car,
                start_date=start,
                end_date=end,
                total_cost=total_cost
            )
            
            car.update_availability()
            messages.success(request, 'Car booked successfully!')
            return redirect('booking_confirmation', booking_id=booking.id)
        else:
            messages.error(request, 'Sorry, this car is fully booked.')
    
    return render(request, 'cars/booking.html', {'car': car})

@login_required
def user_bookings_view(request):
    """View user's booking history"""
    bookings = Booking.objects.filter(user=request.user).order_by('-booking_date')
    return render(request, 'users/bookings.html', {'bookings': bookings})

@login_required
def booking_detail_view(request, booking_id):
    """Display detailed information about a specific booking"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    # Calculate rental duration
    duration = (booking.end_date - booking.start_date).days
    
    context = {
        'booking': booking,
        'duration': duration
    }
    return render(request, 'cars/booking_detail.html', context)

def car_by_category_view(request, category):
    """Display cars filtered by category"""
    all_cars = Car.objects.filter(category__name__iexact=category)
    cars = [car for car in all_cars if car.available_units > 0]
    
    context = {
        'cars': cars,
        'category': category,
        'categories': CarCategory.objects.all()
    }
    return render(request, 'cars/car_category.html', context)

@login_required
def cancel_booking_view(request, booking_id):
    """Cancel a booking"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    if booking.status in ['pending', 'confirmed']:
        booking.status = 'cancelled'
        booking.save()
        
        # Update car availability
        car = booking.car
        car.handle_booking_cancellation()
        
        messages.success(request, 'Booking cancelled successfully.')
    else:
        messages.error(request, 'This booking cannot be cancelled.')
    
    return redirect('user_bookings')

def car_availability_view(request):
    """Display availability status of all cars"""
    # Get all cars with their current booking status
    cars = Car.objects.all()
    today = timezone.now()
    
    for car in cars:
        # Check if car has any current bookings
        current_booking = Booking.objects.filter(
            car=car,
            start_date__lte=today,
            end_date__gte=today,
            status__in=['confirmed', 'pending']
        ).first()
        
        car.current_booking = current_booking
        
        # Get next available date
        next_booking = Booking.objects.filter(
            car=car,
            start_date__gt=today,
            status__in=['confirmed', 'pending']
        ).order_by('start_date').first()
        
        car.next_available = next_booking.start_date if next_booking else today
    
    context = {
        'cars': cars,
        'categories': CarCategory.objects.all(),
        'today': today,
    }
    return render(request, 'cars/availability.html', context)

def car_rates_view(request):
    """Display rental rates for all cars grouped by category"""
    categories = CarCategory.objects.all()
    
    # Get all cars first, then filter by availability in Python
    categorized_cars = {}
    for category in categories:
        all_cars = Car.objects.filter(category=category).order_by('daily_rate')
        # Filter available cars after database query
        available_cars = [car for car in all_cars if car.available_units > 0]
        categorized_cars[category] = available_cars
    
    context = {
        'categorized_cars': categorized_cars,
        'categories': categories
    }
    return render(request, 'cars/rates.html', context)

@login_required
def add_car_view(request):
    """Add a new car to the system"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to add cars.')
        return redirect('car_list')
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES)
        if form.is_valid():
            car = form.save()
            messages.success(request, f'Car "{car.name}" added successfully.')
            return redirect('car_detail', car_id=car.id)
    else:
        form = CarForm()
    
    return render(request, 'cars/car_form.html', {
        'form': form,
        'title': 'Add New Car',
        'submit_text': 'Add Car'
    })

@login_required
def edit_car_view(request, car_id):
    """Edit an existing car"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit cars.')
        return redirect('car_list')
    
    car = get_object_or_404(Car, pk=car_id)
    
    if request.method == 'POST':
        form = CarForm(request.POST, request.FILES, instance=car)
        if form.is_valid():
            car = form.save()
            messages.success(request, f'Car "{car.name}" updated successfully.')
            return redirect('car_detail', car_id=car.id)
    else:
        form = CarForm(instance=car)
    
    return render(request, 'cars/car_form.html', {
        'form': form,
        'title': f'Edit Car: {car.name}',
        'submit_text': 'Update Car',
        'car': car
    })

@login_required
def delete_car_view(request, car_id):
    """Delete an existing car"""
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete cars.')
        return redirect('car_list')
    
    car = get_object_or_404(Car, pk=car_id)
    
    if request.method == 'POST':
        # Check if car has any bookings
        if Booking.objects.filter(car=car, status__in=['pending', 'confirmed']).exists():
            messages.error(request, 'Cannot delete car with active bookings.')
            return redirect('car_detail', car_id=car.id)
        
        # Delete the car image if it exists
        if car.image:
            car.image.delete()
        
        car.delete()
        messages.success(request, f'Car "{car.name}" deleted successfully.')
        return redirect('car_list')
    
    return render(request, 'cars/car_delete.html', {
        'car': car
    })

def search_cars_view(request):
    """Search cars with filters"""
    # Get all cars first
    cars = Car.objects.all()
    categories = CarCategory.objects.all()
    
    category = request.GET.get('category')
    price_range = request.GET.get('price_range')
    transmission = request.GET.get('transmission')
    seats = request.GET.get('seats')
    
    # Apply database filters
    if category:
        cars = cars.filter(category_id=category)
    
    if price_range:
        min_price, max_price = price_range.split('-')
        if max_price == '+':
            cars = cars.filter(daily_rate__gte=float(min_price))
        else:
            cars = cars.filter(daily_rate__gte=float(min_price),
                             daily_rate__lte=float(max_price))
    
    if transmission:
        cars = cars.filter(transmission=transmission)
    
    if seats:
        cars = cars.filter(seats=seats)
    
    # Filter for availability in Python using available_units
    available_cars = [car for car in cars if car.available_units > 0]
    
    return render(request, 'cars/search.html', {
        'cars': available_cars,
        'categories': categories,
        'selected_category': category
    })

def is_admin(user):
    return user.is_authenticated and user.is_staff

@user_passes_test(is_admin)
def admin_dashboard_view(request):
    context = {
        'total_bookings': Booking.objects.count(),
        'pending_bookings': Booking.objects.filter(status='pending').count(),
        'total_cars': Car.objects.count(),
        'total_users': CustomUser.objects.count(),
    }
    return render(request, 'admin/dashboard.html', context)

@user_passes_test(is_admin)
def admin_bookings_view(request):
    bookings_list = Booking.objects.all().order_by('-booking_date')
    
    # Handle filters
    status_filter = request.GET.get('status')
    date_filter = request.GET.get('date')
    
    if status_filter:
        bookings_list = bookings_list.filter(status=status_filter)
    if date_filter:
        bookings_list = bookings_list.filter(start_date=date_filter)
    
    # Pagination
    paginator = Paginator(bookings_list, 10)
    page = request.GET.get('page')
    bookings = paginator.get_page(page)
    
    return render(request, 'admin/bookings.html', {'bookings': bookings})

@user_passes_test(is_admin)
def admin_cars_view(request):
    """Admin view for managing cars"""
    cars = Car.objects.all().order_by('-id')
    
    # Handle filters
    make_filter = request.GET.get('make', '')
    category_filter = request.GET.get('category', '')
    availability_filter = request.GET.get('availability', '')
    
    if make_filter:
        cars = cars.filter(make__icontains=make_filter)
    if category_filter:
        cars = cars.filter(category_id=category_filter)
    if availability_filter:
        # Filter in Python since availability is based on available_units
        cars = [car for car in cars if (car.available_units > 0) == (availability_filter == 'available')]
    
    # Pagination
    paginator = Paginator(cars, 10)
    page = request.GET.get('page')
    cars = paginator.get_page(page)
    
    context = {
        'cars': cars,
        'categories': CarCategory.objects.all(),
        'makes': Car.objects.values_list('make', flat=True).distinct()
    }
    return render(request, 'admin/cars.html', context)

@user_passes_test(is_admin)
def admin_users_view(request):
    """Admin view for managing users"""
    users = CustomUser.objects.all().order_by('-date_joined')
    
    # Handle filters
    user_type = request.GET.get('user_type', '')
    search_query = request.GET.get('search', '')
    
    if user_type:
        users = users.filter(user_type=user_type)
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(users, 10)
    page = request.GET.get('page')
    users = paginator.get_page(page)
    
    return render(request, 'admin/users.html', {'users': users})

@user_passes_test(is_admin)
def admin_booking_detail_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    return render(request, 'admin/booking_detail.html', {'booking': booking})

@user_passes_test(is_admin)
def admin_booking_edit_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    
    if request.method == 'POST':
        # Get form data
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        new_status = request.POST.get('status')
        
        # Convert dates to datetime objects
        start_datetime = datetime.strptime(f"{start_date} 00:00:00", '%Y-%m-%d %H:%M:%S')
        end_datetime = datetime.strptime(f"{end_date} 23:59:59", '%Y-%m-%d %H:%M:%S')
        
        # Update booking
        booking.start_date = timezone.make_aware(start_datetime)
        booking.end_date = timezone.make_aware(end_datetime)
        booking.status = new_status
        
        # Recalculate total cost if dates changed
        days = (end_datetime - start_datetime).days + 1
        booking.total_cost = booking.car.daily_rate * days
        
        # Save changes
        booking.save()
        
        messages.success(request, f'Booking #{booking.id} updated successfully.')
        return redirect('admin_booking_detail', booking_id=booking.id)
    
    return render(request, 'admin/booking_edit.html', {'booking': booking})

@user_passes_test(lambda u: u.is_staff)
def admin_booking_confirm_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    if booking.status == 'pending':
        booking.status = 'confirmed'
        booking.save()
        messages.success(request, f'Booking #{booking.id} has been confirmed.')
    else:
        messages.error(request, 'Booking could not be confirmed.')
    return redirect('admin_bookings')

@user_passes_test(is_admin)
def admin_categories_view(request):
    """Admin view for managing car categories"""
    categories = CarCategory.objects.all()
    return render(request, 'admin/car_categories.html', {'categories': categories})

@user_passes_test(is_admin)
def admin_add_category_view(request):
    if request.method == 'POST':
        form = CarCategoryForm(request.POST)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" added successfully.')
            return redirect('admin_categories')
    return redirect('admin_categories')

@user_passes_test(is_admin)
def admin_get_category_view(request, category_id):
    category = get_object_or_404(CarCategory, pk=category_id)
    return JsonResponse({
        'name': category.name,
        'description': category.description
    })

@user_passes_test(is_admin)
def admin_edit_category_view(request, category_id):
    category = get_object_or_404(CarCategory, pk=category_id)
    if request.method == 'POST':
        form = CarCategoryForm(request.POST, instance=category)
        if form.is_valid():
            category = form.save()
            messages.success(request, f'Category "{category.name}" updated successfully.')
    return redirect('admin_categories')

@user_passes_test(is_admin)
def admin_delete_category_view(request, category_id):
    category = get_object_or_404(CarCategory, pk=category_id)
    if request.method == 'POST':
        if category.car_set.exists():
            messages.error(request, 'Cannot delete category with associated cars.')
        else:
            category.delete()
            messages.success(request, f'Category "{category.name}" deleted successfully.')
    return redirect('admin_categories')

@login_required
def booking_confirmation_view(request, booking_id):
    """Display booking confirmation details"""
    booking = get_object_or_404(Booking, pk=booking_id, user=request.user)
    
    # Calculate rental duration
    duration = (booking.end_date - booking.start_date).days
    
    context = {
        'booking': booking,
        'car': booking.car,
        'duration': duration,
        'total_cost': booking.total_cost,
        'booking_date': booking.booking_date,
    }
    return render(request, 'cars/booking_confirmation.html', context)

@user_passes_test(is_admin)
def handle_car_return_view(request, booking_id):
    """Handle car return and calculate penalties"""
    booking = get_object_or_404(Booking, pk=booking_id)
    
    if request.method == 'POST':
        return_date = timezone.now()
        booking.mark_as_returned(return_date)
        
        if booking.is_late:
            messages.warning(
                request,
                f'Car returned late. Late fees: Ksh{booking.late_fees}'
            )
            # Send late return notification
            send_late_return_notification(booking)
        else:
            messages.success(request, 'Car returned successfully on time.')
        
        return redirect('admin_booking_detail', booking_id=booking_id)
    
    context = {
        'booking': booking,
        'now': timezone.now(),
    }
    return render(request, 'admin/handle_return.html', context)

@login_required
def user_penalties_view(request):
    """View user's penalties and late fees"""
    penalties = Booking.objects.filter(
        user=request.user,
        is_late=True,
        penalty_paid=False
    ).order_by('-actual_return_date')
    
    total_penalties = sum(booking.late_fees for booking in penalties)
    
    context = {
        'penalties': penalties,
        'total_penalties': total_penalties
    }
    return render(request, 'users/penalties.html', context)