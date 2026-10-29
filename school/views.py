
import calendar
from datetime import date
from decimal import Decimal
from functools import wraps
from io import BytesIO
from urllib.parse import urlencode
from xml.sax.saxutils import escape

from django.core.exceptions import PermissionDenied
from django.urls import reverse
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count, Q, Case, When, Value, IntegerField
from django.db import IntegrityError, transaction
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .models import (
    Timetable,
    Teacher,
    Student,
    Parent,
    Grade,
    Homework,
    HomeworkSubmission,
    FeeRecord,
)

from .forms import (
    AttendanceForm,
    GradeForm,
    HomeworkForm,
    HomeworkSubmissionForm,
    HomeworkReviewForm,
    FeeRecordForm,
    GradeFormSet,
)


def _teacher_class_ids(teacher):
    return Timetable.objects.filter(
        teacher=teacher
    ).values_list("school_class_id", flat=True).distinct()


def get_teacher_or_403(request, perm=None, require_classes=False):
    if request.user.is_superuser:
        return getattr(request.user, "teacher", None)

    if not request.user.groups.filter(name="Teacher").exists():
        raise PermissionDenied("Access Denied: You are not a Teacher.")

    if perm and not request.user.has_perm(perm):
        raise PermissionDenied("You do not have permission to perform this action.")

    teacher = getattr(request.user, "teacher", None)
    if teacher is None:
        raise PermissionDenied("No Teacher profile is linked to this account.")

    if require_classes and not _teacher_class_ids(teacher).exists():
        raise PermissionDenied("No classes are assigned to this teacher.")

    return teacher


def role_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.groups.filter(name=group_name).exists():
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return login_required(wrapper)
    return decorator


# Teacher Dashboard
@role_required("Teacher")
def teacher_dashboard(request):
    return render(request, "school/dashboard.html", {"role": "Teacher"})


# Student Dashboard
@login_required
def student_dashboard(request):
    if request.user.groups.filter(name="Student").exists():
        return render(
            request,
            "school/dashboard.html",
            {"role": "Student"}
        )

    raise PermissionDenied("Access Denied: You are not a Student")


# Parent Dashboard
def _parent_children(user):
    parent = getattr(user, "parent", None)

    if parent is None:
        return []

    return list(
        parent.students.select_related("school_class").order_by(
            "first_name", "last_name"
        )
    )


# Parent Dashboard
@login_required
def parent_dashboard(request):
    if not request.user.groups.filter(name="Parent").exists():
        raise PermissionDenied("Access Denied: You are not a Parent")

    children = _parent_children(request.user)
    children_data = []

    for child in children:
        grades = Grade.objects.filter(
            student=child
        ).order_by("-created_at")

        homework_items = []

        if child.school_class_id:
            submissions = {
                s.homework_id: s
                for s in child.homework_submissions.all()
            }
            homeworks = Homework.objects.filter(
                school_class=child.school_class
            ).select_related("teacher").order_by("due_date")

            today = date.today()
            for homework in homeworks:
                submission = submissions.get(homework.id)
                if submission:
                    status = "Submitted"
                elif homework.due_date < today:
                    status = "Overdue"
                else:
                    status = "Pending"

                homework_items.append({
                    "homework": homework,
                    "submission": submission,
                    "status": status,
                })

        fees = list(
            FeeRecord.objects.filter(
                student=child
            ).order_by("-due_date")
        )

        total_fees = sum(
            (fee.amount for fee in fees),
            Decimal("0.00")
        )

        paid_fees = sum(
            (
                fee.amount
                for fee in fees
                if fee.status == "Paid"
            ),
            Decimal("0.00")
        )

        unpaid_fees = total_fees - paid_fees

        children_data.append({
            "child": child,
            "grades": grades,
            "homework_items": homework_items,
            "fees": fees,
            "total_fees": total_fees,
            "paid_fees": paid_fees,
            "unpaid_fees": unpaid_fees,
        })

    return render(
        request,
        "school/dashboard.html",
        {
            "role": "Parent",
            "children": children,
            "children_data": children_data,
        }
    )



