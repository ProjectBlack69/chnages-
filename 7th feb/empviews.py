from django.http import JsonResponse
from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from core.models import Employee, Position, Department, Notification, ChangeRequest, UserModule, Shift, ShiftSwapRequest, AssignmentShift, VirtualClock
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
import json
from django.utils import timezone
from django.utils.timezone import datetime, timedelta
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.forms import PasswordChangeForm
from .forms import JobApplicationForm, EmployeeProfileUpdateForm

def start(request):
    return render(request, 'employee/start.html')

def apply(request):
    if request.method == 'POST':
        form = JobApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()  # Save the application to the database

            full_name = f"{application.first_name} {application.last_name}"
            
            # Notify admins about the new job application
            admin_users = UserModule.objects.filter(is_staff=True)  # Filter for admin users
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    title="New Job Application Submitted",
                    message=f"A new job application has been submitted by {full_name}.",
                )
            
            return JsonResponse({
                'success': True,
                'redirect_url': '/employee/application-success/'  # Specify the success page URL
            })
        else:
            return JsonResponse({
                'success': False,
                'errors': form.errors  # Return validation errors
            })
    else:
        form = JobApplicationForm()
    return render(request, 'employee/apply.html', {'form': form})

def application_success(request):
    return render(request, 'employee/application_success.html')

@require_http_methods(["GET", "POST"])
def employee_login(request):
    if request.method == "GET":
        # Render the login page for GET requests
        return render(request, "employee/login.html")

    if request.method == "POST":
        try:
            data = json.loads(request.body)  # Parse JSON data from the request body
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON.'}, status=400)

        email = data.get('email')
        password = data.get('password')

        if email and password:
            # Authenticate the user
            user = authenticate(request, username=email, password=password)

            if user is not None and user.is_active:
                # Log in the user
                login(request, user)
                return JsonResponse({'status': 'success', 'message': "Employee login successful!"})
            else:
                return JsonResponse({'status': 'error', 'message': "Invalid credentials or inactive account."})

        return JsonResponse({'status': 'error', 'message': "Email and password are required."}, status=400)
    
@login_required
def dashboard(request):
    # Fetch the virtual clock from the core app
    virtual_clock = VirtualClock.objects.first() 
    if virtual_clock:
        virtual_time = virtual_clock.get_virtual_time()
        is_tomorrow = virtual_clock.current_day == 'Tomorrow'
    else:
        virtual_time = datetime.now()
        is_tomorrow = False
    
    # Fetch the logged-in employee
    employee = Employee.objects.filter(user=request.user).first()

    if employee:
        # Count the number of shifts where attendance_status is 'Present'
        attendance_count = AssignmentShift.objects.filter(employee=employee, attendance_status='Present').count()
    else:
        attendance_count = 0

    # Fetch all notifications
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')
    unread_count = notifications.filter(is_read=False).count()
    recent_notifications = notifications[:5]

    # Get the employee and their supervisor
    employee = request.user.employee
    supervisor = employee.supervisor

    # Determine the date to filter shifts
    shift_date = virtual_time.date()

    # Fetch the current shift based on the virtual clock and current day
    current_shift = Shift.objects.filter(
        employee=employee,
        status='Scheduled',
        start_time__lte=virtual_time,
        end_time__gte=virtual_time
    ).select_related('employee').first()

    # If no current shift and virtual clock is set to 'Tomorrow', fetch tomorrow's shift
    if not current_shift and is_tomorrow:
        tomorrow_date = virtual_time.date() + timedelta(days=1)
        current_shift = Shift.objects.filter(
            employee=employee,
            status='Scheduled',
            start_time__date=tomorrow_date
        ).select_related('employee').first()

    # Ensure the current shift logic resets when virtual clock changes back to 'Today'
    if not is_tomorrow and current_shift and current_shift.start_time and current_shift.start_time != virtual_time.time():
        # Fix the comparison by combining the date and time for current_shift
        current_shift_datetime = datetime.combine(shift_date, current_shift.start_time)
        if current_shift_datetime.date() != virtual_time.date():
            current_shift = Shift.objects.filter(
                employee=employee,
                status='Scheduled',
                start_time__lte=virtual_time,
                end_time__gte=virtual_time
            ).select_related('employee').first()

    # Combine start and end times for current shift
    if current_shift:
        start_datetime = datetime.combine(shift_date, current_shift.start_time)
        end_datetime = datetime.combine(shift_date, current_shift.end_time)

        # Convert to ISO 8601 format
        start_time = start_datetime.isoformat()
        end_time = end_datetime.isoformat()
    else:
        start_time = None
        end_time = None

    # Fetch the upcoming shift
    upcoming_shift = Shift.objects.filter(
        employee=employee,
        status='Scheduled',
        start_time__gt=virtual_time
    ).order_by('start_time').first()

    # Shift swap candidates
    swap_candidates = Shift.objects.filter(
        status='Scheduled'
    ).exclude(employee=employee).select_related('employee')[:10]

    # Recent activity data
    activity_data = AssignmentShift.objects.filter(
        employee=employee
    ).order_by('-date')[:5]

    return render(request, 'employee/dashboard.html', {
        'employee': employee,
        'attendance_count': attendance_count,
        'recent_notifications': recent_notifications,
        'unread_count': unread_count,
        'current_shift': current_shift,
        'upcoming_shift': upcoming_shift,
        'supervisor': supervisor,
        'swap_candidates': swap_candidates,
        'activity_data': activity_data,
        'start_time': start_time,
        'end_time': end_time,
        'virtual_time': virtual_time.isoformat(),
    })

