from django.contrib import admin
from .models import (
    CollegeInfo,
    Department,
    Faculty,
    Quiz,
    Question,
    Student,
    Result,
    ActivityReport,
    ActivityPhoto,
    QuestionBank,
    StudentExcel,
    Attendance,
)

admin.site.register(CollegeInfo)
admin.site.register(Department)
admin.site.register(Faculty)
admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Student)
admin.site.register(Result)
admin.site.register(ActivityReport)
admin.site.register(ActivityPhoto)
admin.site.register(QuestionBank)
admin.site.register(StudentExcel)
admin.site.register(Attendance)