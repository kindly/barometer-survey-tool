from rest_framework import serializers
from rest_framework.reverse import reverse
from api.models import (
    SurveyData,
    Survey,
    SurveyDataType,
    QuestionData,
    SURVEY_DATA_PRIVATE_FIELDS,
)
from django.contrib.auth.models import User


class SurveySerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
        slug_field="email", queryset=User.objects.all()
    )

    class Meta:
        model = Survey
        fields = "__all__"

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == "control":
                old_control = instance.control
                old_control.update(value)
                new_control = {k: v for k, v in old_control.items() if v}
                instance.control = new_control
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        output = super().to_representation(instance)
        output.pop("owner")
        output["_url"] = self.context["view"].reverse_action(
            "detail", args=[instance.id]
        )
        output["_data_url"] = reverse(
            "survey-data-list", args=[instance.id], request=self.context["request"]
        )
        return output


class SurveyDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyData
        fields = ["id", "type", "data"]

    type = serializers.SlugRelatedField(
        slug_field="type", queryset=SurveyDataType.objects.all()
    )

    def to_internal_value(self, data):
        if "data" not in data:
            data["data"] = {}
            for key, value in list(data.items()):
                if key.startswith("_") or key in SURVEY_DATA_PRIVATE_FIELDS:
                    continue
                data["data"][key] = value
                data.pop(key)

        internal_value = super().to_internal_value(data)

        internal_value["survey_id"] = self.context["view"].kwargs["survey"]

        return internal_value

    def to_representation(self, instance):
        output = super().to_representation(instance)
        data = output.pop("data")
        new_data = {}
        for key in instance.type.fields:
            new_data[key] = data.get(key, "")

        output.update(new_data)

        output["_url"] = self.context["view"].reverse_action(
            "detail", args=[instance.survey.id, instance.id]
        )

        return output


class SurveyDataTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = SurveyDataType
        fields = ["id", "type", "fields"]


class QuestionDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionData
        fields = ["id", "type", "data"]

    def to_internal_value(self, data):
        if "data" not in data:
            data["data"] = {}
            for key, value in list(data.items()):
                if key.startswith("_"):
                    continue
                data["data"][key] = value
                data.pop(key)

        internal_value = super().to_internal_value(data)

        return internal_value

    def to_representation(self, instance):
        output = super().to_representation(instance)
        data = output.pop("data")

        output.update(data)

        output["_url"] = self.context["view"].reverse_action(
            "detail", args=[instance.id]
        )

        return output
