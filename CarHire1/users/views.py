from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse

from .models import CustomUser
from .forms import (
    CustomUserCreationForm, 
    UserUpdateForm, 
    UserProfileForm
)

def is_customer(user):
    """
    Check if the user is a customer
    """
    return user.is_authenticated and user.user_type == 'customer'

def is_admin(user):
    """
    Check if the user is an admin
    """
    return user.is_authenticated and (user.user_type == 'admin' or user.is_superuser)

def register_view(request):
    """
    User registration view with role assignment
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            # Explicitly set user type to customer during registration
            user = form.save(commit=False)
            user.user_type = 'customer'
            user.save()
            
            # Authenticate and login the user
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            
            if user:
                login(request, user)
                messages.success(request, f'Account created for {username}!')
                return redirect('home')
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'users/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
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
@user_passes_test(is_customer)
def customer_dashboard(request):
    """
    Customer-specific dashboard
    """
    # Fetch user's bookings, etc.
    bookings = request.user.bookings.all()  # Assuming you have a related name 'bookings'
    return render(request, 'users/customer_dashboard.html', {
        'bookings': bookings
    })

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