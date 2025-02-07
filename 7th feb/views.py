from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.views import View
from django.http import Http404
from django.apps import apps
from django.http import JsonResponse, HttpResponse
from django.urls import reverse, NoReverseMatch
from django.forms import modelform_factory
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
import random, string, logging
from django.utils.crypto import get_random_string
import hashlib
from django.utils.timezone import now, localtime, make_aware
from datetime import datetime, timedelta
from django.contrib.auth.decorators import login_required
from core.models import (
    UserModule, Cruise, Destination, Booking, Employee, Customer,
    Task, Promotion, Inventory, Feedback, ActivityLog, OnboardService, Shift, ShiftSwapRequest,
    LoyaltyProgram, SpecialRequest, CustomerBooking, CustomerSegment, Payment, Invoice, 
    RefundRequest, Itinerary, Passenger, JobApplication, Department, Position, ChangeRequest, Notification, VirtualClock
)
from django.utils import timezone
from core.models import VirtualClock
from .forms import VirtualClockForm
from core.helpers import normalize_job_role
from datetime import time, date

logger = logging.getLogger(__name__)

# Main dashboard view
@login_required
def admin_dashboard(request):
    # Collect dynamic data for the dashboard
    dashboard_items = {
        'user_profile_related': [
            {"title": "Users", "count": UserModule.objects.count(), "url": 'usermodule_list', "color": 'deep-ocean'},
            {"title": "Employees", "count": Employee.objects.count(), "url": 'employee_list', "color": 'tropical-water'},
            {"title": "Customers", "count": Customer.objects.count(), "url": 'customer_list', "color": 'sandy-beach'},
        ],
        'cruise_related': [
            {"title": "Cruises", "count": Cruise.objects.count(), "url": 'cruise_list', "color": 'deep-ocean'},
            {"title": "Destinations", "count": Destination.objects.count(), "url": 'destination_list', "color": 'tropical-water'},
            {"title": "Onboard Services", "count": OnboardService.objects.count(), "url": 'onboardservice_list', "color": 'sandy-beach'},
        ],
        'booking_and_payment': [
            {"title": "Bookings", "count": Booking.objects.count(), "url": 'booking_list', "color": 'deep-ocean'},
            {"title": "Passengers", "count": Passenger.objects.count(), "url": 'passenger_list', "color": 'tropical-water'},
            {"title": "Customer Bookings", "count": CustomerBooking.objects.count(), "url": 'customerbooking_list', "color": 'sandy-beach'},
            {"title": "Payments", "count": Payment.objects.count(), "url": 'payment_list', "color": 'deep-ocean'},
            {"title": "Invoices", "count": Invoice.objects.count(), "url": 'invoice_list', "color": 'tropical-water'},
        ],
        'employee_management': [
            {"title": "Tasks", "count": Task.objects.count(), "url": 'task_list', "color": 'deep-ocean'},
            {"title": "Shifts", "count": Shift.objects.count(), "url": 'shift_list', "color": 'tropical-water'},
            {"title": "Shift Swap Requests", "count": ShiftSwapRequest.objects.count(), "url": 'shiftswaprequest_list', "color": 'sandy-beach'},
            {"title": "Loyalty Program", "count": LoyaltyProgram.objects.count(), "url": 'loyaltyprogram_list', "color": 'deep-ocean'},
            {"title": "Special Requests", "count": SpecialRequest.objects.count(), "url": 'specialrequest_list', "color": 'tropical-water'},
            {"title": "Customer Segments", "count": CustomerSegment.objects.count(), "url": 'customersegment_list', "color": 'sandy-beach'},
            {"title": "Departments", "count": Department.objects.count(), "url": 'department_list', "color": 'deep-ocean'},
            {"title": "Positions", "count": Position.objects.count(), "url": 'position_list', "color": 'tropical-water'},
        ],
        'activity_and_logging': [
            {"title": "Activity Log", "count": ActivityLog.objects.count(), "url": 'activitylog_list', "color": 'deep-ocean'},
            {"title": "Notifications", "count": Notification.objects.count(), "url": 'notification_list', "color": 'tropical-water'},
        ],
        'inventory_management': [
            {"title": "Inventory", "count": Inventory.objects.count(), "url": 'inventory_list', "color": 'deep-ocean'},
        ],
        'feedback_and_itinerary': [
            {"title": "Feedback", "count": Feedback.objects.count(), "url": 'feedback_list', "color": 'deep-ocean'},
            {"title": "Itineraries", "count": Itinerary.objects.count(), "url": 'itinerary_list', "color": 'tropical-water'},
        ],
        'actions': {  # New actions section
            'employee': [
                {"title": "Job Applications", "count": JobApplication.objects.count(), "url": 'jobapplication_list', "color": 'deep-ocean'},
                {"title": "Change Requests", "count": ChangeRequest.objects.count(), "url": 'changerequest_list', "color": 'tropical-water'},
            ],
            'admin': [
                {"title": "Assign Shifts", "count": 0, "url": 'assign_shift_to_employee', "color": 'deep-ocean'},
                {"title": "View All Models", "count": 0, "url": 'all_models_list', "color": 'tropical-water'},
                {"title": "Virtual Clock", "count": 0, "url": 'virtual_clock_list', "color": 'sandy-beach'},
            ],
            'customer': [
                {"title": "Refund Requests", "count": RefundRequest.objects.count(), "url": 'refundrequest_list', "color": 'deep-ocean'},
            ],
        }
    }

    # Pass data to the template
    return render(request, 'admin_app/dashboard.html', {
        'user_profile_related': dashboard_items['user_profile_related'],
        'cruise_related': dashboard_items['cruise_related'],
        'booking_and_payment': dashboard_items['booking_and_payment'],
        'employee_management': dashboard_items['employee_management'],
        'activity_and_logging': dashboard_items['activity_and_logging'],
        'inventory_management': dashboard_items['inventory_management'],
        'feedback_and_itinerary': dashboard_items['feedback_and_itinerary'],
        'actions': dashboard_items['actions'],  # Pass the new actions group
    })

