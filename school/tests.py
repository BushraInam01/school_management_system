
from datetime import date

from django.contrib.auth.models import User, Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse

from .models import (
    SchoolClass,
    Student,
    Teacher,
    Grade,
    Homework,
    HomeworkSubmission,
    Timetable,
)


class SchoolModelTests(TestCase):
    """Tests for school model database constraints."""

    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            username="test_student",
            password="TestPassword123!",
        )

        # Create a school class
        self.school_class = SchoolClass.objects.create(
            name="Class 9",
            section="A",
        )

        # Create a student
        self.student = Student.objects.create(
            user=self.user,
            first_name="Test",
            last_name="Student",
            roll_number="TEST001",
            school_class=self.school_class,
        )

        # Create a teacher
        self.teacher = Teacher.objects.create(
            first_name="Test",
            last_name="Teacher",
            email="teacher_test@example.com",
        )

        # Create homework
        self.homework = Homework.objects.create(
            teacher=self.teacher,
            school_class=self.school_class,
            title="Python Homework",
            description="Complete the Python exercises.",
            due_date=date(2026, 12, 31),
            total_marks=100,
        )

    def test_grade_obtained_marks_cannot_exceed_total(self):
        """Obtained marks must not exceed total marks."""

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Grade.objects.create(
                    student=self.student,
                    subject="Python",
                    total_marks=100,
                    obtained_marks=110,
                )

    def test_grade_total_marks_cannot_be_zero(self):
        """Total marks must be greater than zero."""

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Grade.objects.create(
                    student=self.student,
                    subject="Python",
                    total_marks=0,
                    obtained_marks=0,
                )

    def test_student_cannot_submit_homework_twice(self):
        """A student cannot submit the same homework twice."""

        HomeworkSubmission.objects.create(
            homework=self.homework,
            student=self.student,
            answer="First submission",
        )

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                HomeworkSubmission.objects.create(
                    homework=self.homework,
                    student=self.student,
                    answer="Duplicate submission",
                )


class SchoolHomeworkAccessTests(TestCase):
    """Tests for teacher and student homework access."""

    def setUp(self):
        # Create Teacher and Student groups
        self.teacher_group, _ = Group.objects.get_or_create(
            name="Teacher",
        )
        self.student_group, _ = Group.objects.get_or_create(
            name="Student",
        )

        # Create two school classes
        self.class_a = SchoolClass.objects.create(
            name="Class 9",
            section="A",
        )
        self.class_b = SchoolClass.objects.create(
            name="Class 10",
            section="B",
        )

        # Create teacher accounts
        self.teacher_user = User.objects.create_user(
            username="teacher_test",
            password="TestPassword123!",
        )
        self.teacher_user.groups.add(self.teacher_group)

        self.other_teacher_user = User.objects.create_user(
            username="other_teacher",
            password="TestPassword123!",
        )
        self.other_teacher_user.groups.add(self.teacher_group)

        # Create teacher profiles
        self.teacher = Teacher.objects.create(
            user=self.teacher_user,
            first_name="Test",
            last_name="Teacher",
            email="teacher@example.com",
        )

        self.other_teacher = Teacher.objects.create(
            user=self.other_teacher_user,
            first_name="Other",
            last_name="Teacher",
            email="other_teacher@example.com",
        )

        # Assign teachers to different classes
        Timetable.objects.create(
            school_class=self.class_a,
            teacher=self.teacher,
            subject="Python",
            weekday="Monday",
            start_time="09:00",
            end_time="10:00",
        )

        Timetable.objects.create(
            school_class=self.class_b,
            teacher=self.other_teacher,
            subject="Math",
            weekday="Tuesday",
            start_time="10:00",
            end_time="11:00",
        )

        # Create homework for each class
        self.homework_a = Homework.objects.create(
            teacher=self.teacher,
            school_class=self.class_a,
            title="Python Homework",
            description="Complete Python exercises.",
            due_date=date(2026, 12, 31),
            total_marks=100,
        )

        self.homework_b = Homework.objects.create(
            teacher=self.other_teacher,
            school_class=self.class_b,
            title="Math Homework",
            description="Complete Math exercises.",
            due_date=date(2026, 12, 31),
            total_marks=100,
        )

        # Give the teacher permission to view homework
        content_type = ContentType.objects.get_for_model(Homework)

        view_permission = Permission.objects.get(
            content_type=content_type,
            codename="view_homework",
        )

        self.teacher_user.user_permissions.add(view_permission)

    def test_teacher_homework_list_only_shows_own_homework(self):
        """A teacher should only see their own homework."""

        self.client.login(
            username="teacher_test",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("teacher_homework_list"),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Python Homework")
        self.assertNotContains(response, "Math Homework")

    def test_student_cannot_open_homework_from_another_class(self):
        """A student cannot access homework assigned to another class."""

        student_user = User.objects.create_user(
            username="student_test",
            password="TestPassword123!",
        )
        student_user.groups.add(self.student_group)

        student = Student.objects.create(
            user=student_user,
            first_name="Test",
            last_name="Student",
            roll_number="ACCESS001",
            school_class=self.class_a,
        )

        self.client.login(
            username="student_test",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse(
                "homework_submit",
                args=[self.homework_b.id],
            ),
        )

        self.assertEqual(response.status_code, 404)

        self.assertFalse(
            HomeworkSubmission.objects.filter(
                student=student,
                homework=self.homework_b,
            ).exists()
        )

    def test_logout_get_request_is_not_allowed(self):
        self.client.login(
            username="teacher_test",
            password="TestPassword123!",
        )

        response = self.client.get(
            reverse("common_logout")
        )

        self.assertEqual(response.status_code, 405)

    def test_logout_post_request_logs_out_user(self):
        self.client.login(
            username="teacher_test",
            password="TestPassword123!",
        )

        response = self.client.post(
            reverse("common_logout")
        )

        self.assertRedirects(
            response,
            reverse("common_login"),
        )

        self.assertNotIn(
            "_auth_user_id",
            self.client.session,
        )