# Login View
def common_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:
            login(request, user)

            # Admin / superuser access
            if user.is_superuser:
                return redirect("/admin/")

            # Redirect to the requested page, if provided
            next_url = request.POST.get("next") or request.GET.get("next")

            if next_url and url_has_allowed_host_and_scheme(
                next_url,
                allowed_hosts={request.get_host()},
                require_https=request.is_secure(),
            ):
                return redirect(next_url)

            # Role-based dashboard
            if user.groups.filter(name="Teacher").exists():
                return redirect("teacher_dashboard")

            elif user.groups.filter(name="Student").exists():
                return redirect("student_dashboard")

            elif user.groups.filter(name="Parent").exists():
                return redirect("parent_dashboard")

            logout(request)
            return render(request, "school/login.html", {"error": "Your account does not have a school role. Please contact the administrator.", "next": ""})

        return render(
            request,
            "school/login.html",
            {
                "error": "Invalid username or password",
                "next": request.POST.get("next", ""),
            }
        )

    return render(
        request,
        "school/login.html",
        {"next": request.GET.get("next", "")}
    )


# Homepage View
@login_required
def home_view(request):

    # Admin / superuser
    if request.user.is_superuser:
        return redirect("/admin/")

    # Teacher dashboard
    if request.user.groups.filter(name="Teacher").exists():
        return redirect("teacher_dashboard")

    # Student dashboard
    if request.user.groups.filter(name="Student").exists():
        return redirect("student_dashboard")

    # Parent dashboard
    if request.user.groups.filter(name="Parent").exists():
        return redirect("parent_dashboard")

    raise PermissionDenied("Your account does not have a school role.")



# Logout View
@login_required
@require_POST
def common_logout(request):
    logout(request)
    return redirect("common_login")



# Timetable View
@login_required
def timetable_view(request):

    weekday_order = Case(
        When(weekday="Monday", then=Value(1)),
        When(weekday="Tuesday", then=Value(2)),
        When(weekday="Wednesday", then=Value(3)),
        When(weekday="Thursday", then=Value(4)),
        When(weekday="Friday", then=Value(5)),
        When(weekday="Saturday", then=Value(6)),
        default=Value(7),
        output_field=IntegerField(),
    )

    # Teacher timetable
    if request.user.groups.filter(name="Teacher").exists():
        try:
            teacher = request.user.teacher
        except Teacher.DoesNotExist:
            raise PermissionDenied("No Teacher profile is linked to this account.")

        timetables = Timetable.objects.filter(
            teacher=teacher
        ).select_related(
            "school_class",
            "teacher",
        ).order_by(
            weekday_order,
            "start_time",
        )

    # Student timetable
    elif request.user.groups.filter(name="Student").exists():
        try:
            student = request.user.student
        except Student.DoesNotExist:
            raise PermissionDenied("No Student profile is linked to this account.")

        if student.school_class:
            timetables = Timetable.objects.filter(
                school_class=student.school_class
            ).select_related(
                "school_class",
                "teacher",
            ).order_by(
                weekday_order,
                "start_time",
            )
        else:
            timetables = Timetable.objects.none()

    # Parent timetable
    elif request.user.groups.filter(name="Parent").exists():
        try:
            parent = request.user.parent
        except Parent.DoesNotExist:
            raise PermissionDenied("No Parent profile is linked to this account.")

        student_classes = parent.students.filter(
            school_class__isnull=False
        ).values_list(
            "school_class_id",
            flat=True,
        ).distinct()

        timetables = Timetable.objects.filter(
            school_class_id__in=student_classes
        ).select_related(
            "school_class",
            "teacher",
        ).order_by(
            weekday_order,
            "start_time",
        )

    # Unauthorized user
    else:
        raise PermissionDenied("Access Denied: You are not authorized.")

    return render(
        request,
        "school/timetable.html",
        {"timetables": timetables},
    )



# Attendance Marking View
@login_required
def attendance_mark(request):
    get_teacher_or_403(request, "school.add_attendance")

    if request.method == "POST":
        form = AttendanceForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Attendance marked successfully!")
            return redirect("attendance_mark")
    else:
        form = AttendanceForm(user=request.user)

    return render(
        request,
        "school/attendance_form.html",
        {"form": form}
    )


