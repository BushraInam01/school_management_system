
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

from school.models import (
    Attendance,
    Grade,
    Homework,
    HomeworkSubmission,
)


class Command(BaseCommand):
    help = "Create school role groups and configure teacher permissions."

    def handle(self, *args, **options):
        role_names = ["Teacher", "Student", "Parent"]

        for role_name in role_names:
            Group.objects.get_or_create(name=role_name)

        teacher_permissions = [
            ("attendance", Attendance, "add"),
            ("grade", Grade, "add"),
            ("grade", Grade, "change"),
            ("homework", Homework, "add"),
            ("homework", Homework, "view"),
            ("homeworksubmission", HomeworkSubmission, "view"),
            ("homeworksubmission", HomeworkSubmission, "change"),
        ]

        teacher_group = Group.objects.get(name="Teacher")

        for model_name, model, action in teacher_permissions:
            content_type = ContentType.objects.get_for_model(model)
            codename = f"{action}_{model_name}"

            permission = Permission.objects.get(
                content_type=content_type,
                codename=codename,
            )

            teacher_group.permissions.add(permission)

        self.stdout.write(
            self.style.SUCCESS(
                "Teacher, Student, and Parent groups are ready. "
                "Teacher permissions have been configured."
            )
        )
