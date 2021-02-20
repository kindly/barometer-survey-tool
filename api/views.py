import json
import os
import secrets
import hashlib
from urllib.parse import quote

from django.http import JsonResponse
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from django.conf import settings
from api.models import SurveyDataType, SurveyData, Survey, QuestionData
from api.serializers import (
    SurveyDataTypeSerializer,
    SurveyDataSerializer,
    SurveySerializer,
    QuestionDataSerializer,
)

from api.spreadsheet_data import import_question_data, import_survey_data

from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.files.storage import default_storage
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http.response import HttpResponseRedirect, HttpResponse
from django.db.models import Count
from django.db.models import Q

# Create your views here.

from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

from rest_framework import permissions


def check_user_queryset(user, survey_id=None):

    control_data_type = SurveyDataType.objects.filter(type="Control").first()
    if not control_data_type:
        return SurveyData.objects.none()

    hashed_email = hashlib.md5(user.email.encode()).hexdigest()

    queryset = SurveyData.objects.all()
    if survey_id:
        queryset = queryset.filter(survey_id=survey_id)

    queryset = queryset.filter(type=control_data_type)
    queryset = queryset.filter(
        Q(data__contains={"Field": "Researcher", "Value": hashed_email})
        | Q(data__contains={"Field": "Reviewer", "Value": hashed_email})
    )
    return queryset


class StaffOnlyWrite(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.is_staff:
            return True

        return False


class SurveyDataTypePermission(StaffOnlyWrite):
    message = "You do not have permission to edit Survey Data Types"


class QuestionDataPermission(StaffOnlyWrite):
    message = "You do not have permission to edit Question Data"


class SurveyDataPermission(permissions.BasePermission):
    message = "You do not have permission to view this survey"

    def has_permission(self, request, view):

        survey_object = get_object_or_404(Survey, id=view.kwargs["survey"])

        queryset = check_user_queryset(request.user, view.kwargs["survey"])

        if queryset.first():
            print("found")
            return True

        if request.user.is_staff:
            return True

        return False


class SurveyPermission(permissions.BasePermission):
    message = "You do not have permission to view this survey"

    def has_permission(self, request, view):
        if (
            view.action in ("create", "upload_spreadsheet")
            and not request.user.is_staff
        ):
            return False
        return True

    def has_object_permission(self, request, view, survey_object):
        queryset = check_user_queryset(request.user, survey_object.id)

        if queryset.first():
            return True

        if request.user.is_staff:
            return True

        return False


@login_required(login_url="/accounts/login/")
def default(request, a=None, b=None):
    with open("htdocs/index.html") as index:
        return HttpResponse(index.read())


class SurveyDataViewset(viewsets.ModelViewSet):
    serializer_class = SurveyDataSerializer
    permission_classes = [IsAuthenticated, SurveyDataPermission]
    queryset = SurveyData.objects.all()

    def get_queryset(self):
        survey = self.kwargs["survey"]

        survey_type = self.request.query_params.get("type", None)

        queryset = SurveyData.objects.all()

        if survey_type:
            type_object = get_object_or_404(SurveyDataType, type=survey_type)
            queryset = queryset.filter(type=type_object)

        queryset = queryset.filter(survey=survey)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        survey_type = self.request.query_params.get("type", None)
        if survey_type:
            serializer = self.get_serializer(queryset, many=True)
            type_object = get_object_or_404(SurveyDataType, type=survey_type)
            response = {}
            response["headings"] = type_object.fields
            response["data"] = serializer.data
            return Response(response)

        output = {}
        for type_object in SurveyDataType.objects.all():
            type_queryset = queryset.filter(type_id=type_object.id)
            serializer = self.get_serializer(queryset, many=True)
            type_output = {}
            type_output["headings"] = type_object.fields
            type_output["data"] = serializer.data
            output[type_object.type] = type_output

        return Response(output)

    def get_serializer(self, *args, **kwargs):
        serializer_class = self.get_serializer_class()
        kwargs.setdefault("context", self.get_serializer_context())
        if self.action == "update":
            kwargs["partial"] = True

        return serializer_class(*args, **kwargs)


class SurveyViewset(viewsets.ModelViewSet):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated, SurveyPermission]
    queryset = Survey.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if request.user.is_staff:
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        results = []

        for survey_data_object in check_user_queryset(self.request.user):
            serializer = self.get_serializer(survey_data_object.survey)
            results.append(serializer.data)

        return Response(results)

    @action(detail=True, methods=["post"])
    def upload_file(self, request, pk=None):
        object = get_object_or_404(self.get_queryset(), id=pk)
        self.check_object_permissions(request, object)

        file_obj = request.FILES.get("file", "")

        file_directory_within_bucket = "{pk}".format(pk=pk)
        storage_name = secrets.token_urlsafe(5) + "-" + file_obj.name

        file_path_within_bucket = os.path.join(
            file_directory_within_bucket, storage_name
        )

        default_storage.save(file_path_within_bucket, file_obj)
        file_url = default_storage.url(file_path_within_bucket)

        return Response(
            {
                "message": "OK",
                "fileUrl": self.reverse_action(self.get_file.url_name, args=[pk])
                + "?file="
                + quote(storage_name),
            }
        )

    @action(detail=True, methods=["get"])
    def get_file(self, request, pk=None):
        object = get_object_or_404(self.get_queryset(), id=pk)
        self.check_object_permissions(request, object)

        file_name = request.query_params.get("file", "")

        file_directory_within_bucket = "{pk}".format(pk=pk)

        file_path_within_bucket = os.path.join(file_directory_within_bucket, file_name)

        return HttpResponseRedirect(
            redirect_to=default_storage.url(file_path_within_bucket)
        )

    @action(detail=False, methods=["get"])
    def upload_spreadsheet(self, request):
        spreadsheet = request.query_params.get("spreadsheet")
        if not spreadsheet:
            return Response(
                {
                    "message": "Need to supply speadsheet url paramenter",
                },
                status=400,
            )

        email = request.query_params.get("email")
        if email:
            user = get_object_or_404(User, email=email)
        else:
            user = request.user

        results = import_survey_data(user=user, spreadsheet=spreadsheet)

        results["_url"] = self.reverse_action("detail", args=[results["id"]])

        return Response(results)


class SurveyDataTypeViewset(viewsets.ModelViewSet):
    serializer_class = SurveyDataTypeSerializer
    permission_classes = [IsAuthenticated, SurveyDataTypePermission]
    queryset = SurveyDataType.objects.all()


class QuestionDataViewset(viewsets.ModelViewSet):
    serializer_class = QuestionDataSerializer
    permission_classes = [IsAuthenticated, QuestionDataPermission]
    queryset = QuestionData.objects.all()

    @action(detail=False, methods=["get"])
    def list_types(self, request):
        QuestionData.objects.all()
        results = []
        for item in QuestionData.objects.values("type").annotate(
            type_count=Count("type")
        ):
            results.append(item)

        return Response(results)

    @action(detail=False, methods=["get"])
    def upload_spreadsheet(self, request):
        results = import_question_data(settings.SURVEY_QUESTIONS_SHEET)
        return Response(results)

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        question_type = request.query_params.get("type")
        if question_type:
            queryset = queryset.filter(type=question_type)
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)

        output = {}

        QuestionData.objects.all()
        for item in QuestionData.objects.values("type").annotate(
            type_count=Count("type")
        ):
            type = item["type"]
            type_queryset = queryset.filter(type=type)
            serializer = self.get_serializer(type_queryset, many=True)
            output[type] = serializer.data

        return Response(output)
