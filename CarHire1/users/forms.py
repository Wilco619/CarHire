from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser, UserProfile

class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form with email
    """
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = (
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number'
        )

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.user_type = 'customer'  # Default to customer
        
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = (
            'username', 
            'email', 
            'first_name', 
            'last_name', 
            'phone_number', 
            'address', 
            'date_of_birth'
        )

class UserUpdateForm(UserChangeForm):
    """
    Form for updating user information
    """
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 
            'last_name', 
            'email'
        ]

class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile
    """
    class Meta:
        model = UserProfile
        fields = [
            'address', 
            'gender', 
            'date_of_birth', 
            'driver_license_number', 
            'profile_picture'
        ]