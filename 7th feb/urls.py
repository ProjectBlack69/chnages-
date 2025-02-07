from django.urls import path
from admin_app.views import EditModelView, DeleteModelView
from .views import custom_admin_login, admin_dashboard, admin_logout
from . import views

urlpatterns = [
    # Main URLs
    path('', custom_admin_login, name='admin_login'),
    path('dashboard/', admin_dashboard, name='admin_dashboard'),
    path('logout/', admin_logout, name='admin_logout'),

    # Model list views
    path('user_modules/', views.usermodule_list, name='usermodule_list'),
    path('activity_logs/', views.activitylog_list, name='activitylog_list'),
    path('employees/', views.employee_list, name='employee_list'),
    path('customers/', views.customer_list, name='customer_list'),
    path('loyalty_programs/', views.loyalty_program_list, name='loyaltyprogram_list'),
    path('special_requests/', views.special_request_list, name='specialrequest_list'),
    path('special-requests/approve/<int:request_id>/', views.approve_special_request, name='approve_special_request'),
    path('cruises/', views.cruise_list, name='cruise_list'),
    path('destinations/', views.destination_list, name='destination_list'),
    path('onboard_services/', views.onboardservice_list, name='onboardservice_list'),
    path('bookings/', views.booking_list, name='booking_list'),
    path('customer_bookings/', views.customer_booking_list, name='customerbooking_list'),
    path('payments/', views.payment_list, name='payment_list'),
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('refund_requests/', views.refund_request_list, name='refundrequest_list'),
    path('refund-requests/approve/<int:refund_id>/', views.approve_refund, name='approve_refund'),
    path('itineraries/', views.itinerary_list, name='itinerary_list'),
    path('tasks/', views.task_list, name='task_list'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('shift_swap_requests/', views.shiftswaprequest_list, name='shiftswaprequest_list'),
    path('promotions/', views.promotion_list, name='promotion_list'),
    path('customer_segments/', views.customer_segment_list, name='customersegment_list'),
    path('inventory/', views.inventory_list, name='inventory_list'),
    path('feedback/', views.feedback_list, name='feedback_list'),
    path('passengers/', views.passenger_list, name='passenger_list'),
    path('jobapplications/', views.job_application_list, name='jobapplication_list'),
    path('job-applications/<int:pk>/update-status/', views.update_application_status, name='update_application_status'),
    path('departments/', views.department_list, name='department_list'),
    path('positions/', views.position_list, name='position_list'),
    path('shifts/', views.shift_list, name='shift_list'),
    path('assign-shift/', views.assign_shift_to_employee, name='assign_shift_to_employee'),
    path('review-change-requests/', views.review_change_requests, name='changerequest_list'),
    path('process-change-request/<int:pk>/', views.process_change_request, name='process_change_request'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('mark-all-notifications-read/', views.mark_all_admin_notifications_read, name='admin-mark-notifications-read'),
    path('all-models/', views.all_models_view, name='all_models_list'),
    path('clear-all-data/<str:model_name>/', views.clear_all_data, name='clear_all_data'),
    path('virtual-clock/', views.virtual_clock_list, name='virtual_clock_list'),
    path('virtual-clock/create/', views.create_virtual_clock, name='create_virtual_clock'),
    path('virtual-clock/edit/<int:pk>/', views.edit_virtual_clock, name='edit_virtual_clock'),
    path('virtual-clock/delete/<int:pk>/', views.delete_virtual_clock, name='delete_virtual_clock'),
    path('start_virtual_clock/<int:clock_id>/', views.start_virtual_clock, name='start_virtual_clock'),
    path('pause_virtual_clock/<int:clock_id>/', views.pause_virtual_clock, name='pause_virtual_clock'),
    path('reset-virtual-clock/<int:clock_id>/', views.reset_virtual_clock, name='reset_virtual_clock'),
    path('get-updated-virtual-time/<int:clock_id>/', views.get_updated_virtual_time, name='get_updated_virtual_time'),

    # Dynamic Edit and Delete
    path('<str:model_name>/edit/<int:pk>/', EditModelView.as_view(), name='edit_model'),
    path('<str:model_name>/delete/<int:pk>/', DeleteModelView.as_view(), name='delete_model'),

    
]
