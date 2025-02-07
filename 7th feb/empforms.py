from django import forms
from core.models import JobApplication, Employee
from django.contrib.auth.forms import AuthenticationForm, UserChangeForm
from django.contrib.auth import authenticate

class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = JobApplication
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth', 'gender',
            'job_role', 'availability_date', 'city', 'pincode', 'willingness_to_relocate',
            'nationality', 'address', 'previous_experience', 'uploaded_cv'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form_control', 'placeholder': 'Enter your first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form_control', 'placeholder': 'Enter your last name'}),
            'email': forms.EmailInput(attrs={'class': 'form_control', 'placeholder': 'Enter your email'}),
            'phone': forms.TextInput(attrs={'class': 'form_control', 'placeholder': 'Enter your phone number'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form_control', 'type': 'date'}),
            'job_role': forms.Select(attrs={'class': 'form_control'}),
            'gender': forms.Select(attrs={'class': 'form_control'}),
            'availability_date': forms.DateInput(attrs={'class': 'form_control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'textarea_control', 'placeholder': 'Enter your address'}),
            'city': forms.TextInput(attrs={'class': 'form_control', 'placeholder': 'Enter your city'}),
            'pincode': forms.TextInput(attrs={'class': 'form_control', 'placeholder': 'Enter Pincode'}),
            'nationality': forms.Select(attrs={'class': 'form_control', 'placeholder': 'Enter your nationality'}),
            'previous_experience': forms.Textarea(attrs={'class': 'textarea_control', 'placeholder': 'Describe your previous cruise experience(if any)'}),
            'willingness_to_relocate': forms.Select(attrs={'class': 'form_control'}),
            'uploaded_cv': forms.FileInput(attrs={'class': 'form_control'}),
        }

class EmployeeLoginForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={
            "placeholder": "Enter your email",
            "class": "form-control",
        }),
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={
            "placeholder": "Enter your password",
            "class": "form-control",
        }),
    )

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get("username")  # Username is mapped to email
        password = cleaned_data.get("password")

        # Custom authentication
        user = authenticate(email=email, password=password)
        if user is None:
            raise forms.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise forms.ValidationError("This account is inactive.")

        # Store the authenticated user for later use
        self.user = user
        return cleaned_data

class EmployeeProfileUpdateForm(UserChangeForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'employee_id', 'position', 'department', 'phone', 'skills', 'address', 'date_of_birth', 'linkedin_url']