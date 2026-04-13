from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, Enrollment, Lesson, QuizQuestion, LessonProgress

# 1. Advanced User Management
@admin.register(User)
class CustomUserAdmin(UserAdmin):
    # This adds your custom fields to the User edit page
    fieldsets = UserAdmin.fieldsets + (
        ('Role Management', {'fields': ('is_teacher', 'is_student', 'profile_picture', 'enrollment_number')}),
    )
    list_display = ['username', 'enrollment_number', 'is_teacher', 'is_student', 'is_staff']
    list_filter = ['is_teacher', 'is_student', 'is_staff']
    search_fields = ['username', 'enrollment_number']

# 2. Inline Lessons (See Lessons inside Course page)
class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1 # Allows adding one extra lesson quickly

# 3. Course Management
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'category', 'is_paid', 'price', 'created_at']
    list_filter = ['category', 'is_paid', 'created_at']
    search_fields = ['title', 'teacher__username']
    inlines = [LessonInline] # Shows lessons directly inside the course

# 4. Inline Quiz Questions (See Questions inside Lesson page)
class QuizQuestionInline(admin.TabularInline):
    model = QuizQuestion
    extra = 4 # Default 4 options for a quiz

@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order']
    list_filter = ['course']
    inlines = [QuizQuestionInline]

# 5. Simple Registration for other models
admin.site.register(Enrollment)
admin.site.register(LessonProgress)
