from django.urls import path
from . import views

urlpatterns = [
    path('', views.start, name="start-employee" ),
    path('apply/', views.apply, name="apply"),
    path('application-success/', views.application_success, name='application-success'),
    path('login/', views.employee_login, name="employee-login"),
    path('dashboard/', views.dashboard, name="employee-dashboard"),
    path('profile/', views.profile, name="employee-profile"),
    path('update-details/', views.update_details, name='update_employee_details'),
    path('change-password/', views.change_employee_password, name='change_employee_password'),
    path('update-profile-picture/', views.update_employee_profile_picture, name='update_employee_profile_picture'),
    path('submit-change-request/', views.submit_change_request, name='submit_change_request'),
    path('attendance/', views.attendance, name="attendance"),
    path('attendance/mark/', views.mark_attendance, name='mark_attendance'),
    path('training/', views.training, name="training"),
    path('payroll/', views.payroll, name="payroll"),
    path('task/', views.task, name="task"),
    path('notifications/', views.notifications, name='employee-notifications'),
    path('mark-all-notifications-read/', views.mark_all_notifications_read, name='mark-all-notifications-read'),
    path('request-shift-swap/', views.request_shift_swap, name='request_shift_swap'),
    path('get-available-employees/', views.get_available_employees, name='get_available_employees'),
    path('logout/', views.employee_logout, name="employee-logout" ),
]