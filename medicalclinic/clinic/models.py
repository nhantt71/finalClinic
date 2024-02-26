from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Bác sĩ'),
        ('nurse', 'Y tá'),
        ('patient', 'Bệnh nhân'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='patient')


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    fullname = models.CharField(max_length=255)
    birthdate = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    phone_number = models.CharField(max_length=15, null=True, blank=True)
    avatar = models.ImageField(upload_to='avatar/')

    def __str__(self):
        return self.fullname

    class Meta:
        abstract = True


class Doctor(UserProfile):
    specialization = models.CharField(max_length=255, blank=True, null=True)


class Nurse(UserProfile):
    nursing_license = models.CharField(max_length=50, blank=True, null=True)


class Patient(UserProfile):
    medical_history = models.TextField(blank=True)


class DutySchedule(models.Model):
    SHIFT = [
        ('morning', 'Buổi sáng'),
        ('afternoon', 'Buổi chiều'),
        ('night', 'Buổi đêm'),
    ]

    date = models.DateField()
    shift = models.CharField(max_length=20, choices=SHIFT)
    doctors = models.ManyToManyField('Doctor', blank=True, related_name='dutyschedules_doc')
    nurses = models.ManyToManyField('Nurse', blank=True, related_name='dutyschedules_nur')


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    date = models.DateField()
    time = models.TimeField()
    doctor = models.ForeignKey(Doctor, on_delete=models.SET_NULL, null=True, blank=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f'{self.patient.fullname} - {self.date}'


class Medicine(models.Model):
    name = models.CharField(max_length=255)
    amount = models.DecimalField(decimal_places=3, max_digits=50)
    quantity = models.IntegerField(default=50)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Prescription(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE)
    symptoms = models.TextField()
    diagnosis = models.TextField()
    conclusion = models.TextField()
    medicines = models.ManyToManyField(Medicine, through='PrescriptionMedicine')

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.update_medicine_quantity()

    def update_medicine_quantity(self):
        for prescription_medicine in self.prescriptionmedicine_set.all():
            medicine = prescription_medicine.medicine
            quantity_taken = prescription_medicine.quantity
            medicine.quantity -= quantity_taken
            medicine.save()

    def calculate_total_amount(self):
        total_amount = 0

        # Lặp qua tất cả các PrescriptionMedicine liên quan đến Prescription này
        for prescription_medicine in self.prescriptionmedicine_set.all():
            medicine = prescription_medicine.medicine
            quantity = prescription_medicine.quantity

            # Tính tổng số tiền dựa trên giá tiền của từng thuốc và số lượng
            total_amount += medicine.amount * quantity

        num_medicines = self.prescriptionmedicine_set.count()

        if num_medicines > 2:
            total_amount += 500000
        else:
            total_amount += 200000

        return total_amount

    def __str__(self):
        return f'{self.appointment.patient.fullname} - {self.appointment.date}'


class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)


class Payment(models.Model):
    prescription = models.OneToOneField(Prescription, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=50, decimal_places=3)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.prescription.appointment.patient.fullname} - {self.amount} VND"