# Monthly Attendance Report
@login_required
def monthly_attendance_report(request):

    if not request.user.is_superuser:
        raise PermissionDenied("Only admin can view attendance reports.")

    today = date.today()

    month = request.GET.get("month", today.month)
    year = request.GET.get("year", today.year)

    try:
        month = int(month)
        year = int(year)

        if not 1 <= month <= 12 or not 1 <= year <= 9999:
            raise ValueError

    except (ValueError, TypeError):
        messages.error(request, "Invalid month or year.")
        return redirect("monthly_attendance_report")

    report = Student.objects.annotate(
        present_count=Count(
            "attendance_records",
            filter=Q(
                attendance_records__date__month=month,
                attendance_records__date__year=year,
                attendance_records__status="Present",
            ),
        ),
        absent_count=Count(
            "attendance_records",
            filter=Q(
                attendance_records__date__month=month,
                attendance_records__date__year=year,
                attendance_records__status="Absent",
            ),
        ),
    ).order_by("first_name", "last_name")

    return render(
        request,
        "school/monthly_attendance_report.html",
        {
            "report": report,
            "month": month,
            "year": year,
            "month_name": calendar.month_name[month],
        },
    )


# Grade Entry View
@login_required
def grade_entry(request):
    get_teacher_or_403(request, "school.add_grade", require_classes=True)

    if request.method == "POST":
        form = GradeForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Grade saved successfully!")
            return redirect("grade_entry")
    else:
        form = GradeForm(user=request.user)

    return render(
        request,
        "school/grade_form.html",
        {"form": form}
    )


@login_required
def bulk_grade_entry(request):
    get_teacher_or_403(request, "school.add_grade", require_classes=True)

    if request.method == "POST":
        formset = GradeFormSet(
            request.POST,
            form_kwargs={"user": request.user},
            queryset=Grade.objects.none()
        )

        if formset.is_valid():
            formset.save()
            messages.success(request, "All grades saved successfully!")
            return redirect("bulk_grade_entry")
    else:
        formset = GradeFormSet(
            form_kwargs={"user": request.user},
            queryset=Grade.objects.none()
        )

    return render(
        request,
        "school/bulk_grade_entry.html",
        {"formset": formset}
    )




def get_accessible_student(request, student_id=None):
    is_teacher = request.user.groups.filter(name="Teacher").exists()
    is_student = request.user.groups.filter(name="Student").exists()

    # Students can access only their own report card
    if is_student and not request.user.is_superuser:
        try:
            student = request.user.student
        except Student.DoesNotExist:
            raise PermissionDenied(
                "No Student profile is linked to this account."
            )

        if student_id is not None and student.id != student_id:
            raise PermissionDenied(
                "You can only access your own report card."
            )

        return student

    # Parents can access only their own children
    elif (
        request.user.groups.filter(name="Parent").exists()
        and not request.user.is_superuser
    ):
        if student_id is None:
            messages.error(request, "Please provide a student ID.")
            return redirect("dashboard")

        try:
            parent = request.user.parent
        except Parent.DoesNotExist:
            raise PermissionDenied(
                "No Parent profile is linked to this account."
            )

        return get_object_or_404(
            parent.students.select_related("school_class"),
            id=student_id
        )

    # Superusers and teachers
    elif request.user.is_superuser or is_teacher:
        if student_id is None:
            messages.error(request, "Please provide a student ID.")
            return redirect("dashboard")

        student = get_object_or_404(
            Student.objects.select_related("school_class"),
            id=student_id
        )

        # Teachers can access only their assigned classes
        if is_teacher and not request.user.is_superuser:
            teacher = get_teacher_or_403(request)
            assigned_classes = _teacher_class_ids(teacher)

            if (
                student.school_class_id is None
                or student.school_class_id not in assigned_classes
            ):
                raise PermissionDenied(
                    "You can only access report cards for your assigned classes."
                )

        return student

    raise PermissionDenied(
        "Access Denied: You are not authorized."
    )



