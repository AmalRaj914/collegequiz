from django.urls import path
from .import views

urlpatterns = [

    # ============================
    # Student
    # ============================

        

    # ============================
    # Faculty
    # ============================

   
        path(
        "faculty-dashboard/",
        views.faculty_dashboard,
        name="faculty_dashboard"
    ),

    path(
    "upload-students/",
    views.upload_students,
    name="upload_students"
),


path(
    "upload-question-bank/",
    views.upload_question_bank,
    name="upload_question_bank"
),

path(
    "create-quiz/",
    views.create_quiz,
    name="create_quiz"
),

path(
    "results/",
    views.result_list,
    name="result_list"
),

path(
    "participants/",
    views.participant_list,
    name="participant_list"
),



path(
    "student-dashboard/",
    views.student_dashboard,
    name="student_dashboard"
),

path(
    "",
    views.login_view,
    name="login"
),

path(
    "logout/",
    views.logout_view,
    name="logout"
),

path(
    "quiz/<int:quiz_id>/",
    views.quiz_page,
    name="quiz_page"
),
path(
    "publish-quiz/",
    views.publish_quiz,
    name="publish_quiz"
),

path(
    "publish/<int:quiz_id>/",
    views.publish,
    name="publish"
),

path(
    "submit-quiz/<int:quiz_id>/",
    views.submit_quiz,
    name="submit_quiz"
),

path(
    "student-result/<int:quiz_id>/",
    views.student_result,
    name="student_result"
),

path(
    "generate-report/",
    views.generate_report,
    name="generate_report"
),
path(
        "upload-activity-photo/<int:quiz_id>/",
        views.upload_activity_photo,
        name="upload_activity_photo"
    ),

path(
    "student-result/<int:quiz_id>/",
    views.student_result,
    name="student_result"
),
path(
    "results/",
    views.result_list,
    name="result_list"
),
path(

    "download-report/<int:quiz_id>/",

    views.download_pdf_report,

    name="download_pdf_report"

),

]
   