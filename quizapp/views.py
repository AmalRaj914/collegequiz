from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
from django.db.models import Sum

import pandas as pd
import os

from .models import *

from .groq_utils import generate_ai_report


@login_required
@login_required
def faculty_dashboard(request):

    faculty = request.user.faculty

    # Total Students
    students = Student.objects.filter(
        department=faculty.department
    ).count()

    # Total Quizzes
    total_quizzes = Quiz.objects.filter(
        faculty=faculty
    ).count()

    # Quiz List
    quizzes = Quiz.objects.filter(
        faculty=faculty
    ).order_by("-created_date")

    # Total Results
    results = Result.objects.filter(
        quiz__faculty=faculty
    ).count()

    # Total Question Banks
    banks = QuestionBank.objects.filter(
        uploaded_by=faculty
    ).count()

    context = {

        "students": students,

        "quiz": total_quizzes,

        "quizzes": quizzes,

        "results": results,

        "banks": banks,

    }

    return render(
        request,
        "faculty_dashboard.html",
        context
    )

@login_required
def upload_students(request):

    faculty = request.user.faculty

    if request.method == "POST":

        excel = request.FILES.get("excel_file")

        if not excel:
            messages.error(request, "Please select an Excel file.")
            return redirect("upload_students")

        # Save uploaded file
        StudentExcel.objects.create(
            file=excel,
            uploaded_by=faculty
        )

        # Read Excel
        df = pd.read_excel(excel)

        department = faculty.department

        # Change this if you don't have a Section column
        default_section = "A"

        for index, row in df.iterrows():

            roll_no = str(row["Roll No"]).strip().upper()
            student_name = str(row["Name"]).strip()

            # -----------------------------
            # Find Year from Roll Number
            # -----------------------------
            if roll_no.startswith("B24"):
                batch_year = 3

            elif roll_no.startswith("B25"):
                batch_year = 2

            elif roll_no.startswith("B26"):
                batch_year = 1

            else:
                batch_year = 1

            # -----------------------------
            # Section
            # -----------------------------
            if "Section" in df.columns:
                section = str(row["Section"]).strip()
            else:
                section = default_section

            # -----------------------------
            # Create Login
            # -----------------------------
            user, created = User.objects.get_or_create(
                username=roll_no
            )

            if created:
                user.set_password(roll_no)
                user.save()

            # -----------------------------
            # Save Student
            # -----------------------------
            Student.objects.update_or_create(

                roll_no=roll_no,

                defaults={

                    "user": user,

                    "student_name": student_name,

                    "department": department,

                    "batch_year": batch_year,

                    "section": section,

                }

            )

        messages.success(
            request,
            "Student List Uploaded Successfully."
        )

        return redirect("upload_students")

    uploads = StudentExcel.objects.filter(
        uploaded_by=faculty
    ).order_by("-uploaded_date")

    return render(
        request,
        "upload_students.html",
        {
            "uploads": uploads
        }
    )


@login_required

def student_dashboard(request):

    student = request.user.student

    quizzes = Quiz.objects.filter(
        department=student.department,
        year=student.batch_year,
        status=True
    )

    quiz_list = []

    available = 0
    completed = 0
    pending = 0

    total_percentage = 0

    results = Result.objects.filter(
        student=student
    )

    for quiz in quizzes:

        attempted = Result.objects.filter(
            student=student,
            quiz=quiz
        ).exists()

        if attempted:

            completed += 1

        else:

            available += 1
            pending += 1

        quiz_list.append({

            "quiz": quiz,

            "attempted": attempted

        })

    if results.exists():

        total_percentage = round(

            sum(r.percentage for r in results) / results.count(),

            2

        )

    context = {

        "student": student,

        "quiz_list": quiz_list,

        "available": available,

        "completed": completed,

        "pending": pending,

        "average": total_percentage

    }

    return render(

        request,

        "student_dashboard.html",

        context

    )