def profile(request):
    employee = get_object_or_404(Employee, user=request.user)
    return render(request, 'employee/profile.html', {'employee': employee})

@login_required
def notifications(request):
    user = request.user
    all_notifications = Notification.objects.filter(recipient=user).order_by('-created_at')
    unread_notifications = all_notifications.filter(is_read=False)
    unread_count = unread_notifications.count()

    return render(request, 'employee/notification.html', {
        'notifications': all_notifications,  # Show all notifications
        'unread_notifications': unread_notifications,  # For dropdown
        'unread_count': unread_count,
    })

@csrf_exempt
@login_required
def mark_all_notifications_read(request):
    if request.method == 'POST':
        try:
            # Mark all unread notifications as read
            notifications = Notification.objects.filter(recipient=request.user, is_read=False)
            notifications.update(is_read=True)

            # Recalculate unread count
            unread_count = Notification.objects.filter(recipient=request.user, is_read=False).count()
            return JsonResponse({'success': True, 'unread_count': unread_count})
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)

    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)


@login_required
def request_shift_swap(request):
    if request.method == 'POST':
        shift_date = request.POST.get('shift-date')
        swap_reason = request.POST.get('swap-reason')
        employee_to_id = request.POST.get('employee-dropdown')  # We expect the employee's ID here

        # Backend validations
        if not shift_date or not swap_reason or not employee_to_id:
            return JsonResponse({'success': False, 'error': 'All fields are required.'})

        try:
            # Ensure the shift and employee are valid
            shift = Shift.objects.get(day=shift_date)  # Ensure 'day' field is correctly used
            employee_to = Employee.objects.get(id=employee_to_id)
        except (Shift.DoesNotExist, Employee.DoesNotExist):
            return JsonResponse({'success': False, 'error': 'Invalid shift or employee selected.'})

        # Further business logic checks...
        if shift.employee == employee_to:
            return JsonResponse({'success': False, 'error': 'You cannot swap a shift with yourself.'})

        # Create the swap request
        ShiftSwapRequest.objects.create(
            employee_from=request.user.employee,
            employee_to=employee_to,
            shift_from=shift,
            swap_date=shift_date,
            reason=swap_reason
        )

        return JsonResponse({'success': True, 'message': 'Swap request submitted successfully!'})

    return JsonResponse({'success': False, 'error': 'Invalid request method.'})

def get_available_employees(request):
    date = request.GET.get('date')
    if not date:
        return JsonResponse({'success': False, 'error': 'Date not provided.'})

    # Adjust the query as needed to match your models and logic
    shifts = Shift.objects.filter(day=date, status='Scheduled')
    employees = Employee.objects.filter(shift__in=shifts).distinct()

    employee_data = [{'id': emp.id, 'name': f'{emp.first_name} {emp.last_name}'} for emp in employees]

    return JsonResponse({'success': True, 'employees': employee_data})

