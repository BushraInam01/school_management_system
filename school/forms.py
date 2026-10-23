from datetime import date
from django import forms
from django.forms import modelformset_factory

from .models import (
    Attendance,
    Student,
    Teacher,
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

    def clean_date(self):
        date_value = self.cleaned_data.get("date")
        if date_value and date_value > date.today():
            raise forms.ValidationError("Attendance date cannot be in the future.")
        return date_value

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


# Grade Form
class GradeForm(forms.ModelForm):

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

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

                teacher_subjects = sorted(list(set(
                    Timetable.objects.filter(teacher=teacher).values_list("subject", flat=True)
                )))
                choices = [(s, s) for s in teacher_subjects]
                if self.instance and self.instance.pk and self.instance.subject:
                    if (self.instance.subject, self.instance.subject) not in choices:
                        choices.insert(0, (self.instance.subject, self.instance.subject))
                self.fields["subject"] = forms.ChoiceField(
                    choices=[("", "---------")] + choices
                )
            else:
                self.fields["student"].queryset = Student.objects.none()

    def clean_subject(self):
        subject = self.cleaned_data.get("subject")
        if subject:
            subject = subject.strip().title()
        return subject

    def clean(self):
        cleaned_data = super().clean()

        total_marks = cleaned_data.get("total_marks")
        obtained_marks = cleaned_data.get("obtained_marks")
        student = cleaned_data.get("student")
        subject = cleaned_data.get("subject")

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

        if self.user and not self.user.is_superuser and student and subject:
            teacher = getattr(self.user, "teacher", None)
            if teacher and student.school_class:
                if not Timetable.objects.filter(
                    teacher=teacher,
                    school_class=student.school_class,
                    subject__iexact=subject
                ).exists():
                    self.add_error(
                        "subject",
                        "You do not teach this subject to this student's class."
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
    teacher = forms.ModelChoiceField(
        queryset=Teacher.objects.all(),
        required=False
    )

    class Meta:
        model = Homework
        fields = [
            "teacher",
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
        self.user = user

        if user is not None and not user.is_superuser:
            self.fields.pop("teacher", None)
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
        else:
            if "teacher" in self.fields:
                self.fields["teacher"].required = True

    def clean_due_date(self):
        due_date = self.cleaned_data.get("due_date")
        if due_date:
            if not self.instance.pk and due_date < date.today():
                raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

    def clean_total_marks(self):
        total_marks = self.cleaned_data.get("total_marks")
        if total_marks is not None and total_marks <= 0:
            raise forms.ValidationError("Total marks must be greater than zero.")
        return total_marks

    def clean(self):
        cleaned_data = super().clean()
        teacher = cleaned_data.get("teacher")
        school_class = cleaned_data.get("school_class")

        if self.user and not self.user.is_superuser:
            teacher = getattr(self.user, "teacher", None)

        if teacher and school_class:
            if not Timetable.objects.filter(
                teacher=teacher,
                school_class=school_class
            ).exists():
                self.add_error(
                    "school_class",
                    "This teacher does not teach the selected class."
                )

        return cleaned_data


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
            if marks < 0:
                raise forms.ValidationError("Marks cannot be negative.")

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

    def clean_amount(self):
        amount = self.cleaned_data.get("amount")
        if amount is not None and amount < 0:
            raise forms.ValidationError("Fee amount cannot be negative.")
        return amount


# Grade FormSet
GradeFormSet = modelformset_factory(
    Grade,
    form=GradeForm,
    extra=3,
    validate_min=True,
    min_num=1
)