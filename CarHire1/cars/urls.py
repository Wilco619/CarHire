from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    # Public Car Listing and Search URLs
    path('', views.car_list_view, name='car_list'),
    path('search/', views.search_cars_view, name='search_cars'),
    path('category/<str:category>/', views.car_by_category_view, name='car_by_category'),
    
    # Car Detail and Booking URLs
    path('<int:car_id>/', views.car_detail_view, name='car_detail'),
    path('<int:car_id>/book/', 
         login_required(views.book_car_view), 
         name='book_car'),
    
    # Booking Management URLs
    path('bookings/', 
         login_required(views.user_bookings_view), 
         name='user_bookings'),
    path('booking/<int:booking_id>/', 
         views.booking_detail_view, 
         name='booking_detail'),
    path('booking/<int:booking_id>/cancel/', 
         login_required(views.cancel_booking_view), 
         name='cancel_booking'),
    path('booking/<int:booking_id>/confirmation/', 
         views.booking_confirmation_view, 
         name='booking_confirmation'),
    
    # Additional Car-related URLs
    path('availability/', views.car_availability_view, name='car_availability'),
    path('rates/', views.car_rates_view, name='car_rates'),
    
    # Admin-specific Car Management URLs
    path('admin/add/', 
         login_required(views.add_car_view), 
         name='add_car'),
    path('admin/edit/<int:car_id>/', 
         login_required(views.edit_car_view), 
         name='edit_car'),
    path('admin/delete/<int:car_id>/', 
         login_required(views.delete_car_view), 
         name='delete_car'),
    
    # Admin Routes
    path('admin/dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin/bookings/', views.admin_bookings_view, name='admin_bookings'),
    path('admin/cars/', views.admin_cars_view, name='admin_cars'),
    path('admin/users/', views.admin_users_view, name='admin_users'),
    path('admin/booking/<int:booking_id>/return/', 
         views.handle_car_return_view, 
         name='handle_car_return'),
    
    # Admin booking management
    path('admin/bookings/<int:booking_id>/', views.admin_booking_detail_view, name='admin_booking_detail'),
    path('admin/bookings/<int:booking_id>/edit/', views.admin_booking_edit_view, name='admin_booking_edit'),
    path('admin/bookings/<int:booking_id>/confirm/', views.admin_booking_confirm_view, name='admin_booking_confirm'),
    
    # Add these new URL patterns
    path('admin/categories/', views.admin_categories_view, name='admin_categories'),
    path('admin/category/add/', views.admin_add_category_view, name='admin_add_category'),
    path('admin/category/<int:category_id>/', views.admin_get_category_view, name='admin_get_category'),
    path('admin/category/<int:category_id>/edit/', views.admin_edit_category_view, name='admin_edit_category'),
    path('admin/category/<int:category_id>/delete/', views.admin_delete_category_view, name='admin_delete_category'),
    
    # User URLs
    path('penalties/', 
         views.user_penalties_view, 
         name='user_penalties'),
]