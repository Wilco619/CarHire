from django import forms
from .models import Car, CarCategory

class CarForm(forms.ModelForm):
    class Meta:
        model = Car
        fields = [
            'name', 'make', 'model', 
            'description', 'category',
            'year', 'transmission', 
            'fuel_type', 'seats', 
            'daily_rate', 'image',
            'quantity'
        ]
        
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        if quantity < 1:
            raise forms.ValidationError("Number of units must be at least 1")
        return quantity

class CarCategoryForm(forms.ModelForm):
    class Meta:
        model = CarCategory
        fields = ['name', 'description']
        
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if CarCategory.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A category with this name already exists.")
        return name.title()