# View to list all VirtualClock instances
def virtual_clock_list(request):
    virtual_clocks = VirtualClock.objects.all()
    return render(request, 'admin_app/actions/virtual_clock_list.html', {
        'virtual_clocks': virtual_clocks
    })

# View to create a new VirtualClock
def create_virtual_clock(request):
    if request.method == 'POST':
        current_day = request.POST.get('current_day')
        virtual_time = request.POST.get('virtual_time')
        virtual_time = datetime.strptime(virtual_time, '%H:%M').time()

        VirtualClock.objects.create(current_day=current_day, virtual_time=virtual_time)
        return redirect('virtual_clock_list')

    return render(request, 'admin_app/actions/create_virtual_clock.html')

# View to edit a VirtualClock instance
def edit_virtual_clock(request, pk):
    virtual_clock = get_object_or_404(VirtualClock, pk=pk)

    if request.method == 'POST':
        virtual_clock.current_day = request.POST.get('current_day')
        virtual_clock.virtual_time = request.POST.get('virtual_time')
        virtual_clock.virtual_time = datetime.strptime(virtual_clock.virtual_time, '%H:%M').time()

        virtual_clock.save()
        return redirect('virtual_clock_list')

    return render(request, 'admin_app/actions/edit_virtual_clock.html', {
        'virtual_clock': virtual_clock
    })

# View to delete a VirtualClock instance
def delete_virtual_clock(request, pk):
    virtual_clock = get_object_or_404(VirtualClock, pk=pk)
    virtual_clock.delete()
    return redirect('virtual_clock_list')

def reset_virtual_clock(request, clock_id):
    try:
        virtual_clock = VirtualClock.objects.get(id=clock_id)
        # Reset the virtual time to the current real time
        virtual_clock.virtual_time = datetime.now().time()
        virtual_clock.save()
        return redirect('virtual_clock_list')  # Redirect back to the list after resetting
    except VirtualClock.DoesNotExist:
        return redirect('virtual_clock_list')  # Redirect if the clock is not found
    
def start_virtual_clock(request, clock_id):
    try:
        virtual_clock = VirtualClock.objects.get(id=clock_id)
        virtual_clock.paused = False
        virtual_clock.save()
        return JsonResponse({'message': 'Clock started'})
    except VirtualClock.DoesNotExist:
        return JsonResponse({'error': 'Clock not found'}, status=404)

def pause_virtual_clock(request, clock_id):
    try:
        virtual_clock = VirtualClock.objects.get(id=clock_id)
        virtual_clock.paused = True
        virtual_clock.save()
        return JsonResponse({'message': 'Clock paused'})
    except VirtualClock.DoesNotExist:
        return JsonResponse({'error': 'Clock not found'}, status=404)

