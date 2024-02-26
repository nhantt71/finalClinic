

from django.contrib import admin
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Sum
from django.db.models.functions import ExtractMonth, ExtractQuarter, ExtractYear
from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.urls import path

from .models import *


class PrivateClinicAppAdminSite(admin.AdminSite):
    site_header = 'TRANG QUẢN TRỊ PHÒNG MẠCH TƯ'

    def get_urls(self):
        return [
            path('stats/', stats_view)
        ] + super().get_urls()


admin_site = PrivateClinicAppAdminSite(name='myapp')


@staff_member_required
def stats_view(request, period=None):

    period = request.GET.get('period')

    if period is None:
        period = 'month'

    # Lấy dữ liệu dựa vào chu kỳ được chọn (tháng, quý, năm)
    if period == 'month':
        appointments_data = Appointment.objects.annotate(month=ExtractMonth('date')).values('month').annotate(count=Sum('id'))
        revenue_data = Payment.objects.annotate(month=ExtractMonth('paid_at')).values('month').annotate(revenue=Sum('amount'))
    elif period == 'quarter':
        appointments_data = Appointment.objects.annotate(quarter=ExtractQuarter('date')).values('quarter').annotate(count=Sum('id'))
        revenue_data = Payment.objects.annotate(quarter=ExtractQuarter('paid_at')).values('quarter').annotate(revenue=Sum('amount'))
    elif period == 'year':
        appointments_data = Appointment.objects.annotate(year=ExtractYear('date')).values('year').annotate(count=Sum('id'))
        revenue_data = Payment.objects.annotate(year=ExtractYear('paid_at')).values('year').annotate(revenue=Sum('amount'))
    else:
        return HttpResponseBadRequest("Invalid period parameter")

    context = {
        'period': period,
        'appointments_data': appointments_data,
        'revenue_data': revenue_data,
    }

    return TemplateResponse(request, 'admin/stats.html', context)


class DutyScheduleAdmin(admin.ModelAdmin):
    ordering = ['pk']
    list_display = ['id', 'date', 'shift']
    search_fields = ['date']
    list_filter = ['shift']


class CustomAdmin(admin.ModelAdmin):
    list_display = ['fullname', 'birthdate', 'gender', 'phone_number']


class MedicineAdmin(admin.ModelAdmin):
    ordering = ['pk']
    list_display = ['id', 'name', 'amount', 'quantity']
    search_fields = ['name', 'amount', 'quantity']


class AppointmentAdmin(admin.ModelAdmin):
    ordering = ['pk']
    list_display = ['pk', 'date', 'time', 'patient', 'doctor']
    search_fields = ['date', 'time', 'patient', 'doctor']


class UserAdmin(admin.ModelAdmin):
    list_display = ['username', 'email', 'role']

    def save_model(self, request, obj, form, change):
        changed_fields = form.changed_data

        if changed_fields:
            if 'password' in changed_fields:
                changed_fields.remove('password')
                obj.set_password(obj.password)
                if not obj.pk:
                    obj.save()
                else:
                    obj.save(update_fields=changed_fields)
            else:
                obj.save(update_fields=changed_fields)
        else:
            pass


class PrescriptionMedicineInline(admin.TabularInline):  # Sử dụng TabularInline cho giao diện trực quan hơn
    model = PrescriptionMedicine
    extra = 1  # Số lượng form trống để điền


class PrescriptionAdmin(admin.ModelAdmin):
    inlines = [PrescriptionMedicineInline]


admin_site.register(Doctor, CustomAdmin)
admin_site.register(Nurse, CustomAdmin)
admin_site.register(Patient, CustomAdmin)
admin_site.register(User, UserAdmin)
admin_site.register(DutySchedule, DutyScheduleAdmin)
admin_site.register(Medicine, MedicineAdmin)
admin_site.register(Appointment, AppointmentAdmin)
admin_site.register(Prescription, PrescriptionAdmin)
admin_site.register(Payment)