# PDF Student Report Card View
@login_required
def student_report_card(request, student_id=None):
    student = get_accessible_student(request, student_id)

    if not isinstance(student, Student):
        return student

    # Read the selected exam from the URL
    exam_name = request.GET.get("exam_name", "").strip()

    # Redirect to exam selection if no valid exam is selected
    if not exam_name or not Grade.objects.filter(
        student=student,
        exam_name=exam_name
    ).exists():
        return redirect(
            "report_card_exam_select",
            student_id=student.id
        )

    # Get grades for this student and selected exam only
    grades = Grade.objects.filter(
        student=student,
        exam_name=exam_name
    ).order_by("subject")

    # Create PDF in memory
    buffer = BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    styles = getSampleStyleSheet()
    content = []

    content.append(
        Paragraph(
            f"STUDENT REPORT CARD - {escape(exam_name)}",
            styles["Title"]
        )
    )
    content.append(Spacer(1, 20))

    student_name = escape(
        f"{student.first_name} {student.last_name}"
    )
    roll_number = escape(student.roll_number)
    school_class = escape(
        str(student.school_class or "Not Assigned")
    )

    content.append(
        Paragraph(
            f"<b>Student Name:</b> {student_name}",
            styles["Normal"]
        )
    )
    content.append(
        Paragraph(
            f"<b>Roll Number:</b> {roll_number}",
            styles["Normal"]
        )
    )
    content.append(
        Paragraph(
            f"<b>Class:</b> {school_class}",
            styles["Normal"]
        )
    )
    content.append(Spacer(1, 20))

    table_data = [
        ["Subject", "Obtained Marks", "Total Marks", "Percentage"]
    ]
    total_obtained = 0
    total_marks = 0

    for grade in grades:
        percentage = (
            grade.obtained_marks / grade.total_marks * 100
            if grade.total_marks > 0
            else 0
        )

        table_data.append([
            grade.subject,
            str(grade.obtained_marks),
            str(grade.total_marks),
            f"{percentage:.2f}%",
        ])

        total_obtained += grade.obtained_marks
        total_marks += grade.total_marks

    overall_percentage = (
        total_obtained / total_marks * 100
        if total_marks > 0
        else 0
    )

    table_data.append([
        "TOTAL",
        str(total_obtained),
        str(total_marks),
        f"{overall_percentage:.2f}%",
    ])

    marks_table = Table(
        table_data,
        colWidths=[180, 110, 100, 90],
        repeatRows=1,
    )
    marks_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.navy),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BACKGROUND", (0, -1), (-1, -1), colors.lightgrey),
            ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
            ("TOPPADDING", (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ])
    )

    content.append(marks_table)
    content.append(Spacer(1, 20))
    content.append(
        Paragraph(
            f"<b>Overall Percentage:</b> {overall_percentage:.2f}%",
            styles["Normal"]
        )
    )

    pdf.build(content)
    pdf_data = buffer.getvalue()
    buffer.close()

    response = HttpResponse(
        pdf_data,
        content_type="application/pdf"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="report_card_{student.roll_number}.pdf"'
    )
    return response

# Report Card Exam Selection View
@login_required
def report_card_exam_select(request, student_id=None):
    student = get_accessible_student(request, student_id)

    if not isinstance(student, Student):
        return student

    exam_names = (
        Grade.objects.filter(student=student)
        .values_list("exam_name", flat=True)
        .distinct()
        .order_by("exam_name")
    )

    if request.method == "POST":
        exam_name = request.POST.get("exam_name", "").strip()

        exam_exists = Grade.objects.filter(
            student=student,
            exam_name=exam_name
        ).exists()

        if not exam_exists:
            return render(
                request,
                "school/report_card_exam_select.html",
                {
                    "student": student,
                    "exam_names": exam_names,
                    "error": "Please select a valid exam.",
                }
            )

        report_url = reverse(
            "student_report_card",
            kwargs={"student_id": student.id}
        )
        query_string = urlencode({
            "exam_name": exam_name
        })

        return redirect(f"{report_url}?{query_string}")

    return render(
        request,
        "school/report_card_exam_select.html",
        {
            "student": student,
            "exam_names": exam_names,
        }
    )


