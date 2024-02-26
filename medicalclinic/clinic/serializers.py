from rest_framework import serializers
from .models import User, Patient, Appointment, Medicine, Prescription, Payment


class PatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    patient = PatientSerializer()

    class Meta:
        model = User
        fields = ['username', 'password', 'email', 'patient']

    def create(self, validated_data):
        patient_data = validated_data.pop('patient')

        user = User.objects.create(**validated_data)
        Patient.objects.create(user=user, **patient_data)

        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class CustomLoginSerializer(serializers.Serializer):
    user = UserLoginSerializer()
    role = serializers.CharField(source='user.userprofile.role', read_only=True)


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = '__all__'


class CancelAppointmentSerializer(serializers.Serializer):
    appointment_id = serializers.IntegerField()


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'


class PrescriptionSerializer(serializers.ModelSerializer):
    medicines = MedicineSerializer(many=True)

    class Meta:
        model = Prescription
        fields = '__all__'


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'