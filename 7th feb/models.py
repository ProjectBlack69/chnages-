from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, Group, Permission, BaseUserManager, User
from django.db import models
from django.conf import settings
import datetime
from django.forms import ValidationError
from django.utils.timezone import now
from datetime import datetime, timedelta
import uuid
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from decimal import Decimal, ROUND_HALF_UP
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging
from core.helpers import get_nationality_choices
from django_countries.fields import CountryField
logger = logging.getLogger(__name__)

# User and Profile-Related Models
class UserModuleManager(BaseUserManager):
    def create_user(self, email, password=None, role='customer', **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, role=role, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        
        # Create related models based on the role
        if role == 'admin' and not Admin.objects.filter(user=user).exists():
            Admin.objects.create(user=user)  # Create an Admin profile if not exists
        elif role == 'employee' and not Employee.objects.filter(user=user).exists():
            Employee.objects.create(user=user)  # Create an Employee profile if not exists
        elif role == 'customer' and not Customer.objects.filter(user=user).exists():
            Customer.objects.create(user=user)  # Create a Customer profile if not exists
        
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        # Ensure the role is set to 'admin' for superusers
        extra_fields.setdefault('role', 'admin')
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        # Create the user and the Admin profile
        user = self.create_user(email, password, **extra_fields)
        if not Admin.objects.filter(user=user).exists():
            Admin.objects.create(user=user)  # Create Admin profile for superuser if not exists
        return user

    def get_by_natural_key(self, email):
        return self.get(email=email)

class UserModule(AbstractBaseUser, PermissionsMixin):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('customer', 'Customer'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='customer')

    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_created = models.DateTimeField(auto_now_add=True)

    objects = UserModuleManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    groups = models.ManyToManyField(
        Group,
        related_name='user_module_set',
        blank=True,
        help_text="Groups this user belongs to."
    )
    
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='user_module_permissions_set',
        blank=True,
        help_text="Specific permissions for this user."
    )

    def __str__(self):
        return self.email

    
class UserRole(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class ActivityLog(models.Model):
    user = models.ForeignKey(UserModule, on_delete=models.CASCADE)
    action = models.CharField(max_length=100)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.action} at {self.timestamp}"
    
class Notification(models.Model):
    recipient = models.ForeignKey(UserModule, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.recipient.username}: {self.title}"

class Admin(models.Model):
    user = models.OneToOneField(UserModule, on_delete=models.CASCADE, related_name='admin_profile')
    managed_cruises = models.ManyToManyField('Cruise', related_name='managed_by_admin')

    def __str__(self):
        return f"Admin: {self.user.username}"
    
ROLE_HIERARCHY = {
    'deck': ['captain', 'staff_captain', 'navigation_officer', 'safety_officer', 'deckhand'],
    'engine': ['chief_engineer', 'second_engineer', 'third_engineer', 'electrician', 'oiler'],
    'hotel': ['hotel_director', 'executive_housekeeper', 'cabin_steward', 'guest_relations_officer', 'receptionist'],
    'food_and_beverage': ['executive_chef', 'sous_chef', 'pastry_chef', 'bartender', 'waiter_waitress', 'busser'],
    'entertainment': ['cruise_director', 'show_performer', 'dj', 'activity_coordinator', 'kids_club_coordinator'],
    'medical': ['ship_doctor', 'nurse', 'paramedic'],
    'retail_and_sales': ['boutique_manager', 'sales_associate', 'jewelry_assistant'],
    'security': ['chief_security_officer', 'security_trainer', 'security_guard'],
    'it_and_communication': ['it_manager', 'network_specialist', 'av_specialist'],
    'spa_and_wellness': ['spa_manager', 'therapist', 'beautician', 'storekeeper'],
    'logistics_and_supply': ['provision_manager', 'supply_officer', 'storekeeper'],
    'cruise_operations_and_administration': ['cruise_manager', 'hr_manager', 'administrative_assistant'],
}

