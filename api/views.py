from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from .serializers import *

# Create your views here.
from django.http import HttpResponse

err_invalid_input = Response(
    {'message': 'Cannot create user, please recheck input fields'},
    status=status.HTTP_400_BAD_REQUEST,
)
err_no_permission = Response(
    {'message': 'You do not have permission to perform this action'},
    status=status.HTTP_403_FORBIDDEN,
)
err_not_found = Response(
    {'message': 'Not found'},
    status=status.HTTP_404_NOT_FOUND,
)
err_not_allowed = Response(
    {'message': 'Operation Not Allowed'},
    status=status.HTTP_405_METHOD_NOT_ALLOWED
)


def create_log(user, desc):
    Log.objects.create(user=user, desc=desc)

def index(request):
    return HttpResponse("Hello, world. You're at the polls index.")

def check_arguments(request_arr, args):
    # check for missing arguments
    missing = []
    for arg in args:
        if arg not in request_arr:
            missing.append(arg)
    if missing:
        response = {
            'Missing argument': '%s' % ', '.join(missing),
        }
        return 1, Response(response, status=status.HTTP_400_BAD_REQUEST)
    return 0,


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def create(self, request):
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, [
            'username',
            'password',
            'first_name',
            'last_name',
            'email',
        ])
        if response[0] != 0:
            return response[1]

        username = request.data['username']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        email = request.data['email']

        try:
            User.objects.get(username=username)
            return Response(
                {'message': 'A user with identical username already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            base_user = User.objects.create_user(username=username, password=password,
                                                 first_name=first_name, last_name=last_name,
                                                 email=email)
        try:
            base_user.full_clean()
        except ValidationError as ve:
            print(ve)
            base_user.delete()
            return Response(
                str(ve),
                status=status.HTTP_400_BAD_REQUEST
            )
            # return err_invalid_input
        Token.objects.create(user=base_user)
        create_log(user=base_user,
                   desc="User %s has been created" % base_user.username)
        return Response(
            {
                'message': 'A user has been created',
                'result': UserSerializer(base_user, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = User.objects.all()
        serializer_class = UserSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def retrieve(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        queryset = User.objects.all()
        try:
            user = queryset.get(username=pk)
            serializer_class = UserSerializer
            return Response(
                serializer_class(user, many=False).data,
                status=status.HTTP_200_OK
            )
        except:
            return err_not_found

    @action(methods=['POST'], detail=True)
    def change_password(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['password', ])
        if response[0] != 0:
            return response[1]

        queryset = User.objects.all()
        serializer_class = UserSerializer
        username = pk
        password = request.data['password']

        try:
            user = queryset.get(username=username)
            user.set_password(password)
            user.save()
            return Response(
                {
                    'message': 'Password has been set',
                    'result': serializer_class(user, many=False).data
                },
                status=status.HTTP_200_OK,
            )
        except:
            return err_not_found


    @action(methods=['GET'], detail=True)
    def projects(self, request, pk=None):
        user = User.objects.get(username=pk)
        project_list = user.projects
        serializer_class = ProjectSerializer
        if len(court) == 0:
            return err_not_found
        return Response(
            serializer_class(project_list, many=True).data,
            status=status.HTTP_200_OK,
        )


class LogViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserLogSerializer

    def list(self, request):
        if request.user.is_staff:
            queryset = User.objects.all()
            serializer_class = UserLogSerializer
            return Response(serializer_class(queryset, many=True).data,
                            status=status.HTTP_200_OK, )
        try:
            queryset = request.user.logs
            serializer_class = LogSerializer
            return Response(serializer_class(queryset, many=True).data,
                            status=status.HTTP_200_OK, )
        except:
            return Response({'message': 'No log with your username is found'},
                            status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        queryset = User.objects.get(username=pk).logs
        serializer_class = LogSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self):
        return err_not_allowed


class DicomViewSet(viewsets.ModelViewSet):
    queryset = Dicom.objects.all()
    serializer_class = DicomSerializer

    def retrieve(self, request, pk=None):
        try:
            dicom = Dicom.objects.get(name=pk)
        except:
            return err_not_found

        serializer_class = DicomSerializer
        return Response(serializer_class(dicom, many=False).data,
                        status=status.HTTP_200_OK, )
    

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def retrieve(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found

        serializer_class = ProjectSerializer
        return Response(serializer_class(project, many=False).data,
                        status=status.HTTP_200_OK, )
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Project.objects.all()
        serializer_class = ProjectSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request):
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, [
            'name',
            'description',
        ])
        if response[0] != 0:
            return response[1]

        name = request.data['name']
        description = request.data['description']

        try:
            Project.objects.get(name=name)
            return Response(
                {'message': "A project's name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            new_project = Project.objects.create(name=name, description=description)
        try:
            new_project.full_clean()
        except ValidationError as ve:
            print(ve)
            new_project.delete()
            return Response(
                str(ve),
                status=status.HTTP_400_BAD_REQUEST
            )
            # return err_invalid_input
        create_log(user=request.user.username,
                   desc=f"Project: {new_project.name} has been created by {request.user.username}" )
        return Response(
            {
                'message': 'A Project has been created',
                'result': ProjectSerializer(new_project, many=False).data,
            },
            status=status.HTTP_200_OK
        )
    