def get_updated_virtual_time(request, clock_id):
    try:
        virtual_clock = VirtualClock.objects.get(id=clock_id)

        if virtual_clock.paused:
            return JsonResponse({'virtual_time': virtual_clock.virtual_time.strftime('%H:%M:%S')})

        current_time = datetime.now()
        if virtual_clock.current_day == 'Tomorrow':
            current_time += timedelta(days=1)

        virtual_time = current_time.replace(hour=virtual_clock.virtual_time.hour,
                                             minute=virtual_clock.virtual_time.minute,
                                             second=current_time.second,
                                             microsecond=current_time.microsecond)

        return JsonResponse({'virtual_time': virtual_time.strftime('%H:%M:%S')})

    except VirtualClock.DoesNotExist:
        return JsonResponse({'error': 'Clock not found'}, status=404)

@login_required
def usermodule_list(request):
    users = UserModule.objects.all()
    return render(request, 'admin_app/models/usermodule_list.html', {
        'users': users,
    })

@login_required
def cruise_list(request):
    cruises = Cruise.objects.all()
    return render(request, 'admin_app/models/cruise_list.html', {
        'cruises': cruises,
    })

# Define shift types and their corresponding times
SHIFT_DURATIONS = {
    'Morning': {'start': '06:00', 'end': '14:00'},
    'Evening': {'start': '14:00', 'end': '22:00'},
    'Night': {'start': '22:00', 'end': '06:00'},
    'Overnight': {'start': '00:00', 'end': '08:00'},
    'MidDay': {'start': '10:00', 'end': '18:00'},
}

@login_required
def shift_list(request):
    # Get all employees
    employees = Employee.objects.all()

    # Get all shifts (if any)
    shifts = Shift.objects.all()

    # Prepare a dictionary to store employee shift assignments
    employee_shifts = {}
    for employee in employees:
        employee_shifts[employee] = Shift.objects.filter(employee=employee)

    # Separate employees into those with and without shifts
    employees_with_shifts = [employee for employee, shifts in employee_shifts.items() if shifts]
    employees_without_shifts = [employee for employee, shifts in employee_shifts.items() if not shifts]

    # Adjust shift times for virtual vs real-time shifts
    for shift in shifts:
        # Check if the shift is using virtual time (Today or Tomorrow)
        if shift.day == "Today" or shift.day == "Tomorrow":
            # Do not convert virtual time to local time
            # Just use the virtual time directly (no changes)
            shift.start_time = shift.start_time
            shift.end_time = shift.end_time
        else:
            # Handle real-time shifts with timezone conversion
            if timezone.is_aware(shift.start_time):
                shift.start_time = timezone.localtime(shift.start_time)
            if timezone.is_aware(shift.end_time):
                shift.end_time = timezone.localtime(shift.end_time)

    return render(request, 'admin_app/models/shift_list.html', {
        'employees_with_shifts': employees_with_shifts,
        'employees_without_shifts': employees_without_shifts,
        'shifts': shifts,  # Pass the adjusted shifts to the template
        'current_day': localtime(now()).strftime('%Y-%m-%d'),
    })


def get_virtual_time():
    virtual_clock = VirtualClock.objects.first()  # Fetch the first available VirtualClock
    if virtual_clock:
        return make_aware(virtual_clock.get_virtual_time())  # Use its virtual time
    else:
        raise ValueError("No VirtualClock exists. Please create one to use the virtual time feature.")

