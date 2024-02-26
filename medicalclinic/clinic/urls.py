from django.urls import path


from .views import *


urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user_register'),
    path('logout/', Logout.as_view(), name='logout'),
    path('register-appointment/', RegisterAppointment.as_view(), name='register_appointment'),
    path('cancel-appointment/<int:appointment_id>/', CancelAppointment.as_view(), name='cancel_appointment'),
    path('confirm-appointment/<int:appointment_id>/', ConfirmAppointment.as_view(), name='confirm_appointment'),
    path('view-medical-history/<int:patient_id>/', ViewMedicalHistory.as_view(), name='view_medical_history'),
    path('payment/<int:prescription_id>/', PaymentAPI.as_view(), name='payment-api'),
    path('prescriptions/', PrescriptionAPIView.as_view(), name='prescription_api'),
    path('medicine/search/', MedicineSearchAPIView.as_view(), name='medicine_search'),
    path('medicine/get_medicine/', GetMedicineAPIView.as_view(), name='get_medicine'),
]
