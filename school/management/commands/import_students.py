import csv

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from school.models import Student, SchoolClass


class Command(BaseCommand):
    help = "Import students from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str)
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate import without committing changes to database",
        )

    def handle(self, *args, **options):
        csv_file = options["csv_file"]
        dry_run = options.get("dry_run", False)

        try:
            with open(
                csv_file,
                mode="r",
                encoding="utf-8-sig",
                newline=""
            ) as file:
                reader = csv.DictReader(file)

                required_columns = {
                    "first_name",
                    "last_name",
                    "roll_number",
                    "email",
                    "school_class",
                }

                if not reader.fieldnames:
                    raise CommandError("CSV file is empty.")

                missing_columns = required_columns - set(reader.fieldnames)

                if missing_columns:
                    raise CommandError(
                        "Missing CSV columns: "
                        + ", ".join(sorted(missing_columns))
                    )

                imported = 0
                skipped = 0

                with transaction.atomic():
                    for row_number, row in enumerate(reader, start=2):
                        first_name = (row.get("first_name") or "").strip()
                        last_name = (row.get("last_name") or "").strip()
                        roll_number = (row.get("roll_number") or "").strip()
                        email = (row.get("email") or "").strip()
                        class_name = (row.get("school_class") or "").strip()
                        section = (row.get("section") or "").strip()

                        if not all([
                            first_name,
                            last_name,
                            roll_number,
                            class_name,
                        ]):
                            self.stderr.write(
                                f"Row {row_number}: Required data missing. Skipped."
                            )
                            skipped += 1
                            continue

                        if Student.objects.filter(
                            roll_number=roll_number
                        ).exists():
                            self.stderr.write(
                                f"Row {row_number}: Roll number "
                                f"{roll_number} already exists. Skipped."
                            )
                            skipped += 1
                            continue

                        if section:
                            classes = SchoolClass.objects.filter(
                                name=class_name,
                                section=section
                            )
                        else:
                            classes = SchoolClass.objects.filter(
                                name=class_name
                            )

                        if classes.count() == 0:
                            self.stderr.write(
                                f"Row {row_number}: Class '{class_name}' "
                                "not found. Skipped."
                            )
                            skipped += 1
                            continue
                        elif classes.count() > 1:
                            self.stderr.write(
                                f"Row {row_number}: Class '{class_name}' "
                                "matches multiple classes. Please specify a section. Skipped."
                            )
                            skipped += 1
                            continue

                        school_class = classes.first()

                        student = Student(
                            first_name=first_name,
                            last_name=last_name,
                            roll_number=roll_number,
                            email=email,
                            school_class=school_class,
                        )

                        try:
                            student.full_clean()
                        except ValidationError as e:
                            self.stderr.write(
                                f"Row {row_number}: Validation error: {e}. Skipped."
                            )
                            skipped += 1
                            continue

                        student.save()
                        imported += 1

                    if dry_run:
                        transaction.set_rollback(True)
                        self.stdout.write(
                            self.style.WARNING("Dry run mode: changes were rolled back.")
                        )

        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {csv_file}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Imported: {imported}, Skipped: {skipped}"
            )
        )
