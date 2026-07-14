from django.db import models



# --------------------------------
# College Information
# --------------------------------

class CollegeInfo(models.Model):

    college_name = models.CharField(
        max_length=300
    )

    department_name = models.CharField(
        max_length=200
    )

    faculty_name = models.CharField(
        max_length=100
    )

    faculty_designation = models.CharField(
        max_length=100
    )

    hod_name = models.CharField(
        max_length=100
    )

    principal_name = models.CharField(
        max_length=100
    )

    academic_year = models.CharField(
        max_length=20,
        default='2026-27'
    )


    def __str__(self):

        return self.college_name

class Department(models.Model):

    department_code = models.CharField(max_length=5, unique=True)

    department_name = models.CharField(max_length=100)

    def __str__(self):
        return self.department_name
    

# --------------------------------
# Faculty
# --------------------------------

from django.contrib.auth.models import User

class Faculty(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    faculty_name = models.CharField(
        max_length=100
    )

    email = models.EmailField(
        unique=True
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    designation = models.CharField(
        max_length=100
    )

    mobile = models.CharField(
        max_length=15,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.faculty_name

# --------------------------------
# Quiz
# --------------------------------

class Quiz(models.Model):

    faculty = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=200)

    subject_code = models.CharField(max_length=20)

    subject_name = models.CharField(max_length=200)

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    year = models.IntegerField()

    section = models.CharField(max_length=5)

    duration = models.IntegerField(default=20)

    total_questions = models.IntegerField(default=20)

    status = models.BooleanField(default=False)

    created_date = models.DateTimeField(auto_now_add=True)

    ai_report = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title


# --------------------------------
# Questions
# --------------------------------

# --------------------------------
# Question
# --------------------------------

class Question(models.Model):

    

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    question = models.TextField()

    option1 = models.CharField(
        max_length=200
    )

    option2 = models.CharField(
        max_length=200
    )

    option3 = models.CharField(
        max_length=200
    )

    option4 = models.CharField(
        max_length=200
    )

    correct_answer = models.CharField(
        max_length=200
    )

    marks = models.IntegerField(
        default=1
    )
    unit = models.IntegerField(
    default=1
)

    question_level = models.CharField(
        max_length=20,
        choices=[
            ('Easy', 'Easy'),
            ('Medium', 'Medium'),
            ('Hard', 'Hard')
        ],
        default='Easy'
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.question






# --------------------------------
# Student
# --------------------------------

from django.contrib.auth.models import User
from django.contrib.auth.models import User

class Student(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    roll_no = models.CharField(
        max_length=20,
        unique=True
    )

    student_name = models.CharField(
        max_length=150
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE
    )

    batch_year = models.IntegerField()

    section = models.CharField(
        max_length=5
    )

    is_attempted = models.BooleanField(
        default=False
    )

    created_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.student_name
# --------------------------------
# Result
# --------------------------------

class Result(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    score = models.IntegerField()

    percentage = models.FloatField()

    submitted_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "quiz"],
                name="unique_student_quiz"
            )
        ]

    def __str__(self):
        return f"{self.student.roll_no} - {self.quiz.title}"





# --------------------------------
# Activity Report
# --------------------------------

class ActivityReport(models.Model):


    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )


    objective = models.TextField(
        blank=True
    )


    summary = models.TextField(
        blank=True
    )


    outcome = models.TextField(
        blank=True
    )


    ai_report = models.TextField(
        blank=True,
        null=True
    )


    photo1 = models.ImageField(
        upload_to='photos/',
        blank=True,
        null=True
    )


    photo2 = models.ImageField(
        upload_to='photos/',
        blank=True,
        null=True
    )


    generated_date = models.DateTimeField(
        auto_now_add=True
    )






# --------------------------------
# Activity Photos
# --------------------------------

class ActivityPhoto(models.Model):

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    title = models.CharField(max_length=100)

    photo = models.ImageField(
        upload_to="activity_photos/"
    )

    latitude = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    longitude = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    address = models.TextField(
        blank=True,
        null=True
    )

    uploaded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


        # --------------------------------
# Question Bank Upload
# --------------------------------

class QuestionBank(models.Model):

    FILE_TYPES = [
        ("excel","Excel"),
        ("word","Word"),
        ("pdf","PDF"),
        ("csv","CSV"),
        ("txt","Text")
    ]

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    uploaded_by = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE
    )

    file = models.FileField(
        upload_to="question_bank/"
    )
    file_type = models.CharField(
    max_length=20,
    choices=FILE_TYPES,
    default="excel"
)

    total_questions = models.IntegerField(default=0)

    uploaded_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        default="Pending"
    )

    remarks = models.TextField(
        blank=True,
        null=True
    )
    def __str__(self):
        return self.quiz.title

class StudentExcel(models.Model):

    file = models.FileField(
        upload_to="student_excel/"
    )

    uploaded_by = models.ForeignKey(
        Faculty,
        on_delete=models.CASCADE
    )

    uploaded_date = models.DateTimeField(
        auto_now_add=True
    )

    status = models.CharField(
        max_length=20,
        default="Uploaded"
    )
    def __str__(self):
        return self.file.name

class Attendance(models.Model):

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE
    )

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE
    )

    login_time = models.DateTimeField(auto_now_add=True)

    logout_time = models.DateTimeField(
        blank=True,
        null=True
    )

    completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.student.roll_no} - {self.quiz.title}"
    