@login_required
def upload_question_bank(request):

    faculty = request.user.faculty

    quizzes = Quiz.objects.filter(
        faculty=faculty
    )

    if request.method == "POST":

        quiz_id = request.POST.get("quiz")

        quiz = get_object_or_404(
            Quiz,
            id=quiz_id,
            faculty=faculty
        )

        excel = request.FILES.get("question_file")

        # Save uploaded question bank file
        QuestionBank.objects.create(

            quiz=quiz,

            uploaded_by=faculty,

            file=excel,

            file_type="excel",

            status="Uploaded"

        )

        # Read Excel
        df = pd.read_excel(excel)

        total = 0

        # Insert Questions
        for _, row in df.iterrows():

            Question.objects.create(

                quiz=quiz,

                question=str(row["Question"]).strip(),

                option1=str(row["Option A"]).strip(),

                option2=str(row["Option B"]).strip(),

                option3=str(row["Option C"]).strip(),

                option4=str(row["Option D"]).strip(),

                correct_answer=str(row["Correct Answer"]).strip(),

                marks=1,

                unit=1,

                question_level="Easy"

            )

            total += 1

        # Update total questions
        QuestionBank.objects.filter(
            quiz=quiz
        ).update(
            total_questions=total
        )

        messages.success(
            request,
            f"{total} Questions Uploaded Successfully."
        )

        return redirect("upload_question_bank")

    banks = QuestionBank.objects.filter(
        uploaded_by=faculty
    ).order_by("-uploaded_date")

    return render(

        request,

        "upload_question_bank.html",

        {

            "quizzes": quizzes,

            "banks": banks

        }

    )
@login_required
def create_quiz(request):

    faculty = request.user.faculty

    if request.method == "POST":

        Quiz.objects.create(

            faculty=faculty,

            title=request.POST.get("title"),

            subject_code=request.POST.get("subject_code"),

            subject_name=request.POST.get("subject_name"),

            department=faculty.department,

            year=request.POST.get("year"),

            section=request.POST.get("section"),

            duration=request.POST.get("duration"),

            total_questions=request.POST.get("total_questions")

        )

        messages.success(

            request,

            "Quiz Created Successfully."

        )

        return redirect("create_quiz")

    quizzes = Quiz.objects.filter(
        faculty=faculty
    ).order_by("-created_date")

    return render(

        request,

        "create_quiz.html",

        {

            "quizzes": quizzes

        }

    )

@login_required
def publish_quiz(request):

    faculty = request.user.faculty

    quizzes = Quiz.objects.filter(
        faculty=faculty
    ).order_by("-created_date")

    return render(

        request,

        "publish_quiz.html",

        {

            "quizzes": quizzes

        }

    )

@login_required
def publish(request, quiz_id):

    faculty = request.user.faculty

    quiz = get_object_or_404(

        Quiz,

        id=quiz_id,

        faculty=faculty

    )

    quiz.status = True

    quiz.save()

    messages.success(

        request,

        "Quiz Published Successfully."

    )

    return redirect("publish_quiz")

@login_required
def participant_list(request):

    faculty = request.user.faculty

    quizzes = Quiz.objects.filter(
        faculty=faculty
    )

    return render(

        request,

        "participant_list.html",

        {

            "quizzes": quizzes

        }

    )

@login_required
def result_list(request):

    faculty = request.user.faculty

    quizzes = Quiz.objects.filter(
        faculty=faculty
    )

    results = Result.objects.filter(

        quiz__faculty=faculty

    ).select_related(

        "student",

        "quiz"

    )

    return render(

        request,

        "result_list.html",

        {

            "results": results,

            "quizzes": quizzes

        }

    )



@login_required
def quiz_page(request, quiz_id):

    student = request.user.student

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        status=True
    )

    # Prevent multiple attempts
    if Result.objects.filter(student=student, quiz=quiz).exists():
        messages.error(
            request,
            "You have already attended this quiz."
        )
        return redirect("student_dashboard")

    # Record attendance
    Attendance.objects.get_or_create(
        student=student,
        quiz=quiz
    )

    questions = Question.objects.filter(
        quiz=quiz
    ).order_by("?")[:quiz.total_questions]

    context = {
        "quiz": quiz,
        "questions": questions
    }

    return render(
        request,
        "quiz_page.html",
        context
    )


