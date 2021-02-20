from django.db import models
from django.core.exceptions import ValidationError

SURVEY_DATA_PRIVATE_FIELDS = ["id", "survey", "type", "data"]


def validate_survey_data_type(value):
    if not isinstance(value, list):
        raise ValidationError("json needs to be an array")
    for item in value:
        if not isinstance(item, str):
            raise ValidationError("all fields need to be strings")
        if item.startswith("_"):
            raise ValidationError("fields can not start with '_'")
        if item in SURVEY_DATA_PRIVATE_FIELDS:
            raise ValidationError(
                f"fields can not be named {' or '.join(SURVEY_DATA_PRIVATE_FIELDS)}"
            )
    if len(set(value)) != len(value):
        raise ValidationError("there can not be duplicate fields")


class Survey(models.Model):
    class Meta:
        db_table = "survey"

    owner = models.ForeignKey(
        "auth.User", related_name="survey", on_delete=models.PROTECT
    )
    control = models.JSONField()

    def __str__(self):
        return (
            "id: "
            + str(self.id)
            + "  owner: "
            + str(self.owner)
            + ", "
            + ", ".join(
                [key + ": " + str(value) for key, value in self.control.items()]
            )
        )


class SurveyLog(models.Model):
    class Meta:
        db_table = "survey_log"

    parent = models.ForeignKey(Survey, on_delete=models.CASCADE, db_constraint=False)
    event_datetime = models.DateTimeField()
    action = models.CharField(max_length=1)
    username = models.TextField()
    data = models.JSONField()


class SurveyDataType(models.Model):
    class Meta:
        db_table = "survey_data_type"

    type = models.TextField(unique=True)
    fields = models.JSONField(validators=[validate_survey_data_type])

    def __str__(self):
        return self.type + ":   " + ", ".join(self.fields)


class SurveyData(models.Model):
    class Meta:
        db_table = "survey_data"

    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    type = models.ForeignKey(SurveyDataType, on_delete=models.PROTECT)
    data = models.JSONField()

    def __str__(self):
        return "id:" + str(self.id)


class SurveyDataLog(models.Model):
    class Meta:
        db_table = "survey_data_log"

    parent = models.ForeignKey(
        SurveyData, on_delete=models.CASCADE, db_constraint=False
    )
    event_datetime = models.DateTimeField()
    action = models.CharField(max_length=1)
    username = models.TextField()
    data = models.JSONField()


class QuestionData(models.Model):
    class Meta:
        db_table = "questions_data"

    type = models.TextField()
    data = models.JSONField()