def assign_shift_to_employee(request):
    # Try to fetch the VirtualClock instance, if it exists
    virtual_clock = VirtualClock.objects.first()  # Fetch the first available VirtualClock
    if not virtual_clock:
        # If no VirtualClock exists, show an error message and redirect
        messages.error(request, "No virtual clock is set up. Please create a virtual clock to proceed.")
        return redirect('admin_dashboard')  # Redirect to the dashboard or any fallback page

    # If VirtualClock exists, proceed with the logic
    virtual_time = get_virtual_time()
    today = virtual_time.date()
    tomorrow = today + timedelta(days=1)

    # Get employees without shifts for today and tomorrow
    employees_without_todays_shifts = Employee.objects.exclude(
        shift__day='Today', shift__status='Scheduled'
    ).distinct()
    employees_without_tomorrows_shifts = Employee.objects.exclude(
        shift__day='Tomorrow', shift__status='Scheduled'
    ).distinct()

    # Transition logic for virtual clock set to tomorrow
    if virtual_clock.current_day == 'Tomorrow':
        # Step 1: Fetch all scheduled shifts for "Tomorrow"
        tomorrows_shifts = Shift.objects.filter(day='Tomorrow', status='Scheduled')

        # Step 2: Replace today's shifts with tomorrow's shifts
        for shift in tomorrows_shifts:
            # Fetch or create today's shift for the same employee
            todays_shift, created = Shift.objects.get_or_create(
                employee=shift.employee,
                day='Today',
                defaults={
                    'shift_type': shift.shift_type,
                    'start_time': shift.start_time,
                    'end_time': shift.end_time,
                    'status': 'Scheduled',
                }
            )
            if not created:
                # If today's shift already exists, update it with tomorrow's shift details
                todays_shift.shift_type = shift.shift_type
                todays_shift.start_time = shift.start_time
                todays_shift.end_time = shift.end_time
                todays_shift.status = 'Scheduled'
                todays_shift.save()

        # Step 3: Clear tomorrow's shift slots
        tomorrows_shifts.delete()

    if request.method == 'POST':
        try:
            # Handling Today's Shift
            if 'employee_id_today' in request.POST:
                employee_id_today = request.POST.get('employee_id_today')
                shift_type_today = request.POST.get('shift_type_today')
                virtual_start_time_today = make_aware(datetime.combine(virtual_time.date(), datetime.strptime(
                    request.POST.get('start_time_today'), '%H:%M').time()))
                virtual_end_time_today = make_aware(datetime.combine(virtual_time.date(), datetime.strptime(
                    request.POST.get('end_time_today'), '%H:%M').time()))

                employee_today = Employee.objects.get(id=employee_id_today)

                # Check for overlapping shifts
                overlapping_shift = Shift.objects.filter(
                    employee=employee_today,
                    start_time__lt=virtual_end_time_today,
                    end_time__gt=virtual_start_time_today
                ).exists()

                if overlapping_shift:
                    messages.error(request, "The shift overlaps with an existing shift for this employee.")
                    return redirect('assign_shift_to_employee')

                Shift.objects.create(
                    employee=employee_today,
                    shift_type=shift_type_today,
                    day='Today',
                    start_time=virtual_start_time_today,
                    end_time=virtual_end_time_today,
                    status='Scheduled'
                )

            # Handling Tomorrow's Shift
            if 'employee_id_tomorrow' in request.POST:
                employee_id_tomorrow = request.POST.get('employee_id_tomorrow')
                shift_type_tomorrow = request.POST.get('shift_type_tomorrow')
                virtual_start_time_tomorrow = make_aware(datetime.combine(tomorrow, datetime.strptime(
                    request.POST.get('start_time_tomorrow'), '%H:%M').time()))
                virtual_end_time_tomorrow = make_aware(datetime.combine(tomorrow, datetime.strptime(
                    request.POST.get('end_time_tomorrow'), '%H:%M').time()))

                employee_tomorrow = Employee.objects.get(id=employee_id_tomorrow)

                # Check for overlapping shifts
                overlapping_shift = Shift.objects.filter(
                    employee=employee_tomorrow,
                    start_time__lt=virtual_end_time_tomorrow,
                    end_time__gt=virtual_start_time_tomorrow
                ).exists()

                if overlapping_shift:
                    messages.error(request, "The shift overlaps with an existing shift for this employee.")
                    return redirect('assign_shift_to_employee')

                Shift.objects.create(
                    employee=employee_tomorrow,
                    shift_type=shift_type_tomorrow,
                    day='Tomorrow',
                    start_time=virtual_start_time_tomorrow,
                    end_time=virtual_end_time_tomorrow,
                    status='Scheduled'
                )

            messages.success(request, "Shifts assigned successfully!")
            return redirect('assign_shift_to_employee')

        except Employee.DoesNotExist:
            messages.error(request, "The selected employee does not exist.")
        except ValueError as ve:
            messages.error(request, f"Invalid input: {ve}")
        except Exception as e:
            print(f"Error assigning shift: {e}")
            messages.error(request, "An unexpected error occurred. Please try again.")
            return redirect('assign_shift_to_employee')

    return render(request, 'admin_app/actions/assign_shift.html', {
        'employees_without_todays_shifts': employees_without_todays_shifts,
        'employees_without_tomorrows_shifts': employees_without_tomorrows_shifts,
        'tomorrow_day': tomorrow.strftime('%A, %B %d, %Y'),
    })


