from django.contrib import admin
from .models import Question, Answer, Quiz, QuizAttempt, StudentAnswer, Leaderboard

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'video', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'video__unit__course']
    search_fields = ['question_text', 'video__title']
    inlines = [AnswerInline]

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['title', 'video', 'pass_percentage', 'time_limit', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['title', 'video__title']

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'quiz', 'percentage', 'is_passed', 'completed_at']
    list_filter = ['is_passed', 'started_at']
    search_fields = ['student__username', 'quiz__title']

@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ['attempt', 'question', 'selected_answer', 'is_correct', 'points_earned']
    list_filter = ['is_correct']
    search_fields = ['attempt__student__username', 'question__question_text']

@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    list_display = ['unit', 'student', 'rank', 'total_score', 'average_score', 'updated_at']
    list_filter = ['unit', 'updated_at']
    search_fields = ['student__username', 'unit__title']