# Homework Assignment View
@login_required
def homework_create(request):
    teacher = get_teacher_or_403(request, "school.add_homework")

    if request.method == "POST":
        form = HomeworkForm(
            request.POST,
            user=request.user
        )

        if form.is_valid():
            homework = form.save(commit=False)

            if teacher is not None:
                if not Timetable.objects.filter(
                    teacher=teacher,
                    school_class=homework.school_class
                ).exists():
                    raise PermissionDenied("You cannot assign homework to this class.")

                homework.teacher = teacher
            else:
                homework.teacher = form.cleaned_data["teacher"]

            homework.save()

            messages.success(request, "Homework assigned successfully!")
            return redirect("teacher_homework_list")

    else:
        form = HomeworkForm(user=request.user)

    return render(
        request,
        "school/homework_form.html",
        {"form": form}
    )

# Teacher's Homework List View
@login_required
def teacher_homework_list(request):
    teacher = get_teacher_or_403(request, "school.view_homework")

    if request.user.is_superuser:
        homeworks = Homework.objects.select_related(
            "teacher",
            "school_class"
        ).order_by("-due_date")
    else:
        homeworks = Homework.objects.filter(
            teacher=teacher
        ).select_related(
            "teacher",
            "school_class"
        ).order_by("-due_date")

    return render(
        request,
        "school/teacher_homework_list.html",
        {"homeworks": homeworks}
    )


# Student Homework List View
@login_required
def student_homework_list(request):

    if not request.user.groups.filter(
        name="Student"
    ).exists():
        raise PermissionDenied("Only students can view homework.")

    try:
        student = request.user.student
    except Student.DoesNotExist:
        raise PermissionDenied("No Student profile is linked to this account.")

    if student.school_class:
        submissions = {
            s.homework_id: s
            for s in student.homework_submissions.all()
        }
        homeworks = Homework.objects.filter(
            school_class=student.school_class
        ).select_related(
            "teacher",
            "school_class"
        ).order_by("due_date")

        today = date.today()

        for homework in homeworks:
            submission = submissions.get(homework.id)
            homework.is_submitted = submission is not None

            if homework.is_submitted:
                homework.status = "Submitted"
            elif homework.due_date < today:
                homework.status = "Overdue"
            else:
                homework.status = "Pending"

    else:
        homeworks = Homework.objects.none()

    return render(
        request,
        "school/student_homework_list.html",
        {"homeworks": homeworks}
    )

# Homework Submission View
@login_required
def homework_submit(request, homework_id):

    if not request.user.groups.filter(name="Student").exists():
        raise PermissionDenied("Only students can submit homework.")

    try:
        student = request.user.student
    except Student.DoesNotExist:
        raise PermissionDenied("No Student profile is linked to this account.")

    try:
        homework = Homework.objects.get(
            id=homework_id,
            school_class=student.school_class
        )
    except Homework.DoesNotExist:
        raise Http404("Homework not found for your class.")

    if HomeworkSubmission.objects.filter(
        homework=homework,
        student=student
    ).exists():
        messages.info(request, "You have already submitted this homework.")
        return redirect("student_homework_list")

    if date.today() > homework.due_date:
        messages.error(request, "The due date has passed. You can no longer submit this homework.")
        return redirect("student_homework_list")

    if request.method == "POST":
        form = HomeworkSubmissionForm(request.POST)

        if form.is_valid():
            try:
                with transaction.atomic():
                    submission = form.save(commit=False)
                    submission.student = student
                    submission.homework = homework
                    submission.save()

                messages.success(request, "Homework submitted successfully!")
                return redirect("student_homework_list")

            except IntegrityError:
                messages.info(request, "You have already submitted this homework.")
                return redirect("student_homework_list")

    else:
        form = HomeworkSubmissionForm()

    return render(
        request,
        "school/homework_submission_form.html",
        {
            "form": form,
            "homework": homework,
        }
    )



