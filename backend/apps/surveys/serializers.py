from rest_framework import serializers

from .models import Survey, SurveyAnswer, SurveyChoice, SurveyQuestion, SurveyResponse

# --- Admin/authoring serializers ---------------------------------------


class SurveyChoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyChoice
        fields = ["id", "text", "order"]


class SurveyQuestionSerializer(serializers.ModelSerializer):
    choices = SurveyChoiceSerializer(many=True, required=False)

    class Meta:
        model = SurveyQuestion
        fields = ["id", "text", "question_type", "order", "choices"]


class SurveySerializer(serializers.ModelSerializer):
    """Same "replace-all-on-save" nested-write contract as QuizSerializer."""

    questions = SurveyQuestionSerializer(many=True, required=False)

    class Meta:
        model = Survey
        fields = [
            "id", "title", "slug", "description", "is_published",
            "created_by", "created_at", "updated_at", "questions",
        ]
        read_only_fields = ["id", "created_by", "created_at", "updated_at"]

    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        survey = Survey.objects.create(**validated_data)
        self._save_questions(survey, questions_data)
        return survey

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
    def _save_questions(survey, questions_data):
        for order, q_data in enumerate(questions_data):
            choices_data = q_data.pop("choices", [])
            q_data.setdefault("order", order)
            question = SurveyQuestion.objects.create(survey=survey, **q_data)
            for c_order, c_data in enumerate(choices_data):
                c_data.setdefault("order", c_order)
                SurveyChoice.objects.create(question=question, **c_data)


# --- Public serializers --------------------------------------------------


class SurveyChoicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyChoice
        fields = ["id", "text", "order"]


class SurveyQuestionPublicSerializer(serializers.ModelSerializer):
    choices = SurveyChoicePublicSerializer(many=True, read_only=True)

    class Meta:
        model = SurveyQuestion
        fields = ["id", "text", "question_type", "order", "choices"]


class SurveyPublicSerializer(serializers.ModelSerializer):
    questions = SurveyQuestionPublicSerializer(many=True, read_only=True)

    class Meta:
        model = Survey
        fields = ["id", "title", "slug", "description", "questions"]


# --- Response submission -----------------------------------------------


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Write side: {respondent_name?, respondent_email?, answers: [{question_id,
    choice_id}] or [{question_id, text}], matching each question's type}. No
    scoring — a survey response is just recorded. Unknown question/choice ids,
    or a choice_id on a text question (and vice versa), are silently skipped,
    same "don't fail the whole submission over one bad row" policy as Quiz."""

    answers = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = SurveyResponse
        fields = ["id", "respondent_name", "respondent_email", "answers", "submitted_at"]
        read_only_fields = ["id", "submitted_at"]

    def create(self, validated_data):
        survey = self.context["survey"]
        answers_data = validated_data.pop("answers")
        request = self.context["request"]

        questions_by_id = {q.id: q for q in survey.questions.prefetch_related("choices")}
        rows = []
        for ans in answers_data:
            question = questions_by_id.get(ans.get("question_id"))
            if question is None:
                continue
            if question.question_type == "choice":
                choice = next((c for c in question.choices.all() if c.id == ans.get("choice_id")), None)
                if choice is None:
                    continue
                rows.append(SurveyAnswer(question=question, choice=choice))
            else:
                text = (ans.get("text") or "").strip()
                if not text:
                    continue
                rows.append(SurveyAnswer(question=question, text=text))

        response = SurveyResponse.objects.create(
            survey=survey,
            user=request.user if request.user.is_authenticated else None,
            respondent_name=validated_data.get("respondent_name", ""),
            respondent_email=validated_data.get("respondent_email", ""),
        )
        for row in rows:
            row.response = response
        SurveyAnswer.objects.bulk_create(rows)
        return response
