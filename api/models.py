from django.db import models
from django.core.exceptions import ValidationError

def validate_list(value):
    if not isinstance(value, list):
        raise ValidationError("json needs to be a list")

class Survey(models.Model):
    class Meta:
        db_table = "survey"
    owner = models.ForeignKey('auth.User', related_name='survey', on_delete=models.PROTECT)
    control = models.JSONField()
    def __str__(self):
        return 'id: ' + str(self.id) + '  owner: ' + str(self.owner) + ', ' + ', '.join([key + ': ' + str(value) for key, value in self.control.items()])

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
    fields = models.JSONField(validators=[validate_list])
    def __str__(self):
        return self.type + ':   ' + ', '.join(self.fields)


class SurveyData(models.Model):
    class Meta:
        db_table = "survey_data"
    survey = models.ForeignKey(Survey, on_delete=models.CASCADE)
    type = models.ForeignKey(SurveyDataType, on_delete=models.PROTECT)
    data = models.JSONField()

    def __str__(self):
        return 'id:' + str(self.id) 

class SurveyDataLog(models.Model):
    class Meta:
        db_table = "survey_data_log"
    parent = models.ForeignKey(SurveyData, on_delete=models.CASCADE, db_constraint=False)
    event_datetime = models.DateTimeField()
    action = models.CharField(max_length=1)
    username = models.TextField()
    data = models.JSONField()