class Employee(models.Model): 
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField('UserModule', on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100, blank=True, null=True)  
    last_name = models.CharField(max_length=100, blank=True, null=True)   
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES, 
        default='M', 
        blank=True, 
        null=True
    )  # Default set to Male
    phone = models.CharField(max_length=15, blank=True, null=True)        
    address = models.TextField(blank=True, null=True)                     
    city = models.CharField(max_length=100, blank=True, null=True)        
    pincode = models.CharField(max_length=10, blank=True, null=True)      
    nationality = models.CharField(
        max_length=50,
        choices=get_nationality_choices(),
        blank=True,
        null=True
    )
    employee_id = models.CharField(max_length=50, unique=True, default='12')
    position = models.ForeignKey('Position', on_delete=models.SET_NULL, null=True)
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True, blank=True) 
    skills = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    previous_experience = models.TextField(blank=True, null=True)         
    willingness_to_relocate = models.BooleanField(default=False)          
    job_role = models.CharField(max_length=100, blank=True, null=True)   
    availability_date = models.DateField(blank=True, null=True)           
    application_date = models.DateField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    supervisor = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='subordinates'
    )

    def get_department_role_hierarchy(self):
        """
        Retrieves the department and role hierarchy for the employee's job role.
        """
        for department, roles in ROLE_HIERARCHY.items():
            print(f"Checking department: {department} with roles: {roles}")
            if self.job_role in roles:
                print(f"Found department: {department} and roles: {roles}")
                return department, roles
        return None, None
    
    def get_roles_for_department(self, department):
        """
        Retrieves the list of roles for the specified department.
        """
        for dep_name, roles in ROLE_HIERARCHY.items():
            # Check if the provided department matches the department in the hierarchy
            if dep_name == department.name.lower():  # Match by department name
                return roles
        return []

    def assign_supervisor(self):
        if not self.department or not self.position:
            logger.warning(f"Employee {self.employee_id} has no department or position assigned.")
            return

        # Fetch all positions in the department, ordered by position_order
        positions_in_department = Position.objects.filter(department=self.department).order_by('position_order')

        # Find the current position's order in the list
        current_position_index = next(
            (i for i, position in enumerate(positions_in_department) if position == self.position),
            None
        )

        if current_position_index is not None and current_position_index > 0:
            # Supervisor is the position immediately before in position_order
            supervisor_position = positions_in_department[current_position_index - 1]

            # Find an employee with the supervisor's position in the same department
            self.supervisor = Employee.objects.filter(
                department=self.department, 
                position=supervisor_position
            ).first()

            if self.supervisor:
                logger.info(f"Assigned Supervisor: {self.supervisor} for Employee {self.employee_id}")
            else:
                logger.warning(f"No supervisor found with position {supervisor_position} in department {self.department.name}")
        else:
            logger.info(f"Employee {self.employee_id} holds the topmost position in department {self.department.name}")



    def clean(self):
        if self.phone and not self.phone.isdigit():
            raise ValidationError("Phone number must contain only digits.")
        if self.pincode and len(self.pincode) != 6:
            raise ValidationError("Pincode must be exactly 6 digits.")

    def save(self, *args, **kwargs):
        """
        Overrides the save method to ensure supervisor assignment logic is applied.
        """
        if self.supervisor is None:  # Assign supervisor if not already assigned
            self.assign_supervisor()

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.first_name or 'N/A'} {self.last_name or 'N/A'} ({self.department.name if self.department else 'N/A'}) - {self.job_role or 'N/A'}"

class ChangeRequest(models.Model):
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE, related_name='change_requests')
    field_name = models.CharField(max_length=255)
    old_value = models.TextField()
    new_value = models.TextField()
    is_approved = models.BooleanField(null=True)  # Null = Pending, True = Approved, False = Rejected
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Change Request for {self.employee.user.username} - {self.field_name}"
    
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Position(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="positions")
    position_order = models.IntegerField(default=0)  # Define a numeric order for the role hierarchy

    def __str__(self):
        return f"{self.title} ({self.department.name})"

class Customer(models.Model):
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='customer_profile'
    )
    first_name = models.CharField(max_length=50, blank=True, null=True)  
    last_name = models.CharField(max_length=50, blank=True, null=True)   
    loyalty_points = models.IntegerField(default=0)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(
        max_length=10, 
        choices=GENDER_CHOICES, 
        blank=True, 
        null=True
    )
    nationality = models.CharField(
        max_length=50,
        choices=get_nationality_choices(),
        blank=True,
        null=True
    )
    emergency_contact = models.CharField(max_length=15, blank=True, null=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    loyalty_program = models.OneToOneField(
        'LoyaltyProgram', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='customer_profile'
    )
    loyalty_member = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=50, blank=True, null=True)
    preferred_currency = models.CharField(max_length=10, blank=True, null=True)

    def cancel_loyalty_program(self):
        """Cancel the customer's loyalty program membership."""
        self.loyalty_member = False
        if self.loyalty_program:  # If the customer has a linked loyalty program
            self.loyalty_program.delete()  # Remove the associated LoyaltyProgram instance
        self.save()

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"Customer: {self.user.username}"


