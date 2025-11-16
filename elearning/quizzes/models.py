from django.db import models
from django.conf import settings
from elearning.courses.models import Video, Unit

class Question(models.Model):
    QUESTION_TYPES = [
        ('mcq', 'Multiple Choice'),
        ('true_false', 'True/False'),
    ]
    
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPES, default='mcq')
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.video.title} - {self.question_text[:50]}"
    
    class Meta:
        ordering = ['order']


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer_text = models.CharField(max_length=500)
    is_correct = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"{self.question.question_text[:30]} - {self.answer_text[:30]}"
    
    class Meta:
        ordering = ['order']


class Quiz(models.Model):
    video = models.OneToOneField(Video, on_delete=models.CASCADE, related_name='quiz')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    pass_percentage = models.PositiveIntegerField(default=70)
    time_limit = models.PositiveIntegerField(default=30, help_text="Time limit in minutes")
    deadline = models.DateTimeField(blank=True, null=True, help_text="Deadline for students to complete quiz")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_total_questions(self):
        return self.video.questions.count()
    
    def get_total_points(self):
        return sum(q.points for q in self.video.questions.all())
    
    def is_deadline_passed(self):
        """Check if the quiz deadline has passed"""
        if not self.deadline:
            return False
        from django.utils import timezone
        return timezone.now() > self.deadline
    
    def is_available(self):
        """Check if quiz is available for students to take"""
        return self.is_active and not self.is_deadline_passed()
    
    class Meta:
        verbose_name_plural = 'Quizzes'


class QuizAttempt(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quiz_attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='attempts')
    video = models.ForeignKey(Video, on_delete=models.CASCADE, related_name='quiz_attempts')
    score = models.FloatField(default=0.0)
    total_points = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    is_passed = models.BooleanField(default=False)
    time_taken = models.PositiveIntegerField(default=0, help_text="Time taken in seconds")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} - {self.percentage}%"
    
    class Meta:
        ordering = ['-started_at']


class StudentAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name='student_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_answer = models.ForeignKey(Answer, on_delete=models.CASCADE, blank=True, null=True)
    is_correct = models.BooleanField(default=False)
    points_earned = models.FloatField(default=0.0)
    
    def __str__(self):
        return f"{self.attempt.student.username} - Q: {self.question.question_text[:30]}"
    
    class Meta:
        unique_together = ['attempt', 'question']


class Leaderboard(models.Model):
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='leaderboards')
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leaderboard_entries')
    total_score = models.FloatField(default=0.0)
    total_quizzes = models.PositiveIntegerField(default=0)
    average_score = models.FloatField(default=0.0)
    rank = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.unit.title} - {self.student.username} - Rank {self.rank}"
    
    class Meta:
        unique_together = ['unit', 'student']
        ordering = ['rank']
