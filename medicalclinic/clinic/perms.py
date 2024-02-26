from rest_framework import permissions


class IsNurse(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'nurse'


class IsDoctor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'doctor'


class IsPatient(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.role == 'patient'
