from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from .serializers import *
from django.core.files.storage import FileSystemStorage
import subprocess
import time
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
    

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def retrieve(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        result = Result.objects.filter(project=project)

        serializer_class1 = UserProjectSerializer
        serializer_class2 = ResultNoProjectSerializer
        return Response(
            {
                'user': UserProjectSerializer(new_project, many=False).data,
                'result' : ResultNoProjectSerializer(result,many=True).data,
            },
            status=status.HTTP_200_OK
        )
    
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
        create_log(user=request.user,
                   desc=f"Project: {new_project.name} has been created by {request.user.username}" )
        return Response(
            {
                'message': 'The Project has been created',
                'result': UserProjectSerializer(new_project, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'], )    
    def change_pipeline(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['pipeline',])
        if response[0] != 0:
            return response[1]
        try:
            pipeline = Pipeline.objects.get(name=request.data['pipeline'])
        except:
            return err_not_found
        project.pipeline = pipeline
        project.save()
        return Response(
            {
                'message': 'Changed',
                'result': ProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=['POST'], )    
    def add_user(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['user',])
        if response[0] != 0:
            return response[1]
        try:
            user = User.objects.get(username=request.data['user'])
        except:
            return err_not_found
        
        try:
            Project.objects.get(name=project.name,users=user)
            return Response(
                {'message': "The user already join in a project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            project.users.add(user)
            project.save()
            return Response(
            {
                'message': f'{user.username} is joined',
                'result': UserProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )
    @action(detail=True, methods=['POST'], )    
    def remove_user(self, request,pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['user',])
        if response[0] != 0:
            return response[1]
        try:
            user = User.objects.get(projects=project, username=request.data['user'])
        except:
            return Response(
                {'message': "The user not in this project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        project.users.remove(user)
        project.save()
        return Response(
            {
                'message': f'{user.username} is left',
                'result': UserProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    @action (detail=True, methods=['GET'],)
    def list_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        try:
            dicoms = Dicom.objects.filter(projects=project)
        except:
            return Response(
                {'message': "Empty project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        serializer_class = DicomProjectSerializer
        return Response(serializer_class(project, many=False).data,
                        status=status.HTTP_200_OK)
        #add dicoom to project
    @action (detail=True, methods=['POST'],)
    def add_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['name',])
        if response[0] != 0:
            return response[1]
        try:
            dicom = Dicom.objects.get(name=request.data['name'])
        except:
            return err_not_found
        project.dicoms.add(dicom)
        project.save()
        result = Result.objects.create(project=project,dicoms=dicom,diag=None)
        result.save()
        return Response(
            {
                'message': 'Dicom added',
                'result': DicomProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )
    @action (detail=True, methods=['POST'],)
    def remove_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['name',])
        if response[0] != 0:
            return response[1]
        try:
            dicom = Dicom.objects.get(name=request.data['name'])
        except:
            return err_not_found
        result = Result.objects.get(project=project,dicoms=dicom)
        result.delete()
        project.dicoms.remove(dicom)
        project.save()
        return Response(
            {
                'message': 'Dicom deleted',
                'result': DicomProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )        
        #edit result and save
    @action (detail=True, methods=['POST'],)
    def edit_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['diag','name'])
        if response[0] != 0:
            return response[1]
        try:
            diag = Diag.objects.get(name=request.data['diag'])
        except:
            return err_not_found
        try:
            dicom = project.dicoms.get(name=request.data['name'])
        except:
            return err_not_found
        try:
            result = Result.objects.get(project=project,dicoms=dicom)
        except:
            return err_not_found
        old = result.diag
        result.diag = diag
        result.save()
            # return err_invalid_input
        create_log(user=request.user,
                   desc=f"{request.user.username} edit {dicom.name} from {old} to {result.diag} ")
        return Response(
            {
                'message': 'Dicom Uploaded',
                'result': ResultSerializer(result, many=False).data,
            },
            status=status.HTTP_200_OK
        )
        #infer not finish na ja
    @action (detail=True, methods=['POST'],)
    def infer_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(name=pk)
        except:
            return err_not_found
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['name',])
        if response[0] != 0:
            return response[1]
        try:
            dicoms = project.dicoms
        except:
            return err_not_found
        try:
            pipeline = project.pipeline
        except:
            return err_not_found
        import subprocess, os, time, json, csv

        tmp_path = "../media/tmp/"
        file_path = "../media/"
        os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
        for dicom in dicoms:
            os.symlink(file_path+dicom.data.name, tmp_path+dicom.data.name)
        output1 = subprocess.check_output(
        f"clara create job -n {request.data['name']} -p {pipeline.pipeline_id} -f {tmp_path} ", 
        shell=True, 
        encoding='UTF-8'
        )
        line = output1.split('\n')
        job = (line[0].split(':'))[1]
        output2 = subprocess.check_output(f" clara start job -j {job} ", shell=True, encoding='UTF-8')
        while True:
            check = subprocess.check_output(f" clara describe job -j {job} ", shell=True, encoding='UTF-8')
            line_check = (check.split('\n'))[9]
            status = (line_check.split(':'))[1].strip()
            if "1" in status:
                break
            else: time.sleep(1)
        output3 = subprocess.check_output(f"clara download {job}:/operators/{pipeline.name}/* {tmp_path} ", shell=True)
        for dicom in dicoms:
            os.unlink(tmp_path+dicom.data.name)
        # not completed
        csvFilePath = tmp_path+'/Names.csv'
        jsonFilePath = tmp_path+'Names.json'
        data = {} 
        with open(csvFilePath, encoding='utf-8') as csvf: 
            csvReader = csv.DictReader(csvf) 
            for rows in csvReader: 
                key = rows['No'] 
                data[key] = rows 
        with open(jsonFilePath, 'w', encoding='utf-8') as jsonf: 
            jsonf.write(json.dumps(data, indent=4))
        return Response(
            {
                'message': 'Completed',
                'result': jsonFilePath,
            },
            status=status.HTTP_200_OK
        )
        
class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer

    def retrieve(self, request, pk=None):
        try:
            pipeline = Pipeline.objects.get(name=pk)
        except:
            return err_not_found

        serializer_class = PipelineSerializer
        return Response(serializer_class(pipeline, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        queryset = Pipeline.objects.all()
        serializer_class = PipelineSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        response = check_arguments(request.data, ['name','id'])
        if response[0] != 0:
            return response[1]
        
        name = request.data['name']
        pipeline_id = request.data['id']
        try:
            Pipeline.objects.get(name=name)
            return Response(
                {'message': 'This name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            pass
        try:
            Pipeline.objects.get(pipeline_id=pipeline_id)
            return Response(
                {'message': 'This pipeline_id already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            pipeline = Pipeline.objects.create(name=name,pipeline_id=pipeline_id)
        try:
            pipeline.full_clean()
        except ValidationError as ve:
            print(ve)
            pipeline.delete()
            return Response(
                str(ve),
                status=status.HTTP_400_BAD_REQUEST
            )
            # return err_invalid_input
        create_log(user=request.user,
                   desc=f"{request.user.username} create {pipeline.name} (pipeline) ")
        return Response(
            {
                'message': 'Pipeline created',
                'result': PipelineSerializer(pipeline, many=False).data,
            },
            status=status.HTTP_200_OK
        )    
    

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
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Dicom.objects.all()
        serializer_class = DicomSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        response = check_arguments(request.data, ['name','data',])
        if response[0] != 0:
            return response[1]
        
        name = request.data['name']
        data = request.data['data'] 
        try:
            Dicom.objects.get(name=name)
            return Response(
                {'message': 'This name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            dicom = Dicom.objects.create(name=name,data=data)
        try:
            dicom.full_clean()
        except ValidationError as ve:
            print(ve)
            dicom.delete()
            return Response(
                str(ve),
                status=status.HTTP_400_BAD_REQUEST
            )
            # return err_invalid_input
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {dicom.name} (dicom)  ")
        return Response(
            {
                'message': 'Dicom Uploaded',
                'result': DicomSerializer(dicom, many=False).data,
            },
            status=status.HTTP_200_OK
        )

class DiagViewSet(viewsets.ModelViewSet):
    queryset = Diag.objects.all()
    serializer_class = DiagSerializer

    def retrieve(self, request, pk=None):
        try:
            diag = Diag.objects.get(name=pk)
        except:
            return err_not_found

        serializer_class = DiagSerializer
        return Response(serializer_class(diag, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        queryset = Diag.objects.all()
        serializer_class = DiagSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        response = check_arguments(request.data, ['name',])
        if response[0] != 0:
            return response[1]
        
        name = request.data['name']
        try:
            Diag.objects.get(name=name)
            return Response(
                {'message': 'This name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            diag = Diag.objects.create(name=name)
        try:
            diag.full_clean()
        except ValidationError as ve:
            print(ve)
            diag.delete()
            return Response(
                str(ve),
                status=status.HTTP_400_BAD_REQUEST
            )
            # return err_invalid_input
        create_log(user=request.user,
                   desc=f"{request.user.username} create {diag.name} (diag) ")
        return Response(
            {
                'message': 'Diag created',
                'result': DiagSerializer(diag, many=False).data,
            },
            status=status.HTTP_200_OK
        )    