# Teacher Homework Submissions View
@login_required
def homework_submissions(request, homework_id):
    teacher = get_teacher_or_403(request, "school.view_homeworksubmission")

    homework = get_object_or_404(
        Homework,
        id=homework_id
    )

    if not request.user.is_superuser:
        if homework.teacher != teacher:
            raise PermissionDenied("You can only view submissions for your own homework.")

    submissions = homework.submissions.select_related(
        "student"
    ).order_by("submitted_at")

    return render(
        request,
        "school/homework_submissions.html",
        {
            "homework": homework,
            "submissions": submissions,
        }
    )


# Homework Review View
@login_required
def homework_review(request, submission_id):
    teacher = get_teacher_or_403(request, "school.change_homeworksubmission")

    submission = get_object_or_404(
        HomeworkSubmission,
        id=submission_id
    )

    if not request.user.is_superuser:
        if submission.homework.teacher != teacher:
            raise PermissionDenied("You can only review your own homework submissions.")

    if request.method == "POST":
        form = HomeworkReviewForm(
            request.POST,
            instance=submission
        )

        if form.is_valid():
            form.save()
            messages.success(request, "Homework reviewed successfully!")
            return redirect("homework_submissions", homework_id=submission.homework_id)
    else:
        form = HomeworkReviewForm(
            instance=submission
        )

    return render(
        request,
        "school/homework_review_form.html",
        {
            "form": form,
            "submission": submission,
        }
    )


# Student Homework Results View
@login_required
def my_homework_results(request):

    if not request.user.groups.filter(
        name="Student"
    ).exists():
        raise PermissionDenied("Only students can view their homework results.")

    try:
        student = request.user.student
    except Student.DoesNotExist:
        raise PermissionDenied("No Student profile is linked to this account.")

    submissions = HomeworkSubmission.objects.filter(
        student=student
    ).select_related(
        "homework",
        "homework__teacher"
    ).order_by("-submitted_at")

    return render(
        request,
        "school/my_homework_results.html",
        {"submissions": submissions}
    )


# Fee Record Create View
@login_required
def fee_record_create(request):
    if not request.user.is_superuser:
        raise PermissionDenied("Access Denied: Admin only.")

    if request.method == "POST":
        form = FeeRecordForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("fee_record_list")
    else:
        form = FeeRecordForm()

    return render(
        request,
        "school/fee_record_form.html",
        {"form": form}
    )

# Fee Record List View
@login_required
def fee_record_list(request):

    if not request.user.is_superuser:
        raise PermissionDenied("Access Denied: Admin only.")

    fee_records = FeeRecord.objects.select_related(
        "student"
    ).order_by("-created_at")

    return render(
        request,
        "school/fee_record_list.html",
        {"fee_records": fee_records}
    )


# Edit Fee Record View
@login_required
def fee_record_edit(request, fee_id):
    if not request.user.is_superuser:
        raise PermissionDenied("Access Denied: Admin only.")

    fee_record = get_object_or_404(FeeRecord, id=fee_id)

    if request.method == "POST":
        form = FeeRecordForm(request.POST, instance=fee_record)

        if form.is_valid():
            form.save()
            return redirect("fee_record_list")
    else:
        form = FeeRecordForm(instance=fee_record)

    return render(
        request,
        "school/fee_record_edit.html",
        {"form": form, "fee_record": fee_record}
    )


# Delete Fee Record View
@login_required
def fee_record_delete(request, fee_id):
    if not request.user.is_superuser:
        raise PermissionDenied("Access Denied: Admin only.")

    fee_record = get_object_or_404(FeeRecord, id=fee_id)

    if request.method == "POST":
        fee_record.delete()
        return redirect("fee_record_list")

    return render(
        request,
        "school/fee_record_delete.html",
        {"fee_record": fee_record}
    )


#Dashboard Redirect
@login_required
def dashboard_redirect(request):
    if request.user.groups.filter(name="Teacher").exists():
        return redirect("teacher_dashboard")
    if request.user.groups.filter(name="Student").exists():
        return redirect("student_dashboard")
    if request.user.groups.filter(name="Parent").exists():
        return redirect("parent_dashboard")
    if request.user.is_superuser:
        return redirect("fee_record_list")
    return redirect("/")



@login_required
def grade_edit(request, grade_id):
    grade = get_object_or_404(Grade, id=grade_id)

    if not request.user.is_superuser:
        teacher = get_teacher_or_403(request, "school.change_grade")
        if not Timetable.objects.filter(
            teacher=teacher,
            school_class=grade.student.school_class,
            subject__iexact=grade.subject
        ).exists():
            raise PermissionDenied("You can only edit grades for subjects and classes you teach.")

    if request.method == "POST":
        form = GradeForm(
            request.POST,
            instance=grade,
            user=request.user
        )
        if form.is_valid():
            form.save()
            messages.success(request, "Grade updated successfully!")
            return redirect("grade_entry")
    else:
        form = GradeForm(instance=grade, user=request.user)

    return render(
        request,
        "school/grade_form.html",
        {"form": form}
    )


@role_required("Parent")
def parent_child_detail(request, student_id):
    parent = getattr(request.user, "parent", None)

    if parent is None:
        raise PermissionDenied("No Parent profile is linked to this account.")

    student = get_object_or_404(
        parent.students.select_related("school_class"),
        id=student_id
    )

    grades = student.grades.order_by("exam_name", "subject")
    fee_records = student.fee_records.order_by("-due_date")

    submissions = {
        s.homework_id: s
        for s in student.homework_submissions.all()
    }

    homework_rows = []

    if student.school_class:
        today = date.today()
        homeworks = Homework.objects.filter(
            school_class=student.school_class
        ).select_related("teacher").order_by("due_date")

        for homework in homeworks:
            submission = submissions.get(homework.id)

            if submission:
                status = "Submitted"
            elif homework.due_date < today:
                status = "Overdue"
            else:
                status = "Pending"

            homework_rows.append({
                "homework": homework,
                "submission": submission,
                "status": status,
            })

    return render(
        request,
        "school/parent_child_detail.html",
        {
            "student": student,
            "grades": grades,
            "homework_rows": homework_rows,
            "fee_records": fee_records,
        },
    )


@login_required
@role_required("Parent")
def parent_fee_records(request, student_id):
    parent = getattr(request.user, "parent", None)

    if parent is None:
        raise PermissionDenied("No Parent profile is linked to this account.")

    student = get_object_or_404(
        parent.students.all(),
        id=student_id
    )

    fee_records = student.fee_records.order_by("-due_date")

    return render(
        request,
        "school/parent_fee_records.html",
        {
            "student": student,
            "fee_records": fee_records,
        }
    )


@login_required
@role_required("Parent")
def parent_fee_receipt_pdf(request, student_id, fee_id):
    from io import BytesIO
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from django.http import HttpResponse

    parent = getattr(request.user, "parent", None)

    if parent is None:
        raise PermissionDenied("No Parent profile is linked to this account.")

    student = get_object_or_404(
        parent.students.all(),
        id=student_id
    )

    fee = get_object_or_404(
        student.fee_records.all(),
        id=fee_id
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
    )

    styles = getSampleStyleSheet()
    elements = [
        Paragraph("School Fee Record", styles["Title"]),
        Spacer(1, 12),
        Paragraph(f"Student: {student}", styles["Normal"]),
        Paragraph(f"Roll Number: {student.roll_number}", styles["Normal"]),
        Spacer(1, 12),
    ]

    data = [
        ["Fee Detail", "Information"],
        ["Amount", f"Rs. {fee.amount}"],
        ["Due Date", fee.due_date.strftime("%d-%m-%Y")],
        ["Status", fee.status],
        ["Record Created", fee.created_at.strftime("%d-%m-%Y")],
    ]

    table = Table(data, colWidths=[55 * mm, 90 * mm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))

    elements.append(table)
    document.build(elements)

    response = HttpResponse(
        buffer.getvalue(),
        content_type="application/pdf"
    )
    response["Content-Disposition"] = (
        f'attachment; filename="fee_record_{fee.id}.pdf"'
    )
    return response