@login_required
def submit_quiz(request, quiz_id):

    if request.method != "POST":
        return redirect("student_dashboard")

    student = request.user.student

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    # Prevent multiple submissions
    if Result.objects.filter(
        student=student,
        quiz=quiz
    ).exists():

        messages.warning(
            request,
            "You have already submitted this quiz."
        )

        return redirect("student_dashboard")

    questions = Question.objects.filter(
        quiz=quiz
    )

    score = 0

    total_marks = questions.aggregate(
        total=Sum("marks")
    )["total"] or 0

    # Check Answers
    for question in questions:

        selected_answer = request.POST.get(
            f"question_{question.id}"
        )

        if selected_answer:

            selected_answer = selected_answer.strip().upper()

            correct_answer = question.correct_answer.strip().upper()

            if selected_answer == correct_answer:

                score += question.marks

    # Calculate Percentage
    if total_marks > 0:

        percentage = round(
            (score / total_marks) * 100,
            2
        )

    else:

        percentage = 0

    # Save Result
    Result.objects.create(

        student=student,

        quiz=quiz,

        score=score,

        percentage=percentage

    )

    # Update Attendance
    Attendance.objects.filter(

        student=student,

        quiz=quiz

    ).update(

        completed=True,

        logout_time=timezone.now()

    )

    # Update Student
    student.is_attempted = True
    student.save()

    messages.success(
        request,
        f"Quiz Submitted Successfully.\nScore : {score}/{total_marks}"
    )

    return redirect(
        "student_result",
        quiz.id
    )
@login_required
def student_result(request, quiz_id):

    student = request.user.student

    result = get_object_or_404(

        Result,

        student=student,

        quiz_id=quiz_id

    )

    quiz = result.quiz

    total_marks = Question.objects.filter(

        quiz=quiz

    ).aggregate(

        total=Sum("marks")

    )["total"]

    context = {

        "quiz": quiz,

        "result": result,

        "total_marks": total_marks

    }

    return render(

        request,

        "student_result.html",

        context

    )


@login_required
def upload_activity_photo(request, quiz_id):

    faculty = request.user.faculty

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        faculty=faculty
    )

    if request.method == "POST":

        ActivityPhoto.objects.create(

            quiz=quiz,

            title=request.POST.get("title"),

            photo=request.FILES.get("photo"),

            latitude=request.POST.get("latitude"),

            longitude=request.POST.get("longitude"),

            address=request.POST.get("address")

        )

        messages.success(
            request,
            "Activity Photo Uploaded Successfully."
        )

        return redirect(
            "upload_activity_photo",
            quiz.id
        )

    photos = ActivityPhoto.objects.filter(
        quiz=quiz
    ).order_by("-uploaded_date")

    return render(
        request,
        "upload_activity_photo.html",
        {
            "quiz": quiz,
            "photos": photos
        }
    )

@login_required
def generate_report(request):

    faculty = request.user.faculty

    if request.method == "POST":

        quiz_id = request.POST.get("quiz_id")

        quiz = get_object_or_404(
            Quiz,
            id=quiz_id,
            faculty=faculty
        )

        college = CollegeInfo.objects.first()

        total_students = Student.objects.filter(
            department=quiz.department,
            section=quiz.section
        ).count()

        results = Result.objects.filter(
            quiz=quiz
        )

        attended = results.count()

        highest = results.aggregate(
            Max("score")
        )["score__max"] or 0

        lowest = results.aggregate(
            Min("score")
        )["score__min"] or 0

        average = results.aggregate(
            Avg("score")
        )["score__avg"] or 0

        pass_count = results.filter(
            percentage__gte=50
        ).count()

        fail_count = attended - pass_count

        pass_percentage = (
            (pass_count / attended) * 100
            if attended else 0
        )

        fail_percentage = (
            (fail_count / attended) * 100
            if attended else 0
        )

        participants = Result.objects.filter(
            quiz=quiz
        ).select_related("student").order_by("student__roll_no")

        photos = ActivityPhoto.objects.filter(
            quiz=quiz
        ).order_by("uploaded_date")

        photo1 = photos[0] if photos.count() > 0 else None
        photo2 = photos[1] if photos.count() > 1 else None

        prompt = f"""
Generate a professional college quiz activity report.

College:
{college.college_name}

Department:
{college.department_name}

Faculty:
{college.faculty_name}

Subject:
{quiz.subject_name}

Quiz:
{quiz.title}

Students:
{total_students}

Attended:
{attended}

Highest:
{highest}

Lowest:
{lowest}

Average:
{round(average,2)}

Pass Percentage:
{round(pass_percentage,2)}

Fail Percentage:
{round(fail_percentage,2)}

Write under these headings:

1. Objective

2. Introduction

3. Performance Analysis

4. Learning Outcome

5. Suggestions

6. Conclusion
"""

        ai_report = generate_ai_report(prompt)

        ActivityReport.objects.update_or_create(

            quiz=quiz,

            defaults={

                "objective":"AI Generated",

                "summary":"Quiz Analysis",

                "outcome":"Completed",

                "ai_report":ai_report,

                "photo1":photo1.photo if photo1 else None,

                "photo2":photo2.photo if photo2 else None

            }

        )

        context = {

            "college":college,

            "quiz":quiz,

            "participants":participants,

            "photo1":photo1,

            "photo2":photo2,

            "total_students":total_students,

            "attended":attended,

            "highest":highest,

            "lowest":lowest,

            "average":round(average,2),

            "pass_percentage":round(pass_percentage,2),

            "fail_percentage":round(fail_percentage,2),

            "ai_report":ai_report

        }

        return render(
            request,
            "report_preview.html",
            context
        )

    quizzes = Quiz.objects.filter(
        faculty=faculty
    )

    return render(
        request,
        "generate_report.html",
        {
            "quizzes":quizzes
        }
    )

