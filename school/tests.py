
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
    Parent,
    Attendance,
    Grade,
    Homework,
    HomeworkSubmission,
    Timetable,
)
from .forms import HomeworkReviewForm


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

    def test_parent_cannot_view_other_child_detail(self):
        parent_group, _ = Group.objects.get_or_create(name="Parent")
        parent_user = User.objects.create_user(username="parent_user", password="TestPassword123!")
        parent_user.groups.add(parent_group)
        parent = Parent.objects.create(user=parent_user, first_name="Parent", last_name="User", email="parent@example.com")

        child_user = User.objects.create_user(username="child_user", password="TestPassword123!")
        child = Student.objects.create(user=child_user, first_name="Child", last_name="One", roll_number="C001", school_class=self.class_a)
        parent.students.add(child)

        other_user = User.objects.create_user(username="other_child_user", password="TestPassword123!")
        other_child = Student.objects.create(user=other_user, first_name="Other", last_name="Child", roll_number="C002", school_class=self.class_b)

        self.client.force_login(parent_user)
        response = self.client.get(reverse("parent_child_detail", args=[other_child.id]))
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_view_other_student_report_card(self):
        student_user = User.objects.create_user(username="student_1", password="TestPassword123!")
        student_user.groups.add(self.student_group)

        other_user = User.objects.create_user(username="student_2", password="TestPassword123!")
        other_user.groups.add(self.student_group)
        student_2 = Student.objects.create(user=other_user, first_name="Student", last_name="Two", roll_number="ST002", school_class=self.class_a)

        self.client.force_login(student_user)
        response = self.client.get(reverse("student_report_card", args=[student_2.id]))
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_select_another_student_report_card(self):
        student_user = User.objects.create_user(
            username="student_select_1",
            password="TestPassword123!",
        )
        student_user.groups.add(self.student_group)

        other_user = User.objects.create_user(
            username="student_select_2",
            password="TestPassword123!",
        )
        other_user.groups.add(self.student_group)

        other_student = Student.objects.create(
            user=other_user,
            first_name="Other",
            last_name="Student",
            roll_number="SEL002",
            school_class=self.class_a,
        )

        self.client.force_login(student_user)

        response = self.client.get(
            reverse("report_card_exam_select", args=[other_student.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_select_unassigned_class_report_card(self):
        student_user = User.objects.create_user(
            username="select_class_b",
            password="TestPassword123!",
        )
        student_user.groups.add(self.student_group)

        student_b = Student.objects.create(
            user=student_user,
            first_name="Class",
            last_name="B Student",
            roll_number="SEL003",
            school_class=self.class_b,
        )

        self.client.force_login(self.teacher_user)

        response = self.client.get(
            reverse("report_card_exam_select", args=[student_b.id])
        )

        self.assertEqual(response.status_code, 403)

    def test_teacher_cannot_access_unassigned_class_report_card(self):
        student_user = User.objects.create_user(username="student_in_b", password="TestPassword123!")
        student_user.groups.add(self.student_group)
        student_b = Student.objects.create(user=student_user, first_name="Student", last_name="B", roll_number="ST003", school_class=self.class_b)

        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("student_report_card", args=[student_b.id]))
        self.assertEqual(response.status_code, 403)

    def test_fees_views_are_admin_only(self):
        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("fee_record_list"))
        self.assertEqual(response.status_code, 403)

        response = self.client.get(reverse("fee_record_create"))
        self.assertEqual(response.status_code, 403)

        admin_user = User.objects.create_superuser(username="admin_user", password="TestPassword123!", email="admin@example.com")
        self.client.force_login(admin_user)
        response = self.client.get(reverse("fee_record_list"))
        self.assertEqual(response.status_code, 200)

    def test_attendance_permission_and_duplicate(self):
        teacher_without_perm = User.objects.create_user(username="teacher_no_perm", password="TestPassword123!")
        teacher_without_perm.groups.add(self.teacher_group)
        Teacher.objects.create(user=teacher_without_perm, first_name="No", last_name="Perm", email="noperm@example.com")

        self.client.force_login(teacher_without_perm)
        response = self.client.get(reverse("attendance_mark"))
        self.assertEqual(response.status_code, 403)

        content_type = ContentType.objects.get_for_model(Attendance)
        perm = Permission.objects.get(content_type=content_type, codename="add_attendance")
        self.teacher_user.user_permissions.add(perm)

        self.client.force_login(self.teacher_user)
        response = self.client.get(reverse("attendance_mark"))
        self.assertEqual(response.status_code, 200)

        student_user = User.objects.create_user(username="att_student", password="TestPassword123!")
        student = Student.objects.create(user=student_user, first_name="Att", last_name="Student", roll_number="ATT001", school_class=self.class_a)

        Attendance.objects.create(student=student, date=date(2026, 1, 1), status="Present")
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Attendance.objects.create(student=student, date=date(2026, 1, 1), status="Absent")

    def test_homework_review_marks_cannot_exceed_total(self):
        student_user = User.objects.create_user(username="hw_student", password="TestPassword123!")
        student = Student.objects.create(user=student_user, first_name="HW", last_name="Student", roll_number="HW001", school_class=self.class_a)
        submission = HomeworkSubmission.objects.create(homework=self.homework_a, student=student, answer="Done")

        form = HomeworkReviewForm(data={"marks": 150, "feedback": "Good job"}, instance=submission)
        self.assertFalse(form.is_valid())
        self.assertIn("marks", form.errors)

    def test_student_report_card_pdf_smoke(self):
        student_user = User.objects.create_user(username="pdf_student", password="TestPassword123!")
        student_user.groups.add(self.student_group)
        student = Student.objects.create(user=student_user, first_name="PDF", last_name="Student", roll_number="PDF001", school_class=self.class_a)
        Grade.objects.create(student=student, subject="Python", exam_name="Final Exam", total_marks=100, obtained_marks=90)

        self.client.force_login(student_user)
        response = self.client.get(reverse("student_report_card", args=[student.id]), {"exam_name": "Final Exam"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertTrue(len(response.content) > 0)
