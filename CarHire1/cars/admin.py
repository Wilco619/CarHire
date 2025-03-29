from django.contrib import admin
from .models import CarCategory, Car, Booking, UserProfile

@admin.register(CarCategory)
class CarCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    list_display = ('name', 'make', 'model', 'year', 'category', 'transmission', 'fuel_type', 'seats', 'daily_rate')
    list_filter = ('category', 'transmission', 'fuel_type', 'year')
    search_fields = ('name', 'make', 'model')

@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('user', 'car', 'start_date', 'end_date', 'total_cost', 'status', 'booking_date')
    list_filter = ('status', 'start_date', 'end_date')
    search_fields = ('user__username', 'car__name')

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'address', 'driver_license')
    search_fields = ('user__username', 'phone_number', 'driver_license')