@login_required
def student_result(request, quiz_id):

    student = request.user.student

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    result = get_object_or_404(

        Result,

        student=student,

        quiz=quiz

    )

    total_questions = Question.objects.filter(
        quiz=quiz
    ).count()

    correct_answers = result.score

    wrong_answers = total_questions - correct_answers

    context = {

        "student": student,

        "quiz": quiz,

        "result": result,

        "total_questions": total_questions,

        "correct_answers": correct_answers,

        "wrong_answers": wrong_answers

    }

    return render(

        request,

        "student_result.html",

        context

    )

from django.db.models import Avg, Max

@login_required
def result_list(request):

    faculty = request.user.faculty

    results = Result.objects.filter(
        quiz__faculty=faculty
    ).select_related(
        "student",
        "quiz"
    ).order_by(
        "-percentage"
    )

    search = request.GET.get("search")

    if search:

        results = results.filter(
            student__roll_no__icontains=search
        )

    total_students = results.count()

    highest = results.aggregate(
        Max("score")
    )["score__max"] or 0

    average = results.aggregate(
        Avg("percentage")
    )["percentage__avg"] or 0

    context = {

        "results": results,

        "total_students": total_students,

        "highest": highest,

        "average": round(average,2)

    }

    return render(

        request,

        "result_list.html",

        context

    )

