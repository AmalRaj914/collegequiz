from aiohttp import request
from annotated_types import doc
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image
)

from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors


import os


from .models import (
    Student,
    Question,
    Result,
    Quiz,
    ActivityPhoto
)


from .services.ollama_service import generate_ict_report





# =====================================
# Student Login
# =====================================

def student_login(request):

    if request.method == "POST":

        student = Student.objects.create(
            reg_no=request.POST['reg_no'],
            student_name=request.POST['student_name']
        )

        request.session['student_id'] = student.id

        # Save selected quiz
        request.session['quiz_id'] = request.POST['quiz_id']

        return redirect('quiz_page')

    quizzes = Quiz.objects.all()

    return render(
        request,
        'student_login.html',
        {
            'quizzes': quizzes
        }
    )


# =====================================
# Quiz
# =====================================

def quiz_page(request):

    quiz_id = request.session.get('quiz_id')

    if not quiz_id:
        return redirect('student_login')

    quiz = Quiz.objects.get(
        id=quiz_id
    )

    questions = Question.objects.filter(
        quiz=quiz
    )

    if request.method == "POST":

        score = 0

        for q in questions:

            answer = request.POST.get(
                f"question_{q.id}"
            )

            if answer == q.correct_answer:
                score += 1

        total = questions.count()

        percentage = (
            (score / total) * 100
            if total > 0
            else 0
        )

        student = Student.objects.get(
            id=request.session['student_id']
        )

        Result.objects.create(
            student=student,
            quiz=quiz,
            score=score,
            percentage=percentage
        )

        return render(
            request,
            "result.html",
            {
                "score": score,
                "total": total,
                "percentage": percentage,
                "quiz": quiz
            }
        )

    return render(
        request,
        "quiz_page.html",
        {
            "questions": questions,
            "quiz": quiz
        }
    )



# =====================================
# Report Preview
# =====================================


def report_preview(request, quiz_id):


    quiz = get_object_or_404(

        Quiz,

        id=quiz_id

    )


    college = quiz.college



    results = Result.objects.filter(

        quiz=quiz

    )



    photos = ActivityPhoto.objects.all()



    total = results.count()



    highest = (

        results.order_by('-score')
        .first()
        .score

        if total

        else 0

    )



    average = (

        sum(
            r.score for r in results
        )
        /
        total

        if total

        else 0

    )




    if quiz.ai_report:


        ai_report = quiz.ai_report



    else:


        prompt = f"""

Generate ICT Activity Report


College:
{college.college_name}


Department:
{college.department_name}


Quiz:
{quiz.title}


Subject:
{quiz.subject_name}


Class:
{quiz.class_name}


Participants:
{total}


Highest Score:
{highest}


Average:
{average}


Generate:

Objective

Summary

Outcome

"""


        ai_report = generate_ict_report(prompt)


        quiz.ai_report = ai_report


        quiz.save()



    context={


        "college":college,

        "quiz":quiz,

        "results":results,

        "photos":photos,

        "ai_report":ai_report,

        "total_participants":total,

        "highest_score":highest,

        "average_score":average


    }



    return render(

        request,

        "report_preview.html",

        context

    )







from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)

from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from datetime import date

# =====================================
# ICT REPORT PDF WITH PHOTOS
# =====================================

from django.shortcuts import get_object_or_404
from django.http import HttpResponse

from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    PageBreak
)

from reportlab.lib import colors
from reportlab.lib.styles import (
    getSampleStyleSheet,
    ParagraphStyle
)

from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from datetime import date

from .models import Quiz, Result, ActivityPhoto


def report_pdf(request, quiz_id):

    quiz = get_object_or_404(
        Quiz,
        id=quiz_id
    )

    college = quiz.college

    results = Result.objects.filter(
        quiz=quiz
    )

    photos = ActivityPhoto.objects.all()

    total_participants = results.count()

    highest_score = max(
        [r.score for r in results],
        default=0
    )

    average_score = round(
        sum(r.score for r in results) / total_participants,
        2
    ) if total_participants else 0

    response = HttpResponse(
        content_type='application/pdf'
    )

    response[
        'Content-Disposition'
    ] = (
        f'attachment; filename="{quiz.title}_ICT_Report.pdf"'
    )

    doc = SimpleDocTemplate(
        response,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        spaceAfter=10
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceAfter=8
    )

    normal_style = styles["BodyText"]

    elements = []

    # ==================================
    # COLLEGE HEADER
    # ==================================

    elements.append(
        Paragraph(
            college.college_name.upper(),
            title_style
        )
    )

    elements.append(
        Paragraph(
            college.department_name.upper(),
            title_style
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    elements.append(
        Paragraph(
            "ICT ACTIVITY REPORT",
            title_style
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ==================================
    # ACTIVITY DETAILS
    # ==================================

    elements.append(
        Paragraph(
            "1. Activity Details",
            heading_style
        )
    )

    details = [

        ["Quiz Title", quiz.title],

        ["Subject", quiz.subject_name],

        ["Class", quiz.class_name],

        ["Faculty In Charge", college.faculty_name],

        ["Academic Year", college.academic_year],

        ["Report Date", str(date.today())],

        ["Total Participants", str(total_participants)]

    ]

    detail_table = Table(
        details,
        colWidths=[180, 300]
    )

    detail_table.setStyle(
        TableStyle([

            ("GRID", (0, 0), (-1, -1), 1,
             colors.black),

            ("BACKGROUND",
             (0, 0),
             (0, -1),
             colors.lightgrey),

            ("FONTNAME",
             (0, 0),
             (0, -1),
             "Helvetica-Bold"),

            ("VALIGN",
             (0, 0),
             (-1, -1),
             "MIDDLE")

        ])
    )

    elements.append(detail_table)

    elements.append(
        Spacer(1, 20)
    )

    # ==================================
    # AI REPORT
    # ==================================

    elements.append(
        Paragraph(
            "2. Objective / Summary / Outcome",
            heading_style
        )
    )

    ai_report = (
        quiz.ai_report
        if quiz.ai_report
        else "No report generated."
    )

    elements.append(
        Paragraph(
            ai_report.replace(
                "\n",
                "<br/>"
            ),
            normal_style
        )
    )

    elements.append(
        Spacer(1, 20)
    )

    # ==================================
    # STATISTICS
    # ==================================

    elements.append(
        Paragraph(
            "3. Participation Statistics",
            heading_style
        )
    )

    stats = [

        ["Total Participants",
         total_participants],

        ["Highest Score",
         highest_score],

        ["Average Score",
         average_score]

    ]

    stats_table = Table(
        stats,
        colWidths=[220, 150]
    )

    stats_table.setStyle(
        TableStyle([

            ("GRID",
             (0, 0),
             (-1, -1),
             1,
             colors.black),

            ("BACKGROUND",
             (0, 0),
             (0, -1),
             colors.lightgrey),

            ("FONTNAME",
             (0, 0),
             (0, -1),
             "Helvetica-Bold")

        ])
    )

    elements.append(stats_table)

    elements.append(
        Spacer(1, 20)
    )

    # ==================================
    # ATTENDANCE SHEET
    # ==================================

    elements.append(
        Paragraph(
            "4. Attendance Sheet",
            heading_style
        )
    )

    attendance_data = [[

        "S.No",

        "Register No",

        "Student Name",

        "Score",

        "Signature"

    ]]

    for i, r in enumerate(
            results,
            start=1):

        attendance_data.append([

            i,

            r.student.reg_no,

            r.student.student_name,

            r.score,

            ""

        ])

    attendance_table = Table(
        attendance_data,
        colWidths=[40, 90, 180, 50, 120],
        repeatRows=1
    )

    attendance_table.setStyle(
        TableStyle([

            ("GRID",
             (0, 0),
             (-1, -1),
             1,
             colors.black),

            ("BACKGROUND",
             (0, 0),
             (-1, 0),
             colors.lightgrey),

            ("FONTNAME",
             (0, 0),
             (-1, 0),
             "Helvetica-Bold"),

            ("ALIGN",
             (0, 0),
             (-1, -1),
             "CENTER"),

            ("VALIGN",
             (0, 0),
             (-1, -1),
             "MIDDLE")

        ])
    )

    elements.append(
        attendance_table
    )

    elements.append(
        PageBreak()
    )

    # ==================================
    # PHOTOS
    # ==================================

    elements.append(
        Paragraph(
            "5. Activity Photographs",
            heading_style
        )
    )

    elements.append(
        Spacer(1, 10)
    )

    photo_rows = []
    row = []

    for photo in photos:

        if photo.photo:

            img = Image(
                photo.photo.path,
                width=220,
                height=160
            )

            row.append(img)

            if len(row) == 2:
                photo_rows.append(row)
                row = []

    if row:
        photo_rows.append(row)

    if photo_rows:

        photo_table = Table(
            photo_rows,
            colWidths=[250, 250]
        )

        photo_table.setStyle(
            TableStyle([

                ("ALIGN",
                 (0, 0),
                 (-1, -1),
                 "CENTER")

            ])
        )

        elements.append(
            photo_table
        )

    elements.append(
        Spacer(1, 40)
    )

    # ==================================
    # SIGNATURES
    # ==================================

    sign_table = Table(

        [

            [
                "Faculty Coordinator",
                "HOD",
                "Principal"
            ],

            [
                college.faculty_name,
                college.hod_name,
                college.principal_name
            ]

        ],

        colWidths=[160, 160, 160]

    )

    sign_table.setStyle(
        TableStyle([

            ("ALIGN",
             (0, 0),
             (-1, -1),
             "CENTER"),

            ("TOPPADDING",
             (0, 1),
             (-1, 1),
             25)

        ])
    )

    elements.append(
        sign_table
    )

    doc.build(elements)

    return response
# =====================================
# Photo Gallery
# =====================================


def photo_gallery(request):


    photos = ActivityPhoto.objects.all()



    return render(

        request,

        "photo_gallery.html",

        {

        "photos":photos

        }

    )







# =====================================
# Participant PDF
# =====================================


def participant_pdf(request):


    response = HttpResponse(

        content_type="application/pdf"

    )


    response['Content-Disposition'] = (

        'attachment; filename="participants.pdf"'

    )



    doc = SimpleDocTemplate(response)



    data=[


        [

        "Sl No",

        "Register No",

        "Name",

        "Signature"

        ]

    ]



    results = Result.objects.all()




    for i,r in enumerate(results,1):


        data.append(

            [

            i,

            r.student.reg_no,

            r.student.student_name,

            ""

            ]

        )





    table = Table(data)



    table.setStyle(

        TableStyle([

        (

        "GRID",

        (0,0),

        (-1,-1),

        1,

        colors.black

        )

        ])

    )



    doc.build(

        [table]

    )



    return response


# =====================================
# Result List
# =====================================

def result_list(request):

    results = Result.objects.all()


    return render(

        request,

        "result_list.html",

        {
            "results": results
        }

    )





# =====================================
# Participant List
# =====================================

def participant_list(request):

    results = Result.objects.all()


    return render(

        request,

        "participant_list.html",

        {
            "results": results
        }

    )






# =====================================
# Dashboard
# =====================================

def dashboard(request):


    return render(

        request,

        "dashboard.html"

    )
from docx import Document
from django.shortcuts import render
from django.http import HttpResponse
import re

from docx import Document
from django.shortcuts import render
from django.http import HttpResponse
import re

from .models import Quiz, Question, QuestionBank


def upload_question_bank(request):

    quizzes = Quiz.objects.all()

    if request.method == "POST":

        try:

            quiz_id = request.POST.get("quiz")
            file = request.FILES.get("file")

            if not quiz_id:
                return HttpResponse("Please select a quiz")

            if not file:
                return HttpResponse("Please choose a Word file")

            quiz = Quiz.objects.get(id=quiz_id)

            QuestionBank.objects.create(
                quiz=quiz,
                file=file
            )

            doc = Document(file)

            lines = []

            for para in doc.paragraphs:
                text = para.text.strip()

                if text:
                    lines.append(text)

            print("TOTAL LINES =", len(lines))

            saved_count = 0
            i = 0

            while i < len(lines):

                line = lines[i].strip()

                if re.match(r'^\d+\.', line):

                    question = line

                    option1 = ""
                    option2 = ""
                    option3 = ""
                    option4 = ""
                    answer = ""

                    if i + 1 < len(lines):
                        option1 = lines[i + 1].replace("A)", "").replace("", "").strip()

                    if i + 2 < len(lines):
                        option2 = lines[i + 2].replace("B)", "").replace("", "").strip()

                    if i + 3 < len(lines):
                        option3 = lines[i + 3].replace("C)", "").replace("", "").strip()

                    if i + 4 < len(lines):
                        option4 = lines[i + 4].replace("D)", "").replace("", "").strip()

                    if i + 5 < len(lines):

                        answer_line = lines[i + 5]

                        if "Answer:" in answer_line:

                            answer_letter = answer_line.split(":")[1].strip().upper()

                            if answer_letter == "A":
                                answer = option1

                            elif answer_letter == "B":
                                answer = option2

                            elif answer_letter == "C":
                                answer = option3

                            elif answer_letter == "D":
                                answer = option4

                    print("QUESTION =", question)
                    print("OPTION1 =", option1)
                    print("OPTION2 =", option2)
                    print("OPTION3 =", option3)
                    print("OPTION4 =", option4)
                    print("ANSWER =", answer)

                    Question.objects.create(
                        quiz=quiz,
                        question=question,
                        option1=option1,
                        option2=option2,
                        option3=option3,
                        option4=option4,
                        correct_answer=answer
                    )

                    saved_count += 1

                    i += 6

                else:
                    i += 1

            print("TOTAL SAVED =", saved_count)

            return HttpResponse(
                f"{saved_count} Questions Uploaded Successfully"
            )

        except Exception as e:

            print("ERROR =", str(e))

            return HttpResponse(
                f"Error: {str(e)}"
            )

    return render(
        request,
        "question_upload.html",
        {
            "quizzes": quizzes
        }
    )

