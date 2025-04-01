from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, get_user_model, get_backends
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from django.db.models import Sum

from cars.models import Booking

from .models import CustomUser

from .forms import (
    CustomUserCreationForm, 
    UserUpdateForm, 
    UserProfileForm
)

User = get_user_model()

def is_customer(user):
    """
    Check if the user is a customer
    """
    return user.is_authenticated and user.user_type == 'customer'

def is_admin(user):
    """
    Check if the user is an admin
    """
    return user.is_authenticated and (user.user_type == 'admin' or user.is_superuser or user.is_staff)

def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            # Get the first backend from AUTHENTICATION_BACKENDS
            backend = get_backends()[0]
            # Log the user in with the specified backend
            login(request, user, backend=backend.__class__.__name__)
            messages.success(request, 'Account created successfully!')
            return redirect('profile')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {
        'form': form,
        'title': 'Register'
    })

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('username')  # Form field is named username but accepts email
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        
        if user is not None:
            login(request, user)
            # Redirect based on user type
            if user.is_staff or user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('customer_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'users/login.html')

def logout_view(request):
    """
    Logout view with message
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')

@login_required
def customer_dashboard(request):
    """Display customer dashboard with booking information"""
    # Get active bookings
    active_bookings = Booking.objects.filter(
        user=request.user,
        status__in=['pending', 'confirmed', 'active']
    )
    
    # Get past bookings
    past_bookings = Booking.objects.filter(
        user=request.user,
        status__in=['completed', 'cancelled']
    )
    
    # Get recent bookings (last 5)
    recent_bookings = Booking.objects.filter(
        user=request.user
    ).order_by('-booking_date')[:5]
    
    # Calculate unpaid penalties
    unpaid_penalties = Booking.objects.filter(
        user=request.user,
        is_late=True,
        penalty_paid=False
    ).aggregate(total=Sum('late_fees'))['total'] or 0
    
    context = {
        'active_bookings': active_bookings,
        'past_bookings': past_bookings,
        'recent_bookings': recent_bookings,
        'unpaid_penalties': unpaid_penalties,
    }
    
    return render(request, 'users/customer_dashboard.html', context)

@login_required
def profile_view(request):
    """
    Profile view with update functionality
    """
    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileForm(
            request.POST, 
            request.FILES, 
            instance=request.user.profile
        )
        
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile has been updated!')
            return redirect('profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=request.user.profile)
    
    return render(request, 'users/profile.html', {
        'user_form': user_form,
        'profile_form': profile_form
    })

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('profile')
    else:
        form = UserUpdateForm(instance=request.user)
    
    return render(request, 'users/edit_profile.html', {
        'form': form,
        'title': 'Edit Profile'
    })

@user_passes_test(is_admin)
def admin_user_detail(request, user_id):
    user = get_object_or_404(User, id=user_id)
    # Get bookings if they exist, otherwise return empty queryset
    bookings = user.bookings.all().order_by('-booking_date') if hasattr(user, 'bookings') else []
    
    return render(request, 'admin/user_detail.html', {
        'user_detail': user,
        'bookings': bookings
    })

@user_passes_test(is_admin)
def admin_user_edit(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        # Handle form submission
        user.first_name = request.POST.get('first_name')
        user.last_name = request.POST.get('last_name')
        user.email = request.POST.get('email')
        
        if request.POST.get('is_staff'):
            user.is_staff = True
        else:
            user.is_staff = False
            
        user.save()
        messages.success(request, f'User {user.get_full_name()} updated successfully.')
        return redirect('admin_user_detail', user_id=user.id)
        
    return render(request, 'admin/user_edit.html', {'user_detail': user})

@user_passes_test(is_admin)
def admin_user_toggle_status(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if not user.is_superuser:
        user.is_active = not user.is_active
        user.save()
        status = 'activated' if user.is_active else 'deactivated'
        messages.success(request, f'User {user.get_full_name()} has been {status}.')
    return redirect('admin_users')