@login_required
def destination_list(request):
    destinations = Destination.objects.all()
    return render(request, 'admin_app/models/destination_list.html', {
        'destinations': destinations,
    })

@login_required
def booking_list(request):
    bookings = Booking.objects.all()
    return render(request, 'admin_app/models/booking_list.html', {
        'bookings': bookings,
    })

@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'admin_app/models/employee_list.html', {
        'employees': employees,
    })

@login_required
def customer_list(request):
    customers = Customer.objects.all()
    return render(request, 'admin_app/models/customer_list.html', {
        'customers': customers,
    })

@login_required
def task_list(request):
    tasks = Task.objects.all()
    return render(request, 'admin_app/models/task_list.html', {
        'tasks': tasks,
    })

@login_required
def promotion_list(request):
    promotions = Promotion.objects.all()
    return render(request, 'admin_app/models/promotion_list.html', {
        'promotions': promotions,
    })

@login_required
def inventory_list(request):
    inventory = Inventory.objects.all()
    return render(request, 'admin_app/models/inventory_list.html', {
        'inventory': inventory,
    })

@login_required
def feedback_list(request):
    feedbacks = Feedback.objects.all()
    return render(request, 'admin_app/models/feedback_list.html', {
        'feedbacks': feedbacks,
    })

@login_required
def activitylog_list(request):
    logs = ActivityLog.objects.all()
    return render(request, 'admin_app/models/activitylog_list.html', {
        'logs': logs,
    })

@login_required
def onboardservice_list(request):
    onboard_services = OnboardService.objects.all()
    return render(request, 'admin_app/models/onboardservices_list.html', {
        'onboard_services': onboard_services,
    })

@login_required
def shift_list(request):
    shifts = Shift.objects.all()
    return render(request, 'admin_app/models/shift_list.html', {
        'shifts': shifts,
    })

@login_required
def shiftswaprequest_list(request):
    swap_requests = ShiftSwapRequest.objects.all()
    return render(request, 'admin_app/models/shiftswaprequest_list.html', {
        'swap_requests': swap_requests,
    })

@login_required
def loyalty_program_list(request):
    loyalty_programs = LoyaltyProgram.objects.all()
    return render(request, 'admin_app/models/loyalty_program_list.html', {
        'loyalty_programs': loyalty_programs,
    })


@login_required
def special_request_list(request):
    special_requests = SpecialRequest.objects.all()
    return render(request, 'admin_app/models/special_request_list.html', {
        'special_requests': special_requests,
    })

@login_required
def approve_special_request(request, request_id):
    if request.method == "POST":
        special_request = get_object_or_404(SpecialRequest, id=request_id)
        
        # Update status to approved
        special_request.status = "Approved"
        special_request.save()
        
        # Send notification to the customer (In-app notification)
        Notification.objects.create(
            recipient=special_request.customer.user,
            title="Special Request Approved",
            message=f"Your special request for '{special_request.request_type}' has been approved. Our team will take care of it shortly.",
        )

        return JsonResponse({"message": "Special request approved and notification sent."})
    
    return JsonResponse({"error": "Invalid request"}, status=400)


@login_required
def customer_segment_list(request):
    customer_segments = CustomerSegment.objects.all()
    return render(request, 'admin_app/models/customer_segment_list.html', {
        'customer_segments': customer_segments,
    })


@login_required
def customer_booking_list(request):
    customer_bookings = CustomerBooking.objects.all()
    return render(request, 'admin_app/models/customer_booking_list.html', {
        'customer_bookings': customer_bookings,
    })


@login_required
def payment_list(request):
    payments = Payment.objects.all()
    return render(request, 'admin_app/models/payment_list.html', {
        'payments': payments,
    })


@login_required
def invoice_list(request):
    invoices = Invoice.objects.all()
    return render(request, 'admin_app/models/invoice_list.html', {
        'invoices': invoices,
    })


@login_required
def refund_request_list(request):
    if not request.user.is_staff:
        return redirect('admin_dashboard')

    refund_requests = RefundRequest.objects.select_related('booking__customer__user').all()

    return render(request, 'admin_app/models/refund_request_list.html', {
        'refund_requests': refund_requests,
    })

