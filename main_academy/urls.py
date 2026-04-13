from django.urls import path
from . import views

urlpatterns = [
    path('student-dashboard/', views.dashboard, name='student_dashboard'),
    #path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('quiz/<int:lesson_id>/', views.take_quiz, name='take_quiz'),
    path('certificate/<int:course_id>/', views.generate_certificate, name='generate_certificate'),
    #path('course-report/<int:course_id>/', views.teacher_report, name='teacher_report'),
    path('capture-face/', views.capture_face, name='capture_face'),
    # Change this line in your main_academy/urls.py
    path('logout/', views.user_logout, name='logout'),
]
