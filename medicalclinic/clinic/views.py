import random
from django.core.mail import send_mail
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView

from .models import Patient, Appointment, Doctor, Prescription, Payment, Medicine
from .perms import IsNurse, IsPatient, IsDoctor
from .serializers import UserRegistrationSerializer, CustomLoginSerializer, AppointmentSerializer, PatientSerializer, \
    CancelAppointmentSerializer, PrescriptionSerializer, PaymentSerializer, MedicineSerializer


class UserRegistrationView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = CustomLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class Logout(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Thu hồi (revoke) access token
        request.auth.revoke()
        return Response({'message': 'Logout successful'})


class RegisterAppointment(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def post(self, request):
        date = request.data.get('date')
        time = request.data.get('time')
        user_id = request.user.pk

        if Appointment.objects.filter(date=date).count() >= 100:
            return Response({'message': 'Phòng khám đã đầy, vui lòng chọn ngày khám khác.'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            patient = Patient.objects.get(user_id=user_id)
        except Patient.DoesNotExist:
            return Response({'message': 'Không tìm thấy thông tin bệnh nhân.'}, status=status.HTTP_404_NOT_FOUND)

        appointment_data = {'patient': patient.pk, 'date': date, 'time': time}
        appointment_serializer = AppointmentSerializer(data=appointment_data)

        try:
            if appointment_serializer.is_valid():
                appointment_serializer.save()
                return Response({'message': 'Lịch khám đã được đăng ký và xác nhận.'}, status=status.HTTP_201_CREATED)
            else:
                return Response({'message': 'Dữ liệu không hợp lệ.', 'errors': appointment_serializer.errors},
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CancelAppointment(APIView):
    permission_classes = [IsAuthenticated, IsPatient]

    def delete(self, request, appointment_id):
        try:
            user_id = request.user.pk
            patient_id = Patient.objects.get(user_id=user_id).pk

            appointment = Appointment.objects.get(pk=appointment_id, patient=patient_id)
            appointment.delete()
            return Response({'message': 'Lịch đã bị hủy.'}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({'message': 'Không tìm thấy lịch khám hoặc bạn không có quyền hủy lịch này.'},
                            status=status.HTTP_404_NOT_FOUND)


class ConfirmAppointment(APIView):
    permission_classes = [IsAuthenticated, IsNurse]

    def put(self, request, appointment_id):
        try:
            appointment = Appointment.objects.get(pk=appointment_id, is_confirmed=False)
            appointment.is_confirmed = True

            doctors = Doctor.objects.all()

            if not doctors:
                return Response({'message': 'Không có bác sĩ khả dụng.'}, status=status.HTTP_400_BAD_REQUEST)

            doctor = random.choice(doctors)

            appointment.doctor = doctor
            appointment.save()

            patient_email = appointment.patient.user.email
            date = appointment.date
            time = appointment.time
            message = f'Lịch khám của bạn đã được xác nhận. Vào lúc {time} ngày {date} chúng tôi rất mong đợi sự xuất hiện của bạn.'

            send_mail(
                'Xác nhận lịch khám',
                message,
                '2151013063nhan@ou.edu.vn',
                [patient_email],
                fail_silently=False,
            )

            return Response({'message': 'Lịch khám đã được xác nhận.'}, status=status.HTTP_200_OK)
        except Appointment.DoesNotExist:
            return Response({'message': 'Không tìm thấy lịch khám hoặc lịch đã được xác nhận.'},
                            status=status.HTTP_404_NOT_FOUND)


class ViewMedicalHistory(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request, patient_id):
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if start_date and end_date:
            prescriptions = Prescription.objects.filter(
                appointment__patient_id=patient_id,
                appointment__date__range=[start_date, end_date]
            )
        else:
            prescriptions = Prescription.objects.filter(appointment__patient_id=patient_id)

        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)


class PaymentAPI(APIView):
    permission_classes = [IsAuthenticated, IsNurse]

    def post(self, request, prescription_id):
        try:
            prescription = Prescription.objects.get(pk=prescription_id)
        except Prescription.DoesNotExist:
            return Response({'message': 'Không tìm thấy đơn thuốc.'}, status=status.HTTP_404_NOT_FOUND)

        # Tính toán tổng số tiền
        total_amount = prescription.calculate_total_amount()

        # Tạo Payment
        payment_data = {'prescription': prescription.pk, 'amount': total_amount}
        payment_serializer = PaymentSerializer(data=payment_data)

        if payment_serializer.is_valid():
            payment_serializer.save()
            return Response({'message': 'Thanh toán thành công.'}, status=status.HTTP_201_CREATED)
        else:
            return Response({'message': 'Đã xảy ra lỗi khi thanh toán.', 'error': payment_serializer.errors}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PrescriptionAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def post(self, request):
        try:
            appointment_id = request.data.get('appointment_id')
            symptoms = request.data.get('symptoms')
            diagnosis = request.data.get('diagnosis')
            conclusion = request.data.get('conclusion')
            medicines_data = request.data.get('medicines', [])

            prescription = Prescription.objects.create(
                appointment_id=appointment_id,  # Thêm trường appointment
                symptoms=symptoms,
                diagnosis=diagnosis,
                conclusion=conclusion
            )

            for medicine_data in medicines_data:
                medicine_name = medicine_data.get('name')
                medicine = Medicine.objects.get(name=medicine_name)
                quantity = medicine_data.get('quantity', 1)

                if medicine.quantity >= quantity:
                    prescription.medicines.add(medicine, through_defaults={'quantity': quantity})
                    medicine.quantity -= quantity
                    medicine.save()
                else:
                    # Nếu số lượng không đủ, quay lại response lỗi
                    prescription.delete()
                    return Response({'message': f'Số lượng thuốc {medicine_name} không đủ.'},
                                    status=status.HTTP_400_BAD_REQUEST)

            serializer = PrescriptionSerializer(prescription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({'message': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class MedicineSearchAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        # Lấy dữ liệu từ query params (vd: /api/medicine/search/?keyword=paracetamol)
        keyword = request.query_params.get('keyword', '')

        # Xử lý logic tìm kiếm thuốc dựa trên từ khóa
        medicines = Medicine.objects.filter(name__icontains=keyword)
        serializer = MedicineSerializer(medicines, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)


class GetMedicineAPIView(APIView):
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        # Lấy ID của thuốc từ query params (vd: /api/medicine/get_medicine/?id=1)
        medicine_id = request.query_params.get('id', None)

        if not medicine_id:
            return Response({'message': 'Thiếu ID thuốc.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Xử lý logic lấy thông tin thuốc dựa trên ID
            medicine = Medicine.objects.get(id=medicine_id)
            serializer = MedicineSerializer(medicine)

            return Response(serializer.data, status=status.HTTP_200_OK)
        except Medicine.DoesNotExist:
            return Response({'message': 'Không tìm thấy thông tin thuốc.'}, status=status.HTTP_404_NOT_FOUND)
