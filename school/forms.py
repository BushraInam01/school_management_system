from django import forms
from django.forms import modelformset_factory

from .models import (
    Attendance,
    Student,
    Timetable,
    Grade,
    Homework,
    HomeworkSubmission,
    FeeRecord,
)


# Attendance Form
class AttendanceForm(forms.ModelForm):

    class Meta:
        model = Attendance
        fields = ["student", "date", "status"]

        widgets = {
            "date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Teacher can select students only from assigned classes
        if user is not None and not user.is_superuser:
            teacher = getattr(user, "teacher", None)

            if teacher:
                class_ids = Timetable.objects.filter(
                    teacher=teacher
                ).values_list(
                    "school_class_id",
                    flat=True
                ).distinct()

                self.fields["student"].queryset = Student.objects.filter(
                    school_class_id__in=class_ids
                )
            else:
                self.fields["student"].queryset = Student.objects.none()


# Grade Form
class GradeForm(forms.ModelForm):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None and not user.is_superuser:
            teacher = getattr(user, "teacher", None)

            if teacher:
                class_ids = Timetable.objects.filter(
                    teacher=teacher
                ).values_list(
                    "school_class_id",
                    flat=True
                ).distinct()

                self.fields["student"].queryset = Student.objects.filter(
                    school_class_id__in=class_ids
                )
            else:
                self.fields["student"].queryset = Student.objects.none()

    def clean(self):
        cleaned_data = super().clean()

        total_marks = cleaned_data.get("total_marks")
        obtained_marks = cleaned_data.get("obtained_marks")

        if total_marks is not None and total_marks <= 0:
            self.add_error(
                "total_marks",
                "Total marks must be greater than zero."
            )

        if (
            total_marks is not None
            and obtained_marks is not None
            and obtained_marks > total_marks
        ):
            self.add_error(
                "obtained_marks",
                "Obtained marks cannot exceed total marks."
            )

        return cleaned_data

    class Meta:
        model = Grade
        fields = [
            "student",
            "subject",
            "exam_name",
            "total_marks",
            "obtained_marks",
        ]


# Homework Form
class HomeworkForm(forms.ModelForm):

    class Meta:
        model = Homework
        fields = [
            "school_class",
            "title",
            "description",
            "due_date",
            "total_marks",
        ]

        widgets = {
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is not None and not user.is_superuser:
            teacher = getattr(user, "teacher", None)

            if teacher:
                class_ids = Timetable.objects.filter(
                    teacher=teacher
                ).values_list(
                    "school_class_id",
                    flat=True
                ).distinct()

                self.fields["school_class"].queryset = (
                    self.fields["school_class"].queryset.filter(
                        id__in=class_ids
                    )
                )
            else:
                self.fields["school_class"].queryset = (
                    self.fields["school_class"].queryset.none()
                )


# Homework Submission Form
class HomeworkSubmissionForm(forms.ModelForm):

    class Meta:
        model = HomeworkSubmission
        fields = ["answer"]

        widgets = {
            "answer": forms.Textarea(
                attrs={
                    "rows": 5,
                    "placeholder": "Write your homework answer here..."
                }
            ),
        }


# Homework Review Form
class HomeworkReviewForm(forms.ModelForm):

    class Meta:
        model = HomeworkSubmission
        fields = ["marks", "feedback"]

        widgets = {
            "marks": forms.NumberInput(
                attrs={
                    "placeholder": "Enter marks",
                    "min": 0,
                }
            ),
            "feedback": forms.Textarea(
                attrs={
                    "rows": 4,
                    "placeholder": "Write feedback for the student..."
                }
            ),
        }

    def clean_marks(self):
        marks = self.cleaned_data.get("marks")

        if marks is not None:
            total_marks = self.instance.homework.total_marks

            if marks > total_marks:
                raise forms.ValidationError(
                    f"Marks cannot exceed {total_marks}."
                )

        return marks


# Fee Record Form
class FeeRecordForm(forms.ModelForm):

    class Meta:
        model = FeeRecord
        fields = [
            "student",
            "amount",
            "due_date",
            "status",
        ]

        widgets = {
            "due_date": forms.DateInput(
                attrs={"type": "date"}
            ),
        }


# Grade FormSet
GradeFormSet = modelformset_factory(
    Grade,
    form=GradeForm,
    extra=3,
    validate_min=True,
    min_num=1
)