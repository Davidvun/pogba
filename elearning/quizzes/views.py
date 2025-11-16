from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from elearning.accounts.decorators import tutor_required
from .models import Quiz, Question, Answer, QuizAttempt, StudentAnswer
from elearning.courses.models import Video, CourseEnrollment
import json


@tutor_required
def tutor_create_quiz(request, video_id):
    video = get_object_or_404(Video, id=video_id, unit__course__tutor=request.user)
    
    if hasattr(video, 'quiz'):
        messages.info(request, 'This video already has a quiz.')
        return redirect('tutor_edit_quiz', quiz_id=video.quiz.id)
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        pass_percentage = request.POST.get('pass_percentage', 70)
        time_limit = request.POST.get('time_limit', 30)
        deadline = request.POST.get('deadline')
        
        quiz = Quiz.objects.create(
            video=video,
            title=title,
            description=description,
            pass_percentage=pass_percentage,
            time_limit=time_limit,
            deadline=deadline if deadline else None
        )
        
        messages.success(request, 'Quiz created successfully! Now add questions.')
        return redirect('tutor_add_question', quiz_id=quiz.id)
    
    return render(request, 'quizzes/tutor_create_quiz.html', {'video': video})


@tutor_required
def tutor_edit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, video__unit__course__tutor=request.user)
    questions = quiz.video.questions.prefetch_related('answers').all()
    
    if request.method == 'POST':
        quiz.title = request.POST.get('title')
        quiz.description = request.POST.get('description')
        quiz.pass_percentage = request.POST.get('pass_percentage', 70)
        quiz.time_limit = request.POST.get('time_limit', 30)
        quiz.is_active = request.POST.get('is_active') == 'on'
        deadline = request.POST.get('deadline')
        quiz.deadline = deadline if deadline else None
        quiz.save()
        
        messages.success(request, 'Quiz updated successfully!')
        return redirect('tutor_edit_quiz', quiz_id=quiz.id)
    
    return render(request, 'quizzes/tutor_edit_quiz.html', {
        'quiz': quiz,
        'questions': questions
    })


@tutor_required
def tutor_add_question(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, video__unit__course__tutor=request.user)
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        question_type = request.POST.get('question_type', 'mcq')
        points = request.POST.get('points', 1)
        order = request.POST.get('order', 0)
        
        question = Question.objects.create(
            video=quiz.video,
            question_text=question_text,
            question_type=question_type,
            points=points,
            order=order
        )
        
        answer_texts = request.POST.getlist('answer_text[]')
        is_correct_list = request.POST.getlist('is_correct[]')
        
        for i, answer_text in enumerate(answer_texts):
            if answer_text.strip():
                Answer.objects.create(
                    question=question,
                    answer_text=answer_text,
                    is_correct=str(i) in is_correct_list,
                    order=i
                )
        
        messages.success(request, 'Question added successfully!')
        return redirect('tutor_edit_quiz', quiz_id=quiz.id)
    
    max_order = quiz.video.questions.count()
    return render(request, 'quizzes/tutor_add_question.html', {
        'quiz': quiz,
        'suggested_order': max_order + 1
    })


@tutor_required
def tutor_delete_question(request, question_id):
    question = get_object_or_404(Question, id=question_id, video__unit__course__tutor=request.user)
    quiz_id = question.video.quiz.id
    question.delete()
    messages.success(request, 'Question deleted successfully!')
    return redirect('tutor_edit_quiz', quiz_id=quiz_id)


@login_required
def take_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    
    enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=quiz.video.unit.course,
        is_active=True
    ).first()
    
    if not enrollment:
        messages.error(request, 'You must be enrolled in this course to take the quiz.')
        return redirect('course_catalog')
    
    if not quiz.is_available():
        if quiz.is_deadline_passed():
            messages.error(request, 'The deadline for this quiz has passed.')
        else:
            messages.error(request, 'This quiz is not currently active.')
        return redirect('course_learn', course_id=quiz.video.unit.course.id)
    
    questions = quiz.video.questions.prefetch_related('answers').all()
    
    return render(request, 'quizzes/take_quiz.html', {
        'quiz': quiz,
        'questions': questions
    })


@login_required
@require_http_methods(["POST"])
def submit_quiz(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id)
    data = json.loads(request.body)
    
    enrollment = CourseEnrollment.objects.filter(
        student=request.user,
        course=quiz.video.unit.course,
        is_active=True
    ).first()
    
    if not enrollment:
        return JsonResponse({'error': 'Not enrolled'}, status=403)
    
    attempt = QuizAttempt.objects.create(
        student=request.user,
        quiz=quiz,
        video=quiz.video
    )
    
    total_score = 0
    total_points = 0
    
    for q_data in data.get('answers', []):
        question = Question.objects.get(id=q_data['question_id'])
        total_points += question.points
        
        selected_answer_id = q_data.get('answer_id')
        if selected_answer_id:
            selected_answer = Answer.objects.get(id=selected_answer_id)
            is_correct = selected_answer.is_correct
            points_earned = question.points if is_correct else 0
            total_score += points_earned
            
            StudentAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_answer=selected_answer,
                is_correct=is_correct,
                points_earned=points_earned
            )
    
    percentage = (total_score / total_points * 100) if total_points > 0 else 0
    is_passed = percentage >= quiz.pass_percentage
    
    attempt.score = total_score
    attempt.total_points = total_points
    attempt.percentage = percentage
    attempt.is_passed = is_passed
    attempt.completed_at = timezone.now()
    attempt.save()
    
    return JsonResponse({
        'score': total_score,
        'total_points': total_points,
        'percentage': percentage,
        'is_passed': is_passed,
        'attempt_id': attempt.id
    })


@login_required
def quiz_results(request, attempt_id):
    attempt = get_object_or_404(QuizAttempt, id=attempt_id, student=request.user)
    student_answers = attempt.student_answers.select_related('question', 'selected_answer').all()
    
    return render(request, 'quizzes/results.html', {
        'attempt': attempt,
        'student_answers': student_answers
    })


@tutor_required
def tutor_quiz_analytics(request, quiz_id):
    quiz = get_object_or_404(Quiz, id=quiz_id, video__unit__course__tutor=request.user)
    attempts = QuizAttempt.objects.filter(quiz=quiz).select_related('student')
    
    return render(request, 'quizzes/tutor_quiz_analytics.html', {
        'quiz': quiz,
        'attempts': attempts
    })