from .groq_utils import generate_ai_report
@login_required
def generate_report(request):

    faculty = request.user.faculty

    quiz_id = request.GET.get("quiz")

    if not quiz_id:

        return render(
            request,
            "generated_report.html",
            {
                "error": "No Quiz Selected."
            }
        )

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        faculty=faculty
    )

    # -----------------------------
    # Quiz Results
    # -----------------------------

    results = Result.objects.filter(
        quiz=quiz
    ).select_related("student")

    total_students = results.count()

    highest_score = results.aggregate(
        Max("score")
    )["score__max"] or 0

    lowest_score = results.aggregate(
        Min("score")
    )["score__min"] or 0

    average_score = results.aggregate(
        Avg("score")
    )["score__avg"] or 0

    average_percentage = results.aggregate(
        Avg("percentage")
    )["percentage__avg"] or 0

    passed = results.filter(
        percentage__gte=50
    ).count()

    failed = total_students - passed

    pass_percentage = 0
    fail_percentage = 0

    if total_students > 0:

        pass_percentage = round(
            (passed / total_students) * 100,
            2
        )

        fail_percentage = round(
            (failed / total_students) * 100,
            2
        )

    # -----------------------------
    # Attendance Details
    # -----------------------------

    registered_students = Student.objects.filter(
        department=quiz.department,
        batch_year=quiz.year,
        section=quiz.section
    ).count()

    absent_students = registered_students - total_students

    attendance_percentage = 0

    if registered_students > 0:

        attendance_percentage = round(
            (total_students / registered_students) * 100,
            2
        )

    # -----------------------------
    # College Information
    # -----------------------------

    college = CollegeInfo.objects.first()

    # -----------------------------
    # Activity Photos
    # -----------------------------

    photos = ActivityPhoto.objects.filter(
        quiz=quiz
    )

    # -----------------------------
    # Participant Details
    # -----------------------------

    participant_text = ""

    for i, result in enumerate(results, start=1):

        participant_text += (
            f"{i}. "
            f"{result.student.roll_no} - "
            f"{result.student.student_name} - "
            f"Score {result.score} - "
            f"{result.percentage}%\n"
        )

    # -----------------------------
    # AI Prompt
    # -----------------------------

    prompt = f"""
You are an experienced NAAC/NBA documentation expert.

Write a PROFESSIONAL College Quiz Activity Report.

Do NOT use Markdown.

Do NOT use stars (*).

Do NOT use bold symbols.

Write in proper paragraphs.

The report should be suitable for IQAC, NAAC and NBA documentation.

College Name:
{college.college_name if college else ""}

Department:
{quiz.department.department_name}

Quiz Title:
{quiz.title}

Subject Code:
{quiz.subject_code}

Subject Name:
{quiz.subject_name}

Year:
{quiz.year}

Section:
{quiz.section}

Faculty Coordinator:
{faculty.faculty_name}

Designation:
{faculty.designation}

Total Registered Students:
{registered_students}

Students Participated:
{total_students}

Students Absent:
{absent_students}

Attendance Percentage:
{attendance_percentage:.2f}

Highest Score:
{highest_score}

Lowest Score:
{lowest_score}

Average Score:
{average_score:.2f}

Average Percentage:
{average_percentage:.2f}

Pass Percentage:
{pass_percentage:.2f}

Fail Percentage:
{fail_percentage:.2f}

Participants

{participant_text}

Generate the report using these headings only.

Objective

Introduction

Quiz Conduct

Student Participation

Performance Analysis

Learning Outcome

Conclusion

Recommendations

Use the participant information.

Never write Student-1, Student-2 etc.

Never use placeholders.

Write professionally.
"""

    # -----------------------------
    # Generate AI Report
    # -----------------------------

    report = generate_ai_report(prompt)

    # -----------------------------
    # Save Report
    # -----------------------------

    activity, created = ActivityReport.objects.get_or_create(
        quiz=quiz
    )

    activity.ai_report = report
    activity.save()

    # -----------------------------
    # Render
    # -----------------------------

    return render(

        request,

        "generated_report.html",

        {

            "college": college,

            "quiz": quiz,

            "faculty": faculty,

            "participants": results,

            "photos": photos,

            "report": report,

            "total_students": total_students,

            "registered_students": registered_students,

            "absent_students": absent_students,

            "attendance_percentage": attendance_percentage,

            "highest_score": highest_score,

            "lowest_score": lowest_score,

            "average_score": round(average_score, 2),

            "average_percentage": round(average_percentage, 2),

            "passed": passed,

            "failed": failed,

            "pass_percentage": pass_percentage,

            "fail_percentage": fail_percentage,

        }

    )

from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.shortcuts import render, redirect

def login_view(request):

    if request.method == "POST":

        username = request.POST.get("username").strip()

        password = request.POST.get("password").strip()

        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user is not None:

            login(request, user)

            # Faculty Login
            if hasattr(user, "faculty"):

                return redirect("faculty_dashboard")

            # Student Login
            elif hasattr(user, "student"):

                return redirect("student_dashboard")

            else:

                logout(request)

                messages.error(
                    request,
                    "User account is not assigned to Faculty or Student."
                )

        else:

            messages.error(
                request,
                "Invalid Username or Password."
            )

    return render(
        request,
        "login.html"
    )

def logout_view(request):

    logout(request)

    return redirect("login")
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch

@login_required
def download_pdf_report(request, quiz_id):

    faculty = request.user.faculty

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id,
        faculty=faculty
    )

    report = ActivityReport.objects.get(
        quiz=quiz
    )

    participants = Result.objects.filter(
        quiz=quiz
    ).select_related("student")

    photos = ActivityPhoto.objects.filter(
        quiz=quiz
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{quiz.title}_Report.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30
    )

    styles = getSampleStyleSheet()

    story = []

    # ----------------------------------------------------
    # TITLE
    # ----------------------------------------------------

    story.append(
        Paragraph(
            "<b><font size=18>COLLEGE QUIZ ACTIVITY REPORT</font></b>",
            styles["Title"]
        )
    )

    story.append(Spacer(1, 20))

    # ----------------------------------------------------
    # QUIZ DETAILS
    # ----------------------------------------------------

    details = [

        ["Department", quiz.department.department_name],

        ["Quiz Title", quiz.title],

        ["Subject Code", quiz.subject_code],

        ["Subject Name", quiz.subject_name],

        ["Year", quiz.year],

        ["Section", quiz.section],

        ["Faculty Coordinator", faculty.faculty_name],

    ]

    detail_table = Table(
        details,
        colWidths=[150, 320]
    )

    detail_table.setStyle(

        TableStyle([

            ("GRID",(0,0),(-1,-1),0.5,colors.grey),

            ("BACKGROUND",(0,0),(0,-1),colors.lightblue),

            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),

            ("BOTTOMPADDING",(0,0),(-1,-1),8),

        ])

    )

    story.append(detail_table)

    story.append(Spacer(1,20))

    # ----------------------------------------------------
    # AI REPORT
    # ----------------------------------------------------

    story.append(

        Paragraph(
            "<b>AI Generated Activity Report</b>",
            styles["Heading2"]
        )

    )

    story.append(Spacer(1,10))

    story.append(

        Paragraph(
            report.ai_report.replace("\n","<br/>"),
            styles["BodyText"]
        )

    )

    story.append(Spacer(1,25))

    # ----------------------------------------------------
    # PARTICIPANT LIST
    # ----------------------------------------------------

    story.append(

        Paragraph(
            "<b>Participant List</b>",
            styles["Heading2"]
        )

    )

    story.append(Spacer(1,10))

    data = [[

        "Sl.No",

        "Roll No",

        "Student Name",

        "Score",

        "Percentage",

        "Signature"

    ]]

    for i, p in enumerate(participants, start=1):

        data.append([

            str(i),

            p.student.roll_no,

            p.student.student_name,

            str(p.score),

            f"{p.percentage}%",

            ""

        ])

    participant_table = Table(

        data,

        colWidths=[40,70,170,55,70,120]

    )

    participant_table.setStyle(

        TableStyle([

            ("BACKGROUND",(0,0),(-1,0),colors.darkblue),

            ("TEXTCOLOR",(0,0),(-1,0),colors.white),

            ("GRID",(0,0),(-1,-1),1,colors.black),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("VALIGN",(0,0),(-1,-1),"MIDDLE"),

            ("BOTTOMPADDING",(0,0),(-1,0),10),

        ])

    )

    story.append(participant_table)

    story.append(Spacer(1,25))

    # ----------------------------------------------------
    # GEO TAGGED PHOTOS
    # ----------------------------------------------------

    # ----------------------------------------------------
# GEO TAGGED PHOTOS
# ----------------------------------------------------

    if photos.exists():

        story.append(
        Paragraph(
            "<b>Geo Tagged Activity Photos</b>",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 15))

    for photo in photos:

        # Display Photo
        try:

            img = Image(
                photo.photo.path,
                width=5 * inch,
                height=3.5 * inch
            )

            story.append(img)

        except Exception:
            pass

        story.append(Spacer(1, 8))

        # Photo Title
        story.append(
            Paragraph(
                    f"<b>Photo Title :</b> {photo.title}",
                styles["Normal"]
            )
        )

        # Address
        if photo.address:

            story.append(
                Paragraph(
                    f"<b>Address :</b> {photo.address}",
                    styles["Normal"]
                )
            )

        # Latitude
        if photo.latitude:

            story.append(
                Paragraph(
                    f"<b>Latitude :</b> {photo.latitude}",
                    styles["Normal"]
                )
            )

        # Longitude
        if photo.longitude:

            story.append(
                Paragraph(
                    f"<b>Longitude :</b> {photo.longitude}",
                    styles["Normal"]
                )
            )

        # Uploaded Date
        story.append(
            Paragraph(
                f"<b>Uploaded Date :</b> {photo.uploaded_date.strftime('%d-%m-%Y %I:%M %p')}",
                styles["Normal"]
            )
        )

        # Google Maps
        if photo.latitude and photo.longitude:

            story.append(
                Paragraph(
                    f"<b>Google Maps :</b> https://maps.google.com/?q={photo.latitude},{photo.longitude}",
                    styles["Normal"]
                )
            )

        story.append(Spacer(1, 25))

    # ----------------------------------------------------
    # SIGNATURES
    # ----------------------------------------------------

    story.append(Spacer(1,30))

    signature = Table(

        [[

            "Faculty Signature",

            "HOD Signature",

            "Principal Signature"

        ]],

        colWidths=[170,170,170]

    )

    signature.setStyle(

        TableStyle([

            ("LINEABOVE",(0,0),(-1,0),1,colors.black),

            ("TOPPADDING",(0,0),(-1,-1),18),

            ("ALIGN",(0,0),(-1,-1),"CENTER"),

            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold")

        ])

    )

    story.append(signature)

    doc.build(story)

    return response