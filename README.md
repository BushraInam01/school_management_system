
# 🎓 School Management System

A Django-based School Management System built to manage students, teachers, parents, classes, timetables, attendance, grades, homework, and fee records through role-based dashboards.

This project demonstrates practical Django backend development using Models, Views, Forms, Templates, Authentication, Groups & Permissions, Formsets, Django Admin, CSV imports, and PDF report card generation.

## 📌 Table of Contents

- [Project Overview](#-project-overview)
- [Features](#-features)
- [User Roles](#-user-roles)
- [Technology Stack](#-technology-stack)
- [Project Structure](#-project-structure)
- [Installation and Setup](#-installation-and-setup)
- [Application URLs](#-application-urls)
- [Testing and Verification](#-testing-and-verification)
- [CSV Student Import](#-csv-student-import)
- [PDF Report Cards](#-pdf-report-cards)
- [Groups and Permissions](#-groups-and-permissions)
- [Django Admin](#-django-admin)
- [Future Improvements](#-future-improvements)

---

## 📖 Project Overview

The School Management System provides separate dashboards for students, teachers, and parents, along with administrative functionality for managing school records.

Students can view their timetables, assigned homework, homework results, and report cards. Teachers can mark attendance, enter grades, assign homework, and review student submissions. Parents can view their children's timetables and report cards. Administrators can manage school records, fees, and restricted reports.

The project focuses on practical Django backend concepts, database relationships, form handling, authentication, authorization, data import, and PDF generation.

## ✨ Features

### 🔐 Authentication and Role-Based Dashboards
- Common login and logout functionality.
- Separate Student, Teacher, and Parent dashboards.
- Role-based navigation using Django templates.
- Access restrictions using Django Groups and Permissions.
- View-level authorization checks for protected actions.

### 👨‍🎓 Student and Class Management
- Student records and roll numbers.
- Class management and student-to-class relationships.
- Student, teacher, and parent profile relationships.
- Student record management through Django Admin.
- CSV-based student import through a custom management command.

### 📅 Timetable Management
- Class timetable and scheduling records.
- Subject, teacher, day, and time information.
- Student timetable access.
- Teacher timetable access.
- Parent access to their children's timetables.

### 🗓️ Attendance Management
- Teacher attendance marking.
- Attendance records linked to students and dates.
- Monthly attendance reporting for administrators.
- Attendance record management through Django Admin.

### 📊 Grade Management
- Individual grade entry.
- Bulk grade entry using Django formsets.
- Student grade records.
- Permission-protected grade entry.
- PDF report card generation.

### 📝 Homework Management
- Teachers can create and assign homework.
- Students can submit homework.
- Teachers can view student submissions.
- Teachers can review submissions and assign marks.
- Teachers can provide feedback.
- Students can view their homework results and feedback.

### 💰 Fee Management
- Student fee records.
- Paid and unpaid fee statuses.
- Create, edit, and delete fee records.
- Administrative access restrictions.

### 🖥️ Django Admin
- Registered school management models.
- Student-related attendance and grade inlines.
- Centralized school record management.
- User, group, and permission management.

---

## 👥 User Roles

| Role | Responsibilities |
|---|---|
| **Student** | View timetable, homework, homework results, and report card |
| **Teacher** | View timetable, mark attendance, enter grades, assign homework, review submissions |
| **Parent** | View their children's timetables and report cards |
| **Administrator** | Manage school records, fees, permissions, and monthly attendance reports |

Access to protected operations depends on the user's authentication, group membership, permissions, and the relevant view-level checks.

## 🛠️ Technology Stack

- **Language:** Python
- **Backend Framework:** Django
- **Frontend:** HTML and Django Templates
- **Forms:** Django Forms and ModelForms
- **Bulk Grade Entry:** Django Formsets
- **Database:** Django-configured database (SQLite for the default local setup)
- **Authentication:** Django Authentication System
- **Authorization:** Django Groups and Permissions
- **PDF Generation:** ReportLab
- **Data Import:** CSV and Django Management Commands
- **Administration:** Django Admin
- **Configuration:** Environment variables using `python-dotenv`

## 📂 Project Structure

```text
school_management_system/
│
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── asgi.py
│   └── wsgi.py
│
├── data/
│   └── students.csv
│
├── school/
│   ├── migrations/
│   ├── management/
│   │   └── commands/
│   │       └── import_students.py
│   ├── templates/
│   │   └── school/
│   ├── admin.py
│   ├── apps.py
│   ├── forms.py
│   ├── models.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── .gitignore
├── .env                 # Local only; do not commit
├── manage.py
├── requirements.txt
└── README.md
```

## 🚀 Installation and Setup

### Prerequisites

- Python 3.14.4 or another Python version compatible with the project's Django version.
- Git.
- A terminal such as Ubuntu/WSL.

### Step 1: Clone the Repository

Replace the placeholder with your actual GitHub repository URL.

```bash
git clone https://github.com/BushraInam01/school_management_system.git
cd school_management_system
```

### Step 2: Create and Activate a Virtual Environment

On Ubuntu/WSL:

```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a local `.env` file in the project root:

```text
DJANGO_SECRET_KEY=replace-with-a-new-random-secret-key
DJANGO_DEBUG=True
```

Use a unique secret key and keep `.env` out of Git. The provided development configuration defaults `DEBUG` to `False` when the variable is not set to `"True"`.

For production deployment, set `DJANGO_DEBUG=False` and configure `ALLOWED_HOSTS` appropriately.

### Step 5: Apply Database Migrations

```bash
python manage.py migrate
```

The project contains migrations for the school models. `makemigrations` is generally needed only when you make model changes without corresponding migrations.

### Step 6: Create an Administrator Account

```bash
python manage.py createsuperuser
```

Follow the prompts to create the account.

### Step 7: Start the Development Server

```bash
python manage.py runserver
```

Open the application:

http://127.0.0.1:8000/

### Step 8: Configure User Roles

1. Log in to Django Admin.
2. Create or verify the `Teacher`, `Student`, and `Parent` groups.
3. Assign the required permissions to each group.
4. Add users to the appropriate groups.
5. Create the related student, teacher, parent, and class records required by the application.

---

## 🔗 Application URLs

**Base URL:** `http://127.0.0.1:8000/`

Start the Django development server before opening the links. These are local development URLs, not public deployment links.

### 🔐 Authentication and Dashboards

| Page | URL |
|---|---|
| Teacher Dashboard | [Open Teacher Dashboard](http://127.0.0.1:8000/teacher-dashboard/) |
| Student Dashboard | [Open Student Dashboard](http://127.0.0.1:8000/student-dashboard/) |
| Parent Dashboard | [Open Parent Dashboard](http://127.0.0.1:8000/parent-dashboard/) |
| Login | [Open Login](http://127.0.0.1:8000/login/) |
| Logout | [Logout](http://127.0.0.1:8000/logout/) |
| Django Admin | [Open Admin Panel](http://127.0.0.1:8000/admin/) |

### 📅 Timetable and Attendance

| Page | URL |
|---|---|
| Timetable | [View Timetable](http://127.0.0.1:8000/timetable/) |
| Mark Attendance | [Mark Attendance](http://127.0.0.1:8000/attendance/mark/) |
| Monthly Attendance Report | [View Attendance Report](http://127.0.0.1:8000/attendance/report/) |

### 📊 Grades and Report Cards

| Page | URL |
|---|---|
| Individual Grade Entry | [Grade Entry](http://127.0.0.1:8000/grades/entry/) |
| Bulk Grade Entry | [Bulk Grade Entry](http://127.0.0.1:8000/grades/bulk-entry/) |
| My Report Card | [View My Report Card](http://127.0.0.1:8000/my-report-card/) |
| Report Card for a Specific Student | `/report-card/<student_id>/` |

### 📝 Homework

| Page | URL |
|---|---|
| Student Homework List | [View Homework](http://127.0.0.1:8000/homework/) |
| Create Homework | [Create Homework](http://127.0.0.1:8000/homework/create/) |
| Submit Homework | `/homework/<homework_id>/submit/` |
| View Homework Submissions | `/homework/<homework_id>/submissions/` |
| Review a Submission | `/homework/submission/<submission_id>/review/` |
| My Homework Results | [View Homework Results](http://127.0.0.1:8000/homework/results/) |
| Teacher Homework List | [My Homework Assignments](http://127.0.0.1:8000/teacher/homework/) |

### 💰 Fee Management

| Page | URL |
|---|---|
| Fee Records | [View Fee Records](http://127.0.0.1:8000/fees/) |
| Create Fee Record | [Create Fee Record](http://127.0.0.1:8000/fees/create/) |
| Edit Fee Record | `/fees/<fee_id>/edit/` |
| Delete Fee Record | `/fees/<fee_id>/delete/` |

**URL notes:**
- Replace `<student_id>`, `<homework_id>`, `<submission_id>`, and `<fee_id>` with actual record IDs.
- Protected pages require login and the appropriate role or permission.
- The monthly attendance report and fee management are restricted to administrators in the current implementation.
- The project URL configuration does not define a separate registration route.

---

## ✅ Testing and Verification

The following workflows were manually tested during development.

| Test | Observed Result | Status |
|---|---|---|
| Student Dashboard | Student-specific dashboard and links displayed | Passed |
| Teacher Dashboard | Teacher-specific dashboard and links displayed | Passed |
| Parent Dashboard | Parent dashboard displayed | Passed |
| Teacher Attendance Marking | Attendance marked successfully | Passed |
| Individual Grade Entry | Grade saved successfully | Passed |
| Homework Creation | Homework assigned successfully | Passed |
| Student Homework Results | Submission, marks, and feedback displayed | Passed |
| Parent Timetable | Child's timetable displayed | Passed |
| Parent Report Card | Own child's report card opens; another student's returns 404 | Passed |
| Admin Fee Records | Fee records and management options displayed | Passed |
| Unauthorized Grade Entry | Student/Parent access denied | Passed |
| Teacher Attendance Report Access | Administrator-only restriction applied | Passed |
| Teacher Fee Management Access | Administrator-only restriction applied | Passed |
| CSV Import Command | Command help and student import tested | Passed |
| PDF Report Card | Report card generated with marks and percentage | Passed |
| Django System Check | No system-check issues reported | Passed |
| Teacher Homework Filtering | Teachers see only their assigned homework | Passed |
| Duplicate Homework Submission | Duplicate submissions are prevented | Passed |
| Grade Validation | Invalid marks are rejected | Passed |

### Django System Check

Run:

```bash
python manage.py check
```

Verified output:

```text
System check identified no issues (0 silenced).
```

### Example PDF Report Card

A development report card was tested using sample records:

- Student: Bushra Inam
- Class: 9
- Computer: 76/100
- Mathematics: 91/100
- Total: 167/200
- Percentage: 83.50%

These values are sample development data and are not official academic results.

---

## 📥 CSV Student Import

The project includes a custom management command named `import_students` for importing student records from a CSV file.

### View Command Help

```bash
python manage.py help import_students
```

### Import Sample Students

```bash
python manage.py import_students data/students.csv
```

Use the exact argument format supported by the command implementation.

The import workflow was tested with sample student records. The command includes validation for missing required values, duplicate roll numbers, unknown class names, missing files, and empty CSV files.

The sample CSV contains the following columns:

```text
first_name,last_name,roll_number,email,school_class
```

Use only fictional or properly authorized data in sample files, especially when the repository is public.

---

## 📄 PDF Report Cards

The project uses **ReportLab** to generate student report cards.

The report card workflow includes:

- Student information.
- Recorded subject grades.
- Total marks.
- Percentage calculation.

Students can access their report card using the **My Report Card** option in their dashboard.

Ensure the student has the necessary grade records and that ReportLab is installed.

---


## 🔐 Groups and Permissions

Access control works in three layers:

1. **Group membership**: `Teacher`, `Student` and `Parent` groups decide which dashboard and pages a user can open.
2. **Permission checks**: teacher actions also require specific Django permissions (checked with `has_perm`).
3. **Ownership checks**: teachers only see their own classes and homework, students only see their own records, and parents only see their own children.

Superusers (administrators) bypass group checks and are the only users who can open fee records and the monthly attendance report.

### Teacher Group

Permissions required by the current views:

| Permission | Used for |
|------------|----------|
| `school.add_attendance` | Mark attendance |
| `school.add_grade` | Single and bulk grade entry |
| `school.change_grade` | Edit existing grades |
| `school.add_homework` | Create homework |
| `school.view_homework` | Teacher homework list |
| `school.view_homeworksubmission` | View student submissions |
| `school.change_homeworksubmission` | Review submissions and give marks |

A teacher account also needs a linked `Teacher` profile and at least one timetable entry (class assignment). Teachers can only select students and classes from their assigned timetable.

### Student Group

- Access is based on membership in the `Student` group and a linked `Student` profile.
- Students can view their own timetable, homework, homework results and report card.
- The `view_*` permissions assigned to this group are not checked by the current views.

### Parent Group

- Access is based on membership in the `Parent` group and a linked `Parent` profile.
- Parents can view the timetable of their children's classes and the report cards of their own children only (other children return 404).
- The `view_*` permissions assigned to this group are not checked by the current views.

### Administrator

- Superusers manage school records, users, groups and permissions through Django Admin.
- Only administrators can open fee records and the monthly attendance report.

### Configure Groups

1. Run `python manage.py setup_roles` to create the `Teacher`, `Student` and `Parent` groups and configure the required Teacher permissions.
2. Log in to Django Admin with a superuser account.
3. Add each user to the correct group.
4. Create the matching `Teacher`, `Student` or `Parent` profile and link it to the user.
5. For parents, add children in the `students` field of the Parent record.
6. Ensure each teacher has at least one timetable entry assigning their classes.

### Known Limitations

- Parents cannot yet view grades, homework or fee records (only timetable and report cards).
- Fee records are visible to administrators only.

## 🖥️ Django Admin

Open the local admin panel:

http://127.0.0.1:8000/admin/

The admin interface supports management of registered school models, including:

- Students and classes.
- Teachers and timetables.
- Attendance and grades.
- Homework and submissions.
- Fee records.
- User groups and permissions.

Student-related attendance and grade records can also be managed through admin inlines.

---

## 🔮 Future Improvements

Possible future enhancements include:

- Automated tests for models, views, forms, and permissions.
- More comprehensive student and parent profile management.
- Downloadable attendance reports.
- Email notifications for homework and fees.
- Improved calendar and reporting interfaces.
- Responsive UI enhancements.
- Production deployment with secure settings and environment-specific configuration.

---

## 👩‍💻 Development Notes

This project was developed as a practical Django learning assignment to strengthen Python backend development skills through real-world school management workflows.

It demonstrates database modeling, CRUD operations, authentication, authorization, form handling, class and timetable relationships, bulk grade entry, CSV processing, PDF generation, and Django Admin customization.

## 📜 License

This project is intended for educational and portfolio purposes. Add a suitable license file if you plan to distribute or reuse it publicly.
