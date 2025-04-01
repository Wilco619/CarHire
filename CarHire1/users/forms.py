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
        fields = [
            'first_name', 'last_name', 'email',
            'phone_number', 'date_of_birth',
            'street_address', 'city', 'postal_code', 'country',
            'license_number', 'license_country', 'license_expiry',
            'license_image', 'has_international_permit',
            'international_permit_number', 'international_permit_expiry'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'international_permit_expiry': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['email'].required = True
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Set username to email
        if commit:
            user.save()
        return user

class CustomUserChangeForm(UserChangeForm):
    """
    Form for admin user changes
    """
    class Meta(UserChangeForm.Meta):
        model = CustomUser
        fields = [
            'email', 'first_name', 'last_name',
            'phone_number', 'date_of_birth',
            'street_address', 'city', 'postal_code', 'country',
            'license_number', 'license_country', 'license_expiry',
            'license_image', 'has_international_permit',
            'international_permit_number', 'international_permit_expiry',
            'is_active', 'is_staff'
        ]

class UserUpdateForm(forms.ModelForm):
    """
    Form for users to update their information
    """
    class Meta:
        model = CustomUser
        fields = [
            'first_name', 'last_name', 'email',
            'phone_number', 'date_of_birth',
            'street_address', 'city', 'postal_code', 'country',
            'license_number', 'license_country', 'license_expiry',
            'license_image', 'has_international_permit',
            'international_permit_number', 'international_permit_expiry'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'international_permit_expiry': forms.DateInput(attrs={'type': 'date'}),
        }

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