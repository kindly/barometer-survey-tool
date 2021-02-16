from rest_framework import serializers
from api.models import SurveyData, Survey, SurveyDataType
from django.contrib.auth.models import User


class SurveySerializer(serializers.ModelSerializer):
    owner = serializers.SlugRelatedField(
       slug_field='email',
       queryset=User.objects.all()
    )
    class Meta:
        model = Survey
        fields = '__all__'

    def update(self, instance, validated_data):
        for attr, value in validated_data.items():
            if attr == 'control':
                old_control = instance.control
                old_control.update(value)
                new_control = {k:v for k,v in old_control.items() if v}
                instance.control = new_control
            else:
                setattr(instance, attr, value)
        instance.save()
        return instance

    def to_representation(self, instance):
        output = super().to_representation(instance)
        output.pop('owner')
        return output


class SurveyDataSerializer(serializers.ModelSerializer):
    type = serializers.SlugRelatedField(
       slug_field='type',
       queryset=SurveyDataType.objects.all()
    )

    class Meta:
        model = SurveyData
        fields = ['id', 'type', 'data']

    def to_internal_value(self, data):
        internal_value = super().to_internal_value(data)

        internal_value["survey_id"] = self.context['view'].kwargs['survey']

        return internal_value


    def to_representation(self, instance):
        output = super().to_representation(instance)
        new_data = {field: "" for field in instance.type.fields}
        new_data.update(output['data'])
        output['data'] = new_data
        return output

