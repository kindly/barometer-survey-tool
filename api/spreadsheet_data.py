import api.spreadsheet_actions
from api.models import QuestionData, SurveyData, Survey, SurveyDataType

from django.db import transaction


@transaction.atomic
def import_question_data(spreadsheet, overwrite=True):

    if not spreadsheet:
        return
    if not overwrite and QuestionData.objects.exists():
        return

    spreadsheet_data = api.spreadsheet_actions.sheets_data(spreadsheet)

    QuestionData.objects.all().delete()

    type_count = {}
    for type, value in spreadsheet_data.items():
        for item in value["records"]:
            obj = QuestionData(type=type, data=item)
            obj.save()
        type_count[type] = value["count"]

    return type_count


@transaction.atomic
def import_survey_data(spreadsheet, user):

    spreadsheet_data = api.spreadsheet_actions.sheets_data(spreadsheet)

    survey_types = [item.type for item in SurveyDataType.objects.all()]

    survey = Survey(owner=user, control={})
    survey.save()

    output = {}

    type_count = {}
    for sheet_name, value in spreadsheet_data.items():
        if sheet_name not in survey_types:
            continue

        for item in value["records"]:
            obj = SurveyData(
                survey=survey,
                type=SurveyDataType.objects.get(type=sheet_name),
                data=item,
            )
            type_count[sheet_name] = value["count"]
            obj.save()

    output["row_count"] = type_count
    output["id"] = survey.id

    return output