@login_required
def approve_refund(request, refund_id):
    if not request.user.is_staff:
        return redirect('admin_dashboard')

    refund_request = get_object_or_404(RefundRequest, id=refund_id)

    if refund_request.is_approved:
        messages.error(request, "This refund request is already approved.")
        return redirect('refundrequest_list')

    refund_request.is_approved = True
    refund_request.save()

    # Send notification to the customer
    customer_user = refund_request.booking.customer.user
    Notification.objects.create(
        recipient=customer_user,
        title="Refund Request Approved",
        message=f"Your refund request for Booking ID {refund_request.booking.id} has been approved. Final refunded amount: ${refund_request.final_price}.",
    )

    messages.success(request, "Refund request approved and customer notified.")
    return redirect('refundrequest_list')

@login_required
def itinerary_list(request):
    itineraries = Itinerary.objects.all()
    return render(request, 'admin_app/models/itinerary_list.html', {
        'itineraries': itineraries,
    })

@login_required
def passenger_list(request):
    passengers = Passenger.objects.all()
    return render(request, 'admin_app/models/passenger_list.html', {
        'passengers': passengers,
    })

@login_required
def job_application_list(request):
    job_applications = JobApplication.objects.all()
    return render(request, 'admin_app/models/job_application_list.html', {
        'job_applications': job_applications,
    })

@login_required
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'admin_app/models/department_list.html', {'departments': departments})

@login_required
def position_list(request):
    positions = Position.objects.select_related('department').all()
    return render(request, 'admin_app/models/position_list.html', {'positions': positions})
    
@login_required
def notification_list(request):
    if not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized access."}, status=403)

    # Fetch notifications for each user role
    admins = UserModule.objects.filter(role='admin')
    employees = UserModule.objects.filter(role='employee')
    customers = UserModule.objects.filter(role='customer')
    
    admin_notifications = Notification.objects.filter(recipient__in=admins).order_by('-created_at')
    employee_notifications = Notification.objects.filter(recipient__in=employees).order_by('-created_at')
    customer_notifications = Notification.objects.filter(recipient__in=customers).order_by('-created_at')
    all_notifications = Notification.objects.all().order_by('-created_at')
    
    # Count unread notifications for each role
    unread_count_admins = admin_notifications.filter(is_read=False).count()
    unread_count_employees = employee_notifications.filter(is_read=False).count()
    unread_count_customers = customer_notifications.filter(is_read=False).count()
    unread_count_all = all_notifications.filter(is_read=False).count()

    return render(request, 'admin_app/models/notification_list.html', {
        'admin_notifications': admin_notifications,
        'employee_notifications': employee_notifications,
        'customer_notifications': customer_notifications,
        'all_notifications': all_notifications,
        'unread_count_admins': unread_count_admins,
        'unread_count_employees': unread_count_employees,
        'unread_count_customers': unread_count_customers,
        'unread_count_all': unread_count_all,
    })

@csrf_exempt
@login_required
def mark_all_admin_notifications_read(request):
    if request.method == 'POST':
        try:
            notifications = Notification.objects.filter(recipient=request.user, is_read=False)
            notifications.update(is_read=True)  # Mark all as read

            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            return JsonResponse({'success': True, 'unread_count': unread_count})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

def all_models_view(request):
    app_name = 'core'
    models = apps.get_app_config(app_name).get_models()

    # Create a list of model names and their verbose names
    model_info = []
    for model in models:
        # Capitalize each word in the model name
        model_name = model.__name__.replace('_', ' ').title()  # Replace underscores with spaces and capitalize each word
        model_info.append({
            'name': model_name,
            'verbose_name': model._meta.verbose_name,
            'verbose_name_plural': model._meta.verbose_name_plural,
            'model_class_name': model.__name__,  # pass the model class name here
            'model_class': model
        })

    # Handle "clear all data" action if it's a POST request
    if request.method == 'POST' and 'clear_all_data' in request.POST:
        model_name = request.POST.get('model_name')
        try:
            model_class = apps.get_model('core', model_name)
            model_class.objects.all().delete()  # Clear all data for the model
            messages.success(request, f'All data for {model_class._meta.verbose_name_plural} has been cleared.')
        except LookupError:
            messages.error(request, 'Model not found.')
        return redirect('all_models_list')  
    
    return render(request, 'admin_app/models/all_models_list.html', {'models': model_info})


