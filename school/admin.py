from django.contrib import admin

from .models import (
    Student,
    SchoolClass,
    Teacher,
    Parent,
    Timetable,
    Attendance,
    Grade,
    Homework,
    HomeworkSubmission,
    FeeRecord,
)


# Attendance Inline
class AttendanceInline(admin.TabularInline): 
    model = Attendance
    extra = 1


# Grade Inline
class GradeInline(admin.TabularInline):
    model = Grade
    extra = 1


# Student Admin
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = (
        "first_name",
        "last_name",
        "roll_number",
        "email",
        "school_class",
    )

    search_fields = (
        "first_name",
        "last_name",
        "roll_number",
    )

    inlines = [
        AttendanceInline,
        GradeInline,
    ]


# Register remaining models
admin.site.register(SchoolClass)
admin.site.register(Teacher)
admin.site.register(Parent)
admin.site.register(Timetable)
admin.site.register(Attendance)
admin.site.register(Grade)
admin.site.register(Homework)
admin.site.register(HomeworkSubmission)
admin.site.register(FeeRecord)