class LoyaltyProgram(models.Model):
    customer = models.OneToOneField(
        'Customer', 
        on_delete=models.CASCADE, 
        related_name='loyalty_program_instance'
    )
    points = models.IntegerField(default=0)
    level = models.CharField(max_length=50, default='Bronze')
    loyalty_card_number = models.CharField(max_length=16, unique=True, default=0)
    password = models.CharField(max_length=128, null=True, blank=True)  # Allow null temporarily

    def __str__(self):
        return f"Loyalty Program for {self.customer.user.username}"

class SpecialRequest(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    request_type = models.CharField(max_length=255)
    details = models.TextField()
    priority_level = models.CharField(max_length=50, choices=[('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High')], default='Medium')
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="Pending")

    def __str__(self):
        return f"{self.customer.user.username} - {self.request_type}"

# Cruise-Related Models
class Cruise(models.Model):
    CRUISE_TYPES = [
        ('Tropical', 'Tropical/Caribbean Cruise'),
        ('Adventure', 'Expedition/Adventure Cruise'),
        ('Cultural', 'Cultural/European Cruise'),
        ('River', 'River Cruise'),
    ]
    name = models.CharField(max_length=100)
    destination = models.OneToOneField('Destination', on_delete=models.CASCADE, related_name='cruise')
    start_date = models.DateField()
    end_date = models.DateField()
    cabins_available = models.IntegerField()
    price_per_person = models.DecimalField(max_digits=10, decimal_places=2, default=100.0)
    available_seats = models.IntegerField(default=0)
    cruise_type = models.CharField(max_length=50, choices=CRUISE_TYPES, default='Tropical')
    price_per_room_type = models.JSONField(default=dict)
    image_url = models.CharField(max_length=500, blank=True, null=True)
    description = models.TextField(blank=True, null=True) 

    def update_seat_availability(self, increment=True):
        """
        Safely updates the available_seats field.
        - Increment: Adds one seat (default).
        - Decrement: Subtracts one seat if greater than 0.
        """
        if increment:
            self.available_seats += 1
        elif self.available_seats > 0:
            self.available_seats -= 1
        self.save()
    
    def get_duration(self):
        """
        Returns a string in the format 'start_date - end_date (days)'.
        """
        if self.start_date and self.end_date:
            duration_days = (self.end_date - self.start_date).days
            return f"{self.start_date.strftime('%b %d, %Y')} - {self.end_date.strftime('%b %d, %Y')} ({duration_days} days)"
        return "Dates not set"

    def __str__(self):
        destination_name = self.destination.name if self.destination else "No destination"
        return f"Cruise: {self.name} to {destination_name}"



class Destination(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    average_temperature = models.CharField(max_length=50, blank=True, null=True)
    best_time_to_visit = models.CharField(max_length=100, blank=True, null=True)
    activities = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class OnboardService(models.Model):
    service_name = models.CharField(max_length=100)
    service_type = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)
    duration = models.CharField(max_length=50, blank=True, null=True)
    availability = models.BooleanField(default=True)
    additional_info = models.TextField(blank=True, null=True)
    service_category = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image_url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        # Return a string without referencing cruise
        return f"Service: {self.service_name} ({self.service_type})"

# Booking and Payment Models