def clear_all_data(request, model_name):
    app_name = 'core'
    model = apps.get_model(app_label=app_name, model_name=model_name)
    
    if model:
        # Delete all records in the model
        model.objects.all().delete()
        return HttpResponse(f"All data for {model_name} has been cleared.", status=200)
    
    return HttpResponse("Model not found.", status=404)

# Utility functions
def generate_unique_employee_id():
    """
    Generates a unique employee ID in the format EMPXXX, where XXX is an ascending number.
    """
    while True:
        employee_id = get_random_string(8, allowed_chars='1234567890')  
        if not Employee.objects.filter(employee_id=employee_id).exists():
            return employee_id

def generate_secure_password(username):
    """Generates a secure password by combining the username with random symbols and numbers."""
    # Random symbols and numbers to append to the username
    symbols_and_numbers = string.punctuation + string.digits
    random_symbols = ''.join(random.choices(symbols_and_numbers, k=6))  # You can adjust the length of random symbols
    return username + random_symbols

def generate_username(first_name, last_name):
    """Generates a username in the format: firstname_lastname_randomNumber."""
    base_username = f"{first_name.lower()}_{last_name.lower()}"
    random_number = ''.join(random.choices(string.digits, k=3))
    username = f"{base_username}_{random_number}"

    # Ensure username is unique
    while UserModule.objects.filter(username=username).exists():
        random_number = ''.join(random.choices(string.digits, k=3))  # Generate a new random number
        username = f"{base_username}_{random_number}"

    return username

@login_required
def update_application_status(request, pk):
    application = get_object_or_404(JobApplication, pk=pk)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(JobApplication.STATUS_CHOICES):
            application.status = new_status
            application.save()

            if new_status.lower() == 'accepted':
                # Generate username
                username = generate_username(application.first_name, application.last_name)

                # Generate a secure password by using the generated username
                password = generate_secure_password(username)

                # Get or create user account
                user, created = UserModule.objects.get_or_create(
                    email=application.email,
                    defaults={'username': username, 'role': 'employee'}
                )

                if created:
                    user.set_password(password)  # Set hashed password
                    user.save()

                    # Generate a unique employee ID
                    employee_id = generate_unique_employee_id()

                    # Normalize the job role
                    normalized_job_role = normalize_job_role(application.job_role)

                    # Assign department and position based on normalized job role
                    department = None
                    position = None

                    for key, roles in JobApplication.DEPARTMENT_ROLES.items():
                        if any(normalized_job_role == normalize_job_role(role[0]) for role in roles):
                            department = Department.objects.get(name=f"{key.replace('_', ' ').title()} Department")
                            position = Position.objects.get(title=normalized_job_role, department=department)
                            break

                    if not department or not position:
                        raise ValueError(f"Cannot map job role '{application.job_role}' to a valid department or position.")

                    # Create a new Employee record
                    employee = Employee.objects.create(
                        user=user,
                        first_name=application.first_name,
                        last_name=application.last_name,
                        gender=application.gender,
                        phone=application.phone,
                        address=application.address,
                        city=application.city,
                        pincode=application.pincode,
                        nationality=application.nationality,
                        previous_experience=application.previous_experience,
                        job_role=normalized_job_role,
                        department=department,
                        position=position,
                        date_of_birth=application.date_of_birth,
                        availability_date=application.availability_date,
                        application_date=application.application_date,
                        employee_id=employee_id
                    )

                    # Assign a supervisor automatically
                    employee.assign_supervisor()
                    employee.save()

                # Send email to the applicant if the user account was created
                if created:
                    send_mail(
                        'Job Application Status - Accepted',
                        f'Congratulations, {application.first_name}!\n\n'
                        f'Your job application has been accepted. You can log in to the employee dashboard using the following credentials:\n'
                        f'Username: {username}\nPassword: {password}\n\n'
                        f'Please change your password upon first login.',
                        'projectbbsc3rd@gmail.com',
                        [application.email],
                        fail_silently=False,
                    )

            return redirect(reverse('jobapplication_list'))

    return render(request, 'admin_app/models/update_app_status.html', {
        'application': application,
        'status_choices': JobApplication.STATUS_CHOICES,
    })


