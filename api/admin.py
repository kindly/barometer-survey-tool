from django.contrib import admin
from django.db import models
from django_json_widget.widgets import JSONEditorWidget
# Register your models here.

from api.models import Survey, SurveyData, SurveyDataType


@admin.register(Survey, SurveyDataType)
class SurveyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }

@admin.register(SurveyData)
class SurveyAdmin(admin.ModelAdmin):
    formfield_overrides = {
        models.JSONField: {'widget': JSONEditorWidget},
    }