class Payment(models.Model):
    booking = models.OneToOneField('Booking', on_delete=models.CASCADE, related_name='payment_booking')  # Changed related_name to avoid conflict
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateField(auto_now_add=True)
    is_refunded = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, default=uuid.uuid4)
    payment_method = models.CharField(max_length=50, choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Bank Transfer', 'Bank Transfer')], default='Credit Card')

    def save(self, *args, **kwargs):
        # Ensure that transaction_id is set only once
        if not self.transaction_id:
            self.transaction_id = str(uuid.uuid4())
        super(Payment, self).save(*args, **kwargs)

    def __str__(self):
        return f"Payment for {self.booking.cruise.name}, Amount: {self.amount}, Transaction ID: {self.transaction_id}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('Paused', 'Paused'),
        ('Pending', 'Pending'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Restarted', 'Restarted'),
    ]

    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='booking_list')
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE)
    booking_date = models.DateField(auto_now_add=True)  # Automatically set when booking is created
    additional_instructions = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    payment_status = models.CharField(
        max_length=50,
        choices=[('Unpaid', 'Unpaid'), ('Paid', 'Paid')],
        default='Unpaid'  # Default payment status is Unpaid
    )
    
    # Fields related to the form
    travel_insurance = models.BooleanField(default=False)  # Whether the user opted for travel insurance
    room_type = models.CharField(
        max_length=50,
        choices=[('Economy', 'Economy'), ('Business', 'Business'), ('First Class', 'First Class')],
        default='Economy'  # Default room type
    )
    onboard_services = models.ManyToManyField('OnboardService', blank=True)  # Many-to-many with onboard services
    special_request = models.TextField(blank=True, null=True, help_text="Any special requests from the customer")
    loyalty_program_member = models.BooleanField(default=False)  # Whether the user is a loyalty program member
    loyalty_card_number = models.CharField(max_length=50, blank=True, null=True)  # Optional loyalty card number
    loyalty_pass = models.CharField(max_length=50, blank=True, null=True)  # Optional special pass
    loyalty_level = models.CharField(
        max_length=20,
        choices=[('Diamond','Diamond'), ('Gold', 'Gold'), ('Silver', 'Silver'), ('Bronze', 'Bronze')],
        blank=True,
        null=True
    )
    cabin_number = models.CharField(max_length=10, blank=True, null=True, help_text="Assigned cabin number")
    deck_number = models.IntegerField(blank=True, null=True, help_text="Assigned deck number")
    children_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Optional child discount percentage
    elderly_discount = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)  # Optional elderly discount percentage
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.0, blank=True, null=True)
    payment_method = models.CharField(
        max_length=50,
        choices=[('Credit Card', 'Credit Card'), ('PayPal', 'PayPal'), ('Bank Transfer', 'Bank Transfer')],
        default='Credit Card'
    )
    number_of_passengers = models.PositiveIntegerField(default=1)  # Number of passengers included in the booking

    def calculate_total_price(self):
        # Calculate base price as price per passenger multiplied by the number of passengers
        num_passengers = self.passengers.count()
        base_price = Decimal(self.cruise.price_per_person) * Decimal(num_passengers)

        # Handle room price calculation directly from the price per room type
        room_price_value = self.cruise.price_per_room_type.get(self.room_type, 100)  # Default to 100 if room type not found
        room_price = Decimal(room_price_value)  # Convert to Decimal for correct calculations

        # Calculate total service price
        service_price = sum(Decimal(service.price) for service in self.onboard_services.all())

        # Travel insurance price as 5% of the sum of base price, room price, and services
        travel_insurance_price = (base_price + room_price + service_price) * Decimal(0.05)

        # Tax as 10% of the sum of all applicable charges
        tax = (base_price + room_price + service_price + travel_insurance_price) * Decimal(0.10)

        # Total base price (excluding discounts)
        total_base_price = base_price + room_price + service_price

        # Loyalty discount calculation
        loyalty_discount = Decimal(0)
        if self.loyalty_program_member and hasattr(self.customer, 'loyalty_program'):
            loyalty_program = self.customer.loyalty_program
            loyalty_discount = Decimal(loyalty_program.points) * Decimal(0.05)  # 5% per point

        # Discounts for passengers based on age
        discount = Decimal(0)
        for passenger in self.passengers.all():
            if passenger.age <= 12:  # Child discount (15%)
                discount += total_base_price * Decimal(0.15)
            elif passenger.age >= 60:  # Elderly discount (10%)
                discount += total_base_price * Decimal(0.10)

        # Final price calculation
        final_price = total_base_price + tax + travel_insurance_price - loyalty_discount - discount

        # Round the final price to 3 decimal places
        final_price_rounded = final_price.quantize(Decimal('0.001'), rounding=ROUND_HALF_UP)

        # Update the total price field
        self.total_price = final_price_rounded
        self.save()

        return final_price_rounded
    
    def save(self, *args, **kwargs):
        # Handle cabin and deck assignment before saving
        if not self.cabin_number:
            if self.id:  # Ensure the ID exists (i.e., the object is saved)
                self.cabin_number = f"C{self.id % 100}"  # Example: Cabin number logic
            else:
                self.cabin_number = f"C{0}"  # Assign default if ID is not yet available (e.g., when creating new booking)
        
        if not self.deck_number:
            if self.id:  # Ensure the ID exists (i.e., the object is saved)
                self.deck_number = (self.id % 5) + 1  # Example: Deck number logic
            else:
                self.deck_number = 1  # Assign default deck number if ID is not yet available (e.g., when creating new booking)

        # Update cruise availability if the booking is confirmed
        if self.pk:  # Only for existing bookings
            old_status = Booking.objects.get(pk=self.pk).status
            if old_status != 'Confirmed' and self.status == 'Confirmed':
                if self.cruise.available_seats > 0:
                    self.cruise.available_seats -= 1
                    self.cruise.save()
                else:
                    raise ValueError("No seats available on this cruise.")

        # Save the booking first
        super().save(*args, **kwargs)

        # Always update or create CustomerBooking if the booking is confirmed
        if self.status == 'Confirmed':
            # Create or update the CustomerBooking for this confirmed booking
            customer_booking, created = CustomerBooking.objects.update_or_create(
                booking=self,
                defaults={
                    'customer': self.customer,
                    'status': self.status,
                    'booking_type': 'VIP' if self.customer.loyalty_program else 'Regular',
                }
            )

            # Sync related services to the CustomerBooking
            customer_booking.related_services.set(self.onboard_services.all())
            customer_booking.save()

    def __str__(self):
        return f"Booking: {self.cruise.name} by {self.customer.user.username}"


@receiver(post_save, sender=Booking)
def update_customer_booking(sender, instance, created, **kwargs):
    """Ensure CustomerBooking is updated or created when a Booking is saved, especially when confirmed."""
    
    # If the booking's status is confirmed, create or update the CustomerBooking entry
    if instance.status == 'Confirmed':
        # Create or update the CustomerBooking for the confirmed booking
        customer_booking, _ = CustomerBooking.objects.update_or_create(
            booking=instance,
            defaults={
                'customer': instance.customer,
                'status': instance.status,
                'booking_type': 'VIP' if instance.customer.loyalty_program else 'Regular',
            }
        )
        
        # Sync related onboard services to the CustomerBooking
        customer_booking.related_services.set(instance.onboard_services.all())
        customer_booking.save()

class Passenger(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='passengers')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    age = models.PositiveIntegerField(default=0)  
    gender = models.CharField(
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')],
        blank=True,
        null=True
    )
    passport_number = models.CharField(max_length=50)
    nationality = models.CharField(
        max_length=50,
        choices=get_nationality_choices(),
        blank=True,
        null=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.booking.cruise.name})"
    
class CustomerBooking(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='customer_bookings')
    cruise = models.ForeignKey(Cruise, null=True, blank=True, on_delete=models.SET_NULL)
    booking = models.OneToOneField(
        Booking,
        on_delete=models.SET_NULL,  
        null=True,                  
        blank=True
    )
    status = models.CharField(
        max_length=50, 
        choices=[
            ('Confirmed', 'Confirmed'), 
            ('Pending', 'Pending'), 
            ('Canceled', 'Canceled'), 
            ('Completed', 'Completed')
        ], 
        default='Pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)  # Automatically set on creation
    updated_at = models.DateTimeField(auto_now=True)  # Automatically updated on save
    booking_type = models.CharField(
        max_length=50, 
        choices=[('Regular', 'Regular'), ('VIP', 'VIP')], 
        default='Regular'
    )
    cancellation_reason = models.TextField(null=True, blank=True)  # Only applicable for 'Canceled'
    related_services = models.ManyToManyField(OnboardService, related_name='customer_bookings', blank=True)
    refund_approved = models.BooleanField(default=False)  

    def __str__(self):
        cruise_name = self.cruise.name if self.cruise else "No Cruise Assigned"
        return f"Booking for {self.customer.user.username} - {cruise_name} ({self.status})"

    def cancel_booking(self, reason):
        """Cancel the booking and record the reason."""
        if self.status != 'Canceled':
            self.status = 'Canceled'
            self.cancellation_reason = reason
            self.save()

    def mark_as_completed(self):
        """Mark a booking as completed."""
        if self.status not in ['Completed', 'Canceled']:
            self.status = 'Completed'
            self.save()

    def approve_refund(self):
        """Approve the refund for the booking."""
        if not self.refund_approved:
            self.refund_approved = True
            self.save()

# Signal to ensure related fields are updated as needed
@receiver(post_save, sender=Booking)
def update_or_create_customer_booking(sender, instance, created, **kwargs):
    """Create or update CustomerBooking for Confirmed or Canceled bookings."""
    if instance.status in ['Confirmed', 'Canceled']:
        # Create or update the CustomerBooking for confirmed or canceled bookings
        customer_booking, created = CustomerBooking.objects.update_or_create(
            booking=instance,
            defaults={
                'customer': instance.customer,
                'status': instance.status,
                'booking_type': 'VIP' if instance.loyalty_program_member else 'Regular',
                'cruise': instance.cruise,  # Save the cruise field from Booking
            }
        )
        # Sync related onboard services to the CustomerBooking
        customer_booking.related_services.set(instance.onboard_services.all())
        customer_booking.save()
    elif instance.status == 'Pending':
        # Do nothing for Pending bookings but retain existing records
        pass

@receiver(pre_delete, sender=Booking)
def preserve_customer_booking(sender, instance, **kwargs):
    """ Preserve the Cruise in CustomerBooking when Booking is deleted. """
    customer_booking = CustomerBooking.objects.filter(booking=instance).first()
    
    if customer_booking:
        # Preserve the cruise in CustomerBooking
        cruise = customer_booking.cruise  # Get the associated cruise
        
        # Log the cruise for debugging purposes
        if cruise:
            print(f"Preserving Cruise: {cruise.name}")

        # Disassociate the Booking by setting booking to None
        customer_booking.booking = None
        customer_booking.save()


class Invoice(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='invoice')
    issued_date = models.DateField(auto_now_add=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True, blank=True)
    status = models.CharField(max_length=50, default='Issued')

    def __str__(self):
        return f"Invoice for {self.booking}"

class RefundRequest(models.Model):
    booking = models.ForeignKey(
        'Booking',  # Reference to the Booking model
        on_delete=models.PROTECT,  # Prevent deletion of RefundRequest when Booking is deleted
        related_name='refund_requests'
    )
    request_date = models.DateField(auto_now_add=True)
    is_approved = models.BooleanField(default=False)
    final_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    notes = models.TextField(blank=True, null=True)
    name = models.CharField(max_length=100, default="unknown")

    def clean(self):
        if not isinstance(self.final_price, (int, float, Decimal)):
            raise ValidationError("Final price must be a valid decimal number.")

    def __str__(self):
        return f"Refund Request for {self.booking}"

# Employee Management and Task Models

class JobApplication(models.Model):
    # Job role choices by department
    DEPARTMENT_ROLES = {
        'deck': [
            ('captain', 'Captain'),
            ('staff_captain', 'Staff Captain'),
            ('navigation_officer', 'Navigation Officer'),
            ('safety_officer', 'Safety Officer'),
            ('deckhand', 'Deckhand'),
        ],
        'engine': [
            ('chief_engineer', 'Chief Engineer'),
            ('second_engineer', 'Second Engineer'),
            ('third_engineer', 'Third Engineer'),
            ('electrician', 'Electrician'),
            ('oiler', 'Oiler'),
        ],
        'hotel': [
            ('hotel_director', 'Hotel Director'),
            ('executive_housekeeper', 'Executive Housekeeper'),
            ('cabin_steward', 'Cabin Steward/Stewardess'),
            ('guest_relations_officer', 'Guest Relations Officer'),
            ('receptionist', 'Receptionist'),
        ],
        'food_and_beverage': [
            ('executive_chef', 'Executive Chef'),
            ('sous_chef', 'Sous Chef'),
            ('pastry_chef', 'Pastry Chef'),
            ('bartender', 'Bartender'),
            ('waiter_waitress', 'Waiter/Waitress'),
            ('busser', 'Busser'),
        ],
        'entertainment': [
            ('cruise_director', 'Cruise Director'),
            ('show_performer', 'Show Performer'),
            ('dj', 'DJ'),
            ('activity_coordinator', 'Activity Coordinator'),
            ('kids_club_coordinator', 'Kids Club Coordinator'),
        ],
        'medical': [
            ('ship_doctor', 'Ship Doctor'),
            ('nurse', 'Nurse'),
            ('paramedic', 'Paramedic'),
        ],
        'retail_and_sales': [
            ('boutique_manager', 'Boutique Manager'),
            ('sales_associate', 'Sales Associate'),
            ('jewelry_assistant', 'Jewelry Assistant'),
        ],
        'security': [
            ('chief_security_officer', 'Chief Security Officer'),
            ('security_guard', 'Security Guard'),
            ('security_trainer', 'Security Trainer'),
        ],
        'it_and_communication': [
            ('it_manager', 'IT Manager'),
            ('network_specialist', 'Network Specialist'),  # Fixed typo here
            ('av_specialist', 'AV Specialist'),
        ],
        'spa_and_wellness': [
            ('spa_manager', 'Spa Manager'),
            ('therapist', 'Therapist'),
            ('storekeeper', 'Storekeeper'),
            ('beautician', 'Beautician'),
        ],
        'logistics_and_supply': [
            ('provision_manager', 'Provision Manager'),
            ('storekeeper', 'Storekeeper'),  # Fixed the curly braces issue
            ('supply_officer', 'Supply Officer'),
        ],
        'cruise_operations_and_administration': [
            ('cruise_manager', 'Cruise Manager'),
            ('administrative_assistant', 'Administrative Assistant'),
            ('hr_manager', 'HR Manager'),
        ],
    }

    job_role_choices = [
        *DEPARTMENT_ROLES['deck'],
        *DEPARTMENT_ROLES['engine'],
        *DEPARTMENT_ROLES['hotel'],
        *DEPARTMENT_ROLES['food_and_beverage'],
        *DEPARTMENT_ROLES['entertainment'],
        *DEPARTMENT_ROLES['medical'],
        *DEPARTMENT_ROLES['retail_and_sales'],
        *DEPARTMENT_ROLES['security'],
        *DEPARTMENT_ROLES['it_and_communication'],
        *DEPARTMENT_ROLES['spa_and_wellness'],
        *DEPARTMENT_ROLES['logistics_and_supply'],
        *DEPARTMENT_ROLES['cruise_operations_and_administration'],
    ]

    job_role = models.CharField(
        max_length=50,
        choices=job_role_choices
    )

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('reviewed', 'Reviewed'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    # Personal Details
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    date_of_birth = models.DateField()
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES,  
        blank=True, 
        null=True
    ) 
    availability_date = models.DateField()

    # Address
    address = models.TextField()
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    nationality = models.CharField(
        max_length=50,
        choices=get_nationality_choices(),
        blank=True,
        null=True
    )

    # Application Details
    previous_experience = models.TextField(blank=True)
    willingness_to_relocate = models.CharField(
        max_length=4,
        choices=[('yes', 'Yes'), ('no', 'No'), ('none', 'None')],
        default='none'
    )  # Optional additional field
    uploaded_cv = models.FileField(upload_to='uploads/cvs/')  # Stores the CV file

    # Metadata
    application_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pending'
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name} - {self.job_role}"

class Task(models.Model):
    description = models.TextField()
    due_date = models.DateField()
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"Task: {self.description}, Due: {self.due_date}"

class Shift(models.Model):
    SHIFT_TYPES = [
        ('Morning', 'Morning Shift'),
        ('Evening', 'Evening Shift'),
        ('Night', 'Night Shift'),
        ('Overnight', 'Overnight Shift'),
        ('MidDay', 'Mid Day Shift'),
    ]

    SHIFT_STATUS_CHOICES = [
        ('Scheduled', 'Scheduled'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Swapped', 'Swapped'),
        ('Pending', 'Pending'),
    ]

    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    day = models.CharField(max_length=10, null=True, blank=True)
    shift_type = models.CharField(max_length=20, choices=SHIFT_TYPES)
    start_time = models.TimeField(null=True, blank=True)
    end_time = models.TimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=SHIFT_STATUS_CHOICES, default='Scheduled')

    def __str__(self):
        return f'{self.day} - {self.shift_type} ({self.employee.user.email})'

class AssignmentShift(models.Model):
    ATTENDANCE_STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
        ('On Leave', 'On Leave'),
    ]

    shift = models.ForeignKey('Shift', on_delete=models.CASCADE)
    employee = models.ForeignKey('Employee', on_delete=models.CASCADE)
    attendance_status = models.CharField(
        max_length=20,
        choices=ATTENDANCE_STATUS_CHOICES,
        default='Absent'
    )
    date = models.DateField()
    shift_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    class Meta:
        unique_together = ('shift', 'employee', 'date')

    def __str__(self):
        return f"Attendance for {self.employee.user.email} on {self.date} - Shift: {self.shift.shift_type}"

    def mark_attendance(self, status):
        self.attendance_status = status
        if status == 'Present':
            self.shift_completed = True
        self.save()

    def complete_shift(self):
        self.shift_completed = True
        self.mark_attendance('Present')

