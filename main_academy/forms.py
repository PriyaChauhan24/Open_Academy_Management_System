from django import forms
from .models import User, Course

# 1. PROFESSIONAL COURSE FORM
# Handles Technical/Non-Tech selection and Live Lecture links
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            'title', 
            'description', 
            'category', 
            'is_paid', 
            'price', 
            'live_lecture_link',  # Matches your new Model name
            'thumbnail'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Course Title'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control', 'placeholder': 'Enter course details...'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'live_lecture_link': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Zoom/Google Meet URL'}),
            'thumbnail': forms.FileInput(attrs={'class': 'form-control'}),
        }

# 2. STUDENT REGISTRATION FORM
# Includes the Enrollment Number required for your Academy System
class StudentRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Create a strong password'
    }))
    
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 
        'placeholder': 'Confirm your password'
    }))

    class Meta:
        model = User
        fields = ['username', 'email', 'enrollment_number', 'password']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enrollment Number (e.g. 2101...)'}),
        }

    # Custom validation to check if passwords match
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirm_password = cleaned_data.get("confirm_password")

        if password != confirm_password:
            raise forms.ValidationError("Passwords do not match!")
        return cleaned_data