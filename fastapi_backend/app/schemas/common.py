from enum import StrEnum


class UserRole(StrEnum):
    SECURITY_OFFICER = "security_officer"
    DOCTOR = "doctor"
    CLINICIAN = "clinician"
    ADMIN = "admin"
    RESEARCHER = "researcher"