class ShiftSwapRequest(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Cancelled', 'Cancelled'),
    ]

    employee_from = models.ForeignKey('Employee', related_name='shift_swap_from', on_delete=models.CASCADE, blank=True, null=True)
    employee_to = models.ForeignKey('Employee', related_name='shift_swap_to', on_delete=models.CASCADE, blank=True, null=True)
    shift_from = models.ForeignKey('Shift', on_delete=models.CASCADE, related_name='shift_swap_from', blank=True, null=True)
    shift_to = models.ForeignKey('Shift', on_delete=models.CASCADE, related_name='shift_swap_to', blank=True, null=True)
    swap_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Pending')
    reason = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_by = models.ForeignKey('Admin', null=True, blank=True, on_delete=models.SET_NULL)

    def __str__(self):
        return f"Swap Request: {self.employee_from.user.email} to {self.employee_to.user.email} on {self.swap_date} - Status: {self.status}"

    def approve(self):
        self.status = 'Approved'
        self.save()
        self.swap_shifts()

    def reject(self):
        self.status = 'Rejected'
        self.save()

    def cancel(self):
        self.status = 'Cancelled'
        self.save()

    def swap_shifts(self):
        # Swap shifts between employees
        self.shift_from.employee, self.shift_to.employee = self.shift_to.employee, self.shift_from.employee
        self.shift_from.save()
        self.shift_to.save()

# Promotions and Inventory Management
class Promotion(models.Model):
    title = models.CharField(max_length=100)
    start_date = models.DateField()
    end_date = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Campaign: {self.title}"

class CustomerSegment(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    criteria = models.TextField()  # Define criteria for segmentation

    def __str__(self):
        return f"Segment: {self.name}"

class Inventory(models.Model):
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE, related_name='inventory')
    item_name = models.CharField(max_length=100)
    quantity = models.IntegerField()

    def __str__(self):
        return f"Inventory: {self.item_name} on {self.cruise.name}"

# Feedback Models
class Feedback(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='feedbacks')
    cruise = models.ForeignKey(Cruise, on_delete=models.CASCADE, related_name='feedbacks')
    rating = models.PositiveIntegerField(default=0)
    comments = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Feedback by {self.customer.user.username} for {self.cruise.name}"

class Itinerary(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='itineraries')
    day = models.IntegerField()
    activity = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return f"Itinerary Day {self.day} for {self.booking}"
    
def get_default_virtual_time():
    return datetime.now().time()
    
class VirtualClock(models.Model):
    current_day_choices = [
        ('Today', 'Today'),
        ('Tomorrow', 'Tomorrow'),
    ]
    
    current_day = models.CharField(max_length=10, choices=current_day_choices, default='Today')
    virtual_time = models.TimeField(default=get_default_virtual_time)
    paused = models.BooleanField(default=True)

    def __str__(self):
        return f"Virtual Clock for {self.current_day} set to {self.virtual_time}"

    def get_virtual_time(self):
        """
        This method returns the virtual time based on the current day and the manually set virtual time.
        """
        current_time = datetime.now()  # Get the current time
        if self.current_day == 'Tomorrow':
            current_time += timedelta(days=1)  # Adjust the time to tomorrow if the virtual clock is set to 'Tomorrow'
        
        virtual_time = current_time.replace(hour=self.virtual_time.hour, minute=self.virtual_time.minute, second=0, microsecond=0)
        return virtual_time

    def get_real_time(self):
        """
        This method returns the actual current real time.
        """
        return datetime.now().strftime('%H:%M:%S')

    def reset_to_real_time(self):
        """
        Resets the virtual time to the current real time.
        """
        self.virtual_time = datetime.now().time()
        self.save()