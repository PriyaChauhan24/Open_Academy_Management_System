from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.conf import settings
from django.http import JsonResponse, HttpResponse
from django.core.files.base import ContentFile
import cv2
import os
import face_recognition
import numpy as np
import base64

# Models and Forms
from .models import User, Course, Enrollment, Lesson, QuizQuestion, LessonProgress
from .forms import CourseForm, StudentRegistrationForm

# Certificate Generation Imports
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import landscape, A4
from reportlab.lib import colors

# --- 1. REGISTRATION FLOW ---
def register(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role') 
        enroll_num = request.POST.get('enrollment_number')

        if User.objects.filter(username=username).exists():
            return render(request, 'registration/register.html', {'error': 'Username already taken'})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.enrollment_number = enroll_num
        
        if role == 'teacher':
            user.is_teacher, user.is_student = True, False
        else:
            user.is_student, user.is_teacher = True, False
        
        user.save()
        login(request, user)
        # Redirect to face capture to complete biometric profile
        return redirect('capture_face') 

    return render(request, 'registration/register.html')

# --- 2. MASTER DASHBOARD (Teacher & Student Logic) ---
@login_required
def dashboard(request):
    # --- TEACHER LOGIC ---
    if request.user.is_teacher:
        if request.method == 'POST':
            # Handle Course Creation from Studio
            if 'create_course' in request.POST:
                form = CourseForm(request.POST, request.FILES)
                if form.is_valid():
                    course = form.save(commit=False)
                    course.teacher = request.user
                    course.save()
                    return redirect('dashboard')
            
            # Handle Profile Update
            elif 'update_profile' in request.POST:
                request.user.username = request.POST.get('username')
                if 'profile_pic' in request.FILES:
                    request.user.profile_picture = request.FILES['profile_pic']
                request.user.save()
                return redirect('dashboard')

        my_courses = Course.objects.filter(teacher=request.user)
        context_data = {
            'my_courses': my_courses,
            'total_courses': my_courses.count(),
            'total_students': Enrollment.objects.filter(course__in=my_courses).count() + 1240,
            'form': CourseForm()
        }
        return render(request, 'dashboards/teacher_dashboard.html', context_data)

    # --- STUDENT LOGIC (UPDATED) ---
    # Handle AJAX Profile Updates (Name) from the Dashboard Modal
    if request.method == 'POST' and 'update_profile' in request.POST:
        new_name = request.POST.get('full_name')
        if new_name:
            request.user.username = new_name 
            request.user.save()
            return JsonResponse({'status': 'success', 'message': 'Profile updated!'})

    all_courses = Course.objects.all().order_by('-created_at')
    enrolled = Enrollment.objects.filter(student=request.user)
    
    course_progress_data = []
    total_finished = 0
    total_pending = 0

    for item in enrolled:
        total_lessons = item.course.lessons.count()
        completed = LessonProgress.objects.filter(
            student=request.user, 
            lesson__course=item.course, 
            is_completed=True
        ).count()
        
        percent = int((completed / total_lessons * 100)) if total_lessons > 0 else 0
        course_progress_data.append({
            'course': item.course,
            'percent': percent,
            'completed': completed,
            'total': total_lessons
        })
        total_finished += completed
        total_pending += (total_lessons - completed)

    # Resolve profile picture URL for sidebar/settings
    profile_url = request.user.profile_picture.url if request.user.profile_picture else "/static/img/default-avatar.png"

    return render(request, 'dashboards/student_dashboard.html', {
        'all_courses': all_courses,
        'progress_data': course_progress_data,
        'total_finished': total_finished,
        'total_pending': total_pending,
        'profile_url': profile_url, 
    })

# --- 3. AI BIOMETRIC MODULE (Capture & Login) ---
@login_required
def capture_face(request):
    if request.method == 'POST':
        image_data = request.POST.get('image_data')
        if image_data:
            try:
                # Decode Base64 from Canvas
                format, imgstr = image_data.split(';base64,')
                ext = format.split('/')[-1]
                temp_data = base64.b64decode(imgstr)
                
                # Setup Directory
                profile_pics_path = os.path.join(settings.MEDIA_ROOT, 'profile_pics')
                if not os.path.exists(profile_pics_path):
                    os.makedirs(profile_pics_path, exist_ok=True)

                # Convert to OpenCV Format
                nparr = np.frombuffer(temp_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                new_encoding = face_recognition.face_encodings(rgb_img)

                if len(new_encoding) > 0:
                    data = ContentFile(temp_data, name=f"user_{request.user.id}.{ext}")
                    request.user.profile_picture = data
                    request.user.save()
                    return JsonResponse({'status': 'success', 'redirect': '/dashboard/'})
                
                return JsonResponse({'status': 'error', 'message': 'No face detected.'})
            except Exception as e:
                return JsonResponse({'status': 'error', 'message': str(e)})
            
    return render(request, 'face_capture.html')

def face_login_verify(request):
    if request.method == 'POST':
        image_data = request.POST.get('image_data')
        if not image_data:
            return JsonResponse({'status': 'error', 'message': 'No image data received.'})

        try:
            # Process incoming image
            format, imgstr = image_data.split(';base64,')
            temp_data = base64.b64decode(imgstr)
            nparr = np.frombuffer(temp_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            current_face_encodings = face_recognition.face_encodings(rgb_img)

            if len(current_face_encodings) > 0:
                current_face_encoding = current_face_encodings[0]
                
                # Match against stored profiles
                users = User.objects.exclude(profile_picture='')
                for user in users:
                    if os.path.exists(user.profile_picture.path):
                        saved_image = face_recognition.load_image_file(user.profile_picture.path)
                        saved_encodings = face_recognition.face_encodings(saved_image)
                        
                        if len(saved_encodings) > 0:
                            # 0.6 is standard tolerance, 0.5 is strict
                            match = face_recognition.compare_faces([saved_encodings[0]], current_face_encoding, tolerance=0.5)
                            if match[0]:
                                login(request, user)
                                return JsonResponse({'status': 'success', 'redirect': '/dashboard/'})

                return JsonResponse({'status': 'error', 'message': 'Identity not recognized.'})
            return JsonResponse({'status': 'error', 'message': 'No face detected.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'System Error: {str(e)}'})
    
    return render(request, 'registration/login.html')

# --- 4. ACADEMIC MODULES & UTILITIES ---
@login_required
def watch_lesson(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    all_lessons = Lesson.objects.filter(course=lesson.course).order_by('order')
    return render(request, 'watch_lesson.html', {'lesson': lesson, 'all_lessons': all_lessons})

@login_required
def take_quiz(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    if request.method == 'POST':
        LessonProgress.objects.update_or_create(
            student=request.user, lesson=lesson,
            defaults={'is_completed': True, 'quiz_score': 100}
        )
        return render(request, 'quiz_result.html', {'score': 100, 'lesson': lesson})
    return render(request, 'take_quiz.html', {'lesson': lesson, 'questions': lesson.questions.all()})

@login_required
def enroll_in_course(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    return redirect('dashboard')

@login_required
def generate_certificate(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=landscape(A4))
    width, height = landscape(A4)
    
    # Simple Certificate Styling
    p.setStrokeColor(colors.gold)
    p.setLineWidth(10)
    p.rect(20, 20, width-40, height-40)
    p.setFont("Helvetica-Bold", 40)
    p.drawCentredString(width/2, height-150, "CERTIFICATE OF COMPLETION")
    p.setFont("Helvetica", 20)
    p.drawCentredString(width/2, height-230, "This is to certify that")
    p.setFont("Helvetica-Bold", 30)
    p.drawCentredString(width/2, height-280, request.user.username.upper())
    p.setFont("Helvetica", 20)
    p.drawCentredString(width/2, height-330, f"has successfully completed the course")
    p.setFont("Helvetica-BoldOblique", 25)
    p.drawCentredString(width/2, height-380, f"'{course.title}'")
    
    p.showPage()
    p.save()
    
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{course.title}_Certificate.pdf"'
    response.write(buffer.getvalue())
    return response

def user_logout(request):
    logout(request)
    return redirect('login')
