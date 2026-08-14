from rest_framework import serializers

from .models import Answer, Choice, Question, Quiz, QuizAttempt

# --- Admin/authoring serializers (include is_correct) -----------------------


class ChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "is_correct", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    choices = ChoiceSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "choices"]


class QuizSerializer(serializers.ModelSerializer):
    """Authoring contract: the whole question/choice tree is written as one
    nested payload, same "replace-all-on-save" shape PageSerializer already
    uses for translations — no separate question/choice CRUD endpoints."""

    questions = QuestionSerializer(many=True, required=False)

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "slug", "description", "is_published",
            "created_by", "created_at", "updated_at", "questions",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        quiz = Quiz.objects.create(**validated_data)
        self._save_questions(quiz, questions_data)
        return quiz

    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            instance.questions.all().delete()
            self._save_questions(instance, questions_data)
        return instance

    @staticmethod
    def _save_questions(quiz, questions_data):
        for order, q_data in enumerate(questions_data):
            choices_data = q_data.pop("choices", [])
            q_data.setdefault("order", order)
            question = Question.objects.create(quiz=quiz, **q_data)
            for c_order, c_data in enumerate(choices_data):
                c_data.setdefault("order", c_order)
                Choice.objects.create(question=question, **c_data)


# --- Public serializers (never expose is_correct) ---------------------------


class ChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ["id", "text", "order"]


class QuestionPublicSerializer(serializers.ModelSerializer):
    choices = ChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ["id", "text", "order", "choices"]


class QuizPublicSerializer(serializers.ModelSerializer):
    questions = QuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "slug", "description", "questions"]


# --- Attempt submission -------------------------------------------------


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Write side: {respondent_name?, respondent_email?, answers: [{question_id,
    choice_id}]}. Scoring happens here, server-side, from each choice's real
    `is_correct` — never trusts a client-submitted score. Unknown/mismatched
    question or choice ids are silently skipped rather than rejecting the
    whole submission, so one bad id can't block an otherwise-valid attempt."""

    answers = serializers.ListField(child=serializers.DictField(), write_only=True)
    per_question = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "respondent_name", "respondent_email", "answers",
            "score", "total_questions", "completed_at", "per_question",
        ]
        read_only_fields = ["id", "score", "total_questions", "completed_at"]

    def get_per_question(self, obj):
        return getattr(obj, "_per_question_result", [])

    def create(self, validated_data):
        quiz = self.context["quiz"]
        answers_data = validated_data.pop("answers")
        request = self.context["request"]

        questions_by_id = {q.id: q for q in quiz.questions.prefetch_related("choices")}
        score = 0
        per_question = []
        rows = []
        for ans in answers_data:
            question = questions_by_id.get(ans.get("question_id"))
            if question is None:
                continue
            choice = next((c for c in question.choices.all() if c.id == ans.get("choice_id")), None)
            if choice is None:
                continue
            if choice.is_correct:
                score += 1
            correct_choice = next((c for c in question.choices.all() if c.is_correct), None)
            per_question.append({
                "question_id": question.id,
                "correct": choice.is_correct,
                "correct_choice_id": correct_choice.id if correct_choice else None,
            })
            rows.append(Answer(question=question, choice=choice))

        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user if request.user.is_authenticated else None,
            respondent_name=validated_data.get("respondent_name", ""),
            respondent_email=validated_data.get("respondent_email", ""),
            score=score,
            total_questions=quiz.questions.count(),
        )
        for row in rows:
            row.attempt = attempt
        Answer.objects.bulk_create(rows)
        attempt._per_question_result = per_question
        return attempt