@login_required
def review_change_requests(request):
    if not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized access."}, status=403)

    # Fetch all pending change requests
    pending_requests = ChangeRequest.objects.filter(is_approved__isnull=True).select_related('employee')
    all_requests = ChangeRequest.objects.filter(is_approved__isnull=False).select_related('employee')

    # Mark notifications related to change requests as read
    if request.method == 'POST':  # Check if the admin explicitly marks notifications as read
        notification_ids = request.POST.getlist('notification_ids')
        if notification_ids:
            Notification.objects.filter(pk__in=notification_ids, recipient=request.user).update(is_read=True)

    return render(request, 'admin_app/models/change_request_list.html', {
        'pending_requests': pending_requests,
        'all_requests': all_requests,
    })


@login_required
def process_change_request(request, pk):
    if not request.user.is_staff:
        return JsonResponse({"success": False, "message": "Unauthorized access."}, status=403)

    change_request = get_object_or_404(ChangeRequest, pk=pk)
    action = request.POST.get('action')  # `approve` or `reject`

    if action == 'approve':
        setattr(change_request.employee, change_request.field_name, change_request.new_value)
        change_request.employee.save()
        change_request.is_approved = True
        change_request.save()

        # Notify Employee
        Notification.objects.create(
            recipient=change_request.employee.user,
            title="Change Request Approved",
            message=f"Your change request for {change_request.field_name} has been approved.",
        )
    elif action == 'reject':
        change_request.is_approved = False
        change_request.save()

        # Notify Employee
        Notification.objects.create(
            recipient=change_request.employee.user,
            title="Change Request Rejected",
            message=f"Your change request for {change_request.field_name} has been rejected.",
        )
    else:
        return JsonResponse({"success": False, "message": "Invalid action."}, status=400)

    # Add the "Completed" status logic for the button field
    return JsonResponse({
        "success": True,
        "message": "Change request processed successfully.",
        "new_status": "Completed"  # Use this in the frontend to update the button
    })

# Login, logout, and other admin views
def custom_admin_login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        username = request.POST.get('username')  # Ensure this is unique

        # Check if the username already exists
        if UserModule.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return render(request, 'admin_app/login.html')

        user = authenticate(request, email=email, password=password)

        if user is not None and user.is_active and user.role == 'admin':
            login(request, user)
            return redirect('admin_dashboard')  # Redirect to admin dashboard
        else:
            messages.error(request, 'Invalid email or password for admin.')
            return render(request, 'admin_app/login.html')

    return render(request, 'admin_app/login.html')


def admin_logout(request):
    logout(request)
    return redirect('admin_login')

class EditModelView(View):
    def get(self, request, model_name, pk):
        model = apps.get_model('core', model_name.title())
        obj = get_object_or_404(model, pk=pk)
        form_class = modelform_factory(model, exclude=[])
        form = form_class(instance=obj)

        # Generate list URL based on model name
        list_url = reverse(f'{model_name}_list')

        context = {
            'form': form,
            'object': obj,
            'model_verbose_name': model._meta.verbose_name,
            'list_url': list_url,  # Pass list URL here
        }
        return render(request, 'admin_app/models/edit_model.html', context)

    def post(self, request, model_name, pk):
        model = apps.get_model('core', model_name)
        obj = get_object_or_404(model, pk=pk)
        form_class = modelform_factory(model, exclude=[])
        form = form_class(request.POST, instance=obj)

        if form.is_valid():
            form.save()
            messages.success(request, f"{model._meta.verbose_name} updated successfully.")
            return redirect(reverse(f'{model_name}_list'))

        list_url = reverse(f'{model_name}_list')
        
        context = {
            'form': form,
            'object': obj,
            'model_verbose_name': model._meta.verbose_name,
            'list_url': list_url,
        }
        return render(request, 'admin_app/models/edit_model.html', context)
    

class DeleteModelView(View):
    def get(self, request, model_name, pk):
        model = apps.get_model('core', model_name.title())
        obj = get_object_or_404(model, pk=pk)
        
        # Generate list URL for the cancel button in the confirm delete template
        list_url = reverse(f'{model_name}_list')

        context = {
            'object': obj,
            'model_verbose_name': model._meta.verbose_name,
            'list_url': list_url,
        }
        return render(request, 'admin_app/models/confirm_delete.html', context)

    def post(self, request, model_name, pk):
        model = apps.get_model('core', model_name)
        obj = get_object_or_404(model, pk=pk)
        
        # Capture the list URL before deleting
        list_url = reverse(f'{model_name}_list')
        
        # Delete the object and redirect
        obj.delete()
        messages.success(request, f"{model._meta.verbose_name} deleted successfully.")
        return redirect(list_url)
    
