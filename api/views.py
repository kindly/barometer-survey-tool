import json
import os
import secrets
from urllib.parse import quote

from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from api.models import SurveyDataType, SurveyData, Survey
from api.serializers import SurveyDataSerializer, SurveySerializer
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.files.storage import default_storage
from django.urls import reverse
from django.shortcuts import redirect, render
from django.http.response import HttpResponseRedirect, HttpResponse

# Create your views here.

from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated

from rest_framework import permissions


class SurveyDataPermission(permissions.BasePermission):
    message = 'You do not have permission to view this survey'

    def has_permission(self, request, view):
        survey_object = get_object_or_404(Survey, id=view.kwargs['survey'])

        if survey_object.owner == request.user or request.user.is_staff:
            return True

        return False

class SurveyPermission(permissions.BasePermission):
    message = 'You do not have permission to view this survey'

    def has_permission(self, request, view):
        if view.action == 'create' and not request.user.is_staff:
            return False
        return True

    def has_object_permission(self, request, view, survey_object):
        if survey_object.owner == request.user or request.user.is_staff:
            return True
        return False


@login_required(login_url="/accounts/login/")
def default(request):
    with open('htdocs/index.html') as index:
        return HttpResponse(index.read())


class SurveyDataViewset(viewsets.ModelViewSet):
    serializer_class = SurveyDataSerializer
    permission_classes = [IsAuthenticated, SurveyDataPermission]

    def get_queryset(self):
        survey = self.kwargs['survey']

        survey_type = self.request.query_params.get('type', None)

        queryset = SurveyData.objects.all()

        if survey_type:
            type_object = get_object_or_404(SurveyDataType, type=survey_type)
            queryset = queryset.filter(type=type_object)

        queryset = queryset.filter(survey=survey)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)

        survey_type = self.request.query_params.get('type', None)
        if survey_type:
            type_object = get_object_or_404(SurveyDataType, type=survey_type)
            response = {}
            response['headings'] = type_object.fields
            new_data = []
            for row in serializer.data:
                row['data']['id'] = row['id']
                new_data.append(row['data'])
            response['data'] = new_data
            return Response(response)

        return Response(serializer.data)


class SurveyViewset(viewsets.ModelViewSet):
    serializer_class = SurveySerializer
    permission_classes = [IsAuthenticated, SurveyPermission]
    queryset=Survey.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        if not request.user.is_staff:
            queryset = queryset.filter(owner=request.user)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def upload_file(self, request, pk=None):
        object = get_object_or_404(self.get_queryset(), id=pk)
        self.check_object_permissions(request, object)

        file_obj = request.FILES.get('file', '')

        file_directory_within_bucket = '{pk}'.format(pk=pk)
        storage_name = secrets.token_urlsafe(5) + '-' + file_obj.name

        file_path_within_bucket = os.path.join(
            file_directory_within_bucket,
            storage_name
        )

        default_storage.save(file_path_within_bucket, file_obj)
        file_url = default_storage.url(file_path_within_bucket)

        return Response({
            'message': 'OK',
            'fileUrl': self.reverse_action(self.get_file.url_name, args=[pk]) + '?file=' + quote(storage_name)
        })

    @action(detail=True, methods=['get'])
    def get_file(self, request, pk=None):
        object = get_object_or_404(self.get_queryset(), id=pk)
        self.check_object_permissions(request, object)

        file_name = request.GET.get('file', '')

        file_directory_within_bucket = '{pk}'.format(pk=pk)

        file_path_within_bucket = os.path.join(
            file_directory_within_bucket,
            file_name
        )

        return HttpResponseRedirect(redirect_to=default_storage.url(file_path_within_bucket))