@csrf_exempt
@login_required
def update_details(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        employee = request.user.employee

        try:
            # Initialize a list to store change requests
            changes = []

            # Check and record changes for each field
            if 'full_name' in data:
                full_name = data['full_name']
                first_name, last_name = full_name.split(' ')[0], full_name.split(' ')[1]
                if employee.first_name != first_name:
                    changes.append(ChangeRequest(
                        employee=employee,
                        field_name='first_name',
                        old_value=employee.first_name,
                        new_value=first_name
                    ))
                if employee.last_name != last_name:
                    changes.append(ChangeRequest(
                        employee=employee,
                        field_name='last_name',
                        old_value=employee.last_name,
                        new_value=last_name
                    ))

            if 'job_title' in data:
                job_title = data['job_title']
                if employee.job_role != job_title:
                    changes.append(ChangeRequest(
                        employee=employee,
                        field_name='job_role',
                        old_value=employee.job_role,
                        new_value=job_title
                    ))

            if 'department' in data:
                department_name = data['department']
                if employee.department and employee.department.name != department_name:
                    changes.append(ChangeRequest(
                        employee=employee,
                        field_name='department',
                        old_value=employee.department.name if employee.department else None,
                        new_value=department_name
                    ))

            # Add other fields as necessary
            for field in ['phone', 'skills', 'address', 'date_of_birth', 'linkedin_url']:
                if field in data:
                    new_value = data[field]
                    old_value = getattr(employee, field, '')
                    if str(old_value) != str(new_value):
                        changes.append(ChangeRequest(
                            employee=employee,
                            field_name=field,
                            old_value=old_value,
                            new_value=new_value
                        ))

            # Save all changes
            ChangeRequest.objects.bulk_create(changes)

            # Notify admins (optional: add Notification model logic here)
            admin_users = UserModule.objects.filter(is_staff=True)
            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    title="Pending Employee Change Request",
                    message=f"{employee.first_name} {employee.last_name} submitted changes for approval."
                )

            return JsonResponse({'success': True, 'message': 'Change requests submitted for admin approval.'})

        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)})

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
@csrf_exempt
def change_employee_password(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user = request.user

        if user.role != 'employee':
            return JsonResponse({'success': False, 'message': 'User is not an employee'})

        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')

        if not user.check_password(current_password):
            return JsonResponse({'success': False, 'message': 'Incorrect current password'})
        if new_password != confirm_password:
            return JsonResponse({'success': False, 'message': 'Passwords do not match'})

        # Update the password
        user.set_password(new_password)
        user.save()

        # Re-authenticate and log the user back in
        user = authenticate(request, email=user.email, password=new_password)
        if user is not None:
            login(request, user)

        return JsonResponse({'success': True, 'message': 'Password updated successfully'})

    return JsonResponse({'success': False, 'message': 'Invalid request method'})

@login_required
def submit_change_request(request):
    if request.method == "POST":
        employee = request.user.employee  # Assuming `Employee` is linked to `User`
        changes = request.POST.dict()  # Collect changes from the form
        
        for field, new_value in changes.items():
            old_value = getattr(employee, field, None)
            if str(old_value) != new_value:  # Create requests only for actual changes
                ChangeRequest.objects.create(
                    employee=employee,
                    field_name=field,
                    old_value=old_value,
                    new_value=new_value,
                )
        
        # Notify Admins
        admin_users = UserModule.objects.filter(is_staff=True)  # Assuming admins have `is_staff` as `True`
        for admin in admin_users:
            Notification.objects.create(
                recipient=admin,
                title="Employee Change Request",
                message=f"{employee.first_name} {employee.last_name} requested changes to their profile.",
            )
        
        return JsonResponse({"success": True, "message": "Change request submitted successfully."})
    
    return JsonResponse({"success": False, "message": "Invalid request method."}, status=400)

def employee_logout(request):
    if request and hasattr(request, 'user') and request.user.is_authenticated:
        logout(request)
    return redirect('start-employee')

@login_required
def attendance(request):
    # Fetch the virtual clock
    virtual_clock = VirtualClock.objects.first()
    if not virtual_clock:
        return render(request, 'employee/attendance.html', {'error': 'Virtual Clock not configured.'})

    # Get virtual day and time
    virtual_time = virtual_clock.get_virtual_time()
    virtual_date = virtual_time.date()

    # Get logged-in employee
    employee = Employee.objects.get(user=request.user)

    # Fetch today's shift based on virtual day
    shift = Shift.objects.filter(employee=employee, status='Scheduled', day=virtual_clock.current_day).first()

    # Fetch attendance history for the virtual date
    attendance_history = AssignmentShift.objects.filter(employee=employee).order_by('-date')

    context = {
        'employee': employee,
        'shift': shift,
        'attendance_history': attendance_history,
        'virtual_date': virtual_date,
        'virtual_day': virtual_clock.current_day,
    }
    return render(request, 'employee/attendance.html', context)


@login_required
def mark_attendance(request):
    if request.method == 'POST':
        # Fetch the virtual clock
        virtual_clock = VirtualClock.objects.first()
        if not virtual_clock:
            return redirect('attendance')

        virtual_time = virtual_clock.get_virtual_time()
        virtual_date = virtual_time.date()

        shift_id = request.POST.get('shift_id')
        status = request.POST.get('status')

        # Fetch the shift
        shift = Shift.objects.get(id=shift_id)
        if shift.day != virtual_clock.current_day:
            return redirect('attendance')  # Prevent marking attendance for a different day

        # Create or update the attendance record
        attendance, created = AssignmentShift.objects.get_or_create(
            shift=shift,
            employee=shift.employee,
            date=virtual_date,
        )
        attendance.mark_attendance(status)

        return redirect('attendance')

    return redirect('attendance')


def payroll(request):
    return render(request, 'employee/payroll.html')

def training(request):
    return render(request, 'employee/training.html')

def task(request):
    return render(request, 'employee/task.html')

@csrf_exempt
@login_required
def update_employee_profile_picture(request):
    if request.method == 'POST' and request.FILES.get('profile_picture'):
        try:
            employee = Employee.objects.get(user=request.user)  # Fetch employee instance
            profile_picture = request.FILES['profile_picture']

            # Save the new profile picture
            employee.profile_picture = profile_picture
            employee.save()

            return JsonResponse({'success': True, 'url': employee.profile_picture.url})
        except Employee.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Employee profile not found'}, status=404)
    return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)

