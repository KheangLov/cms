from django.contrib import admin

from .models import Answer, Choice, Question, Quiz, QuizAttempt

admin.site.register(Quiz)
admin.site.register(Question)
admin.site.register(Choice)
admin.site.register(QuizAttempt)
admin.site.register(Answer)
