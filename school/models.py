from django.db import models
from django.contrib.auth.models import User


# class School
class SchoolClass(models.Model):
    name = models.CharField(max_length=50)
    section = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name


# Class Student
class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True)

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# Class Teacher
class Teacher(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"





# Class Parent

class Parent(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)

    students = models.ManyToManyField(
        Student,
        related_name="parents",
        blank=True,
    )

    def __str__(self):
        return f"{self.first_name} {self.last_name}"



# Class Timetable
class Timetable(models.Model):

    WEEKDAYS = [
        ("Monday", "Monday"),
        ("Tuesday", "Tuesday"),
        ("Wednesday", "Wednesday"),
        ("Thursday", "Thursday"),
        ("Friday", "Friday"),
        ("Saturday", "Saturday"),
    ]

    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.PROTECT
    )

    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT
    )

    subject = models.CharField(max_length=100)

    weekday = models.CharField(
        max_length=10,
        choices=WEEKDAYS
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.school_class} - {self.subject} - {self.weekday}"




# Class Attendance
class Attendance(models.Model):

    STATUS_CHOICES = [
        ("Present", "Present"),
        ("Absent", "Absent"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="attendance_records"
    )

    date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES
    )

    class Meta:
        unique_together = ("student", "date")

    def __str__(self):
        return f"{self.student} - {self.date} - {self.status}"



# Grade Model
class Grade(models.Model):
    EXAM_CHOICES = [
        ("Quiz", "Quiz"),
        ("Mid Term", "Mid Term"),
        ("Final Exam", "Final Exam"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="grades"
    )

    subject = models.CharField(max_length=100)

    exam_name = models.CharField(
        max_length=100,
        choices=EXAM_CHOICES,
        default="Final Exam"
    )

    total_marks = models.PositiveIntegerField(default=100)

    obtained_marks = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.subject} - {self.exam_name}"

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(total_marks__gt=0),
                name="grade_total_marks_gt_zero",
            ),
            models.CheckConstraint(
                condition=models.Q(
                    obtained_marks__lte=models.F("total_marks")
                ),
                name="grade_obtained_lte_total",
            ),
            models.UniqueConstraint(
                fields=["student", "subject", "exam_name"],
                name="unique_grade_per_student_subject_exam",
            ),
        ]



# Homework Model
class Homework(models.Model):
    teacher = models.ForeignKey(
        Teacher,
        on_delete=models.PROTECT,
        related_name="homeworks"
    )
    school_class = models.ForeignKey(
        SchoolClass,
        on_delete=models.CASCADE,
        related_name="homeworks"
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateField()
    total_marks = models.PositiveIntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


# Homework Submission Model
class HomeworkSubmission(models.Model):
    homework = models.ForeignKey(
        Homework,
        on_delete=models.CASCADE,
        related_name="submissions"
    )

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name="homework_submissions"
    )

    answer = models.TextField()
    feedback = models.TextField(blank=True)
    marks = models.PositiveIntegerField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["homework", "student"],
                name="unique_student_homework_submission"
            )
        ]

    def __str__(self):
        return f"{self.student} - {self.homework.title}"


# Fee Model
class FeeRecord(models.Model):
    STATUS_CHOICES = [
        ("Unpaid", "Unpaid"),
        ("Paid", "Paid"),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.PROTECT,
        related_name="fee_records"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    due_date = models.DateField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="Unpaid"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student} - {self.amount} - {self.status}"