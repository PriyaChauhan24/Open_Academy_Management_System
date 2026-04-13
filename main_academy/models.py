from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator

# 1. CUSTOM USER MODEL
# This handles both Student and Teacher roles and stores the AI Face ID profile pic
class User(AbstractUser):
    is_teacher = models.BooleanField(default=False)
    is_student = models.BooleanField(default=False)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    enrollment_number = models.CharField(max_length=20, unique=True, null=True, blank=True)

    def __str__(self):
        return self.username

# 2. COURSE MODEL
# Handles Technical/Non-Technical categories and Paid/Free logic
class Course(models.Model):
    CATEGORY_CHOICES = [
        ('technical', 'Technical'),
        ('non-technical', 'Non-Technical'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='courses_taught')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='technical')
    thumbnail = models.ImageField(upload_to='course_thumbs/', default='default_course.jpg')
    
    # Pricing logic
    is_paid = models.BooleanField(default=False)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Lecture Links
    thumbnail = models.ImageField(upload_to='course_thumbnails/', null=True, blank=True)
    live_lecture_link = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True) # Important for the "NEW" badge

    def __str__(self):
        return self.title

# 3. LESSON MODEL
# One Course can have many Lessons (Videos)
class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=255)
    video_url = models.URLField(help_text="YouTube Embed Link for VOD")
    order = models.IntegerField(default=1, help_text="Sequence (1, 2, 3...)")
    content = models.TextField(blank=True, help_text="Optional lesson notes")

    def __str__(self):
        return f"{self.course.title} - {self.title}"

# 4. ENROLLMENT MODEL
# Links a Student to a Course. Prevents double enrollment.
class Enrollment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='enrolled_courses')
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)

    class Meta:
        unique_together = ('student', 'course')

    def __str__(self):
        return f"{self.student.username} -> {self.course.title}"

# 5. QUIZ SYSTEM
# Each Lesson has its own set of questions
class QuizQuestion(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option1 = models.CharField(max_length=255)
    option2 = models.CharField(max_length=255)
    option3 = models.CharField(max_length=255)
    option4 = models.CharField(max_length=255)
    correct_answer = models.IntegerField(choices=[(1, 'Option 1'), (2, 'Option 2'), (3, 'Option 3'), (4, 'Option 4')])

    def __str__(self):
        return f"Quiz for {self.lesson.title}"

# 6. PERFORMANCE TRACKING
# Tracks which student finished which lesson and their score
class LessonProgress(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE)
    is_completed = models.BooleanField(default=False)
    quiz_score = models.FloatField(default=0.0)
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'lesson')

    def __str__(self):
        return f"{self.student.username} progress on {self.lesson.title}"
