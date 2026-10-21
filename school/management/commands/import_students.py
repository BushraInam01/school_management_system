import csv

from django.core.management.base import BaseCommand, CommandError

from school.models import Student, SchoolClass


class Command(BaseCommand):
    help = "Import students from a CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str)

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

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

                for row_number, row in enumerate(reader, start=2):
                    first_name = (row.get("first_name") or "").strip()
                    last_name = (row.get("last_name") or "").strip()
                    roll_number = (row.get("roll_number") or "").strip()
                    email = (row.get("email") or "").strip()
                    class_name = (row.get("school_class") or "").strip()

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

                    school_class = SchoolClass.objects.filter(
                        name=class_name
                    ).first()

                    if school_class is None:
                        self.stderr.write(
                            f"Row {row_number}: Class '{class_name}' "
                            "not found. Skipped."
                        )
                        skipped += 1
                        continue

                    Student.objects.create(
                        first_name=first_name,
                        last_name=last_name,
                        roll_number=roll_number,
                        email=email,
                        school_class=school_class,
                    )

                    imported += 1

        except FileNotFoundError:
            raise CommandError(f"CSV file not found: {csv_file}")

        self.stdout.write(
            self.style.SUCCESS(
                f"Import completed. Imported: {imported}, Skipped: {skipped}"
            )
        )
