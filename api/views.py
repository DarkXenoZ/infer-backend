from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
from .serializers import *
from django.core.files.storage import FileSystemStorage
import pydicom
import imageio
from datetime import datetime
from django.core.files import File
import subprocess, os, time, json, csv,shutil,glob
from .tasks import *
from tensorflow import keras
import numpy as np
import matplotlib.cm as cm
import PIL
import io
from zipfile import ZipFile
import cv2
from pynvml import *
from django.core.files.uploadedfile import InMemoryUploadedFile
import psutil
# Create your views here.
from django.http import HttpResponse
import nrrd

err_invalid_input = Response(
    {'message': 'please recheck input fields'},
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
def not_found(Object):
    return Response(
        {'message': f'{Object} not found'},
        status=status.HTTP_404_NOT_FOUND,
    )

def create_log(user, desc):
    Log.objects.create(user=user, desc=desc)


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

def check_staff_permission(project, request):
    return request.user if request.user.is_staff else project.users.get(username=request.user.username)

class UtilViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['GET'], )    
    def check_usage(self, request):
        nvmlInit()
        h = nvmlDeviceGetHandleByIndex(0)
        info = nvmlDeviceGetMemoryInfo(h)
        RAM_used = psutil.virtual_memory()[2]
        return Response(
            {
                'GPU' : info.used/info.total * 100,
                'MEM' : RAM_used
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['GET'], )    
    def check_server_status(self, request):
        try:
            clara_status = subprocess.check_output(f'kubectl get pods | grep "clara-platform" ', shell=True, encoding='UTF-8')
            clara_status = ("Running" in clara_status)
        except:
            clara_status = False
        try:
            trtis_status = subprocess.check_output(f'docker ps | grep "deepmed_trtis" ', shell=True, encoding='UTF-8')
            trtis_status = (len(trtis_status)>0)
        except:
            trtis_status = False
        return Response(
            {
                'trtis_status' : trtis_status,
                'clara_status' : clara_status
            },
            status=status.HTTP_200_OK
        )
    
    @action(detail=False, methods=['POST'], )    
    def restart(self, request):
        clara_status = subprocess.Popen(f'/root/claracli/clara-platform restart -y ', shell=True)
        trtis_status = subprocess.Popen(f'docker restart deepmed_trtis ', shell=True)
        return Response(
            {
                'message' : "done"
            },
            status=status.HTTP_200_OK
        )


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
            'admin'
        ])
        if response[0] != 0:
            return response[1]

        username = request.data['username']
        password = request.data['password']
        first_name = request.data['first_name']
        last_name = request.data['last_name']
        email = request.data['email']
        admin = request.data['admin'] == "true"

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
            base_user.is_staff = admin
            base_user.save()
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
            return Response(
                UserSerializer(user, many=False).data,
                status=status.HTTP_200_OK
            )
        except:
            return err_not_found
    
    def update(self, request, pk=None):
        if pk != request.user.username and not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(username=pk)
            try:
                user.first_name = request.data["first_name"]
            except:
                pass
            try:
                user.last_name = request.data["last_name"]
            except:
                pass
            try:
                user.email = request.data["email"]
            except:
                pass
            try:
                user.is_staff = request.data["admin"]=="true"
            except:
                pass
            user.save()
        except:
            return err_not_found
        return Response(
                UserSerializer(user, many=False).data,
                status=status.HTTP_200_OK
            )

    @action(methods=['PUT'],detail=True)    
    def update_batch(self, request,pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            users = request.data["users"].split(',')
        except:
            return err_invalid_input
        for username in users:
            try:
                user = User.objects.get(username=username)
                try:
                    user.first_name = request.data["first_name"]
                except:
                    pass
                try:
                    user.last_name = request.data["last_name"]
                except:
                    pass
                try:
                    user.email = request.data["email"]
                except:
                    pass
                try:
                    user.is_staff = request.data["admin"]=="true"
                except:
                    pass
                user.save()
            except:
                return err_invalid_input
        queryset = User.objects.all()
        return Response(
                UserSerializer(queryset, many=True).data,
                status=status.HTTP_200_OK
            )

    def destroy(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(username=pk)
            user.delete()
        except:
            return err_not_found
        return Response(status=status.HTTP_200_OK)
    
    @action(methods=['PUT'], detail=True)
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
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if not request.user.is_staff and request.user not in project.users:
            return err_no_permission
        if "2D" in project.task:
            images = Image.objects.filter(project=project)
            imgSerializer = ImageSerializer
        else:
            images = Image3D.objects.filter(project=project)
            imgSerializer = Image3DSerializer
        status_count=[0,0,0,0]
        diag_list ={}
        for each in images:
            status_count[each.status]+=1
            if each.actual_class == None :
                pass
            else:
                diags = tuple(each.actual_class)
                for diag in diags:
                    if diag not in diag_list:
                        diag_list[diag] = 1
                    else:
                        diag_list[diag]+= 1
        total = sum(diag_list.values())
        for i in diag_list: 
            diag_list[i] = diag_list[i]/total
        pipelines = Pipeline.objects.filter(project=project)
        fstatus = {'uploaded' : status_count[0],
                'in process': status_count[1],
                'ai-annotated' : status_count[2],
                'verified' : status_count[3]}
        return Response(
            {
                'project': UserProjectSerializer(project, many=False).data,
                'predicted': diag_list,
                'pipelines': PipelineSerializer(pipelines,many=True).data,
                'status' : fstatus,
                'result' : imgSerializer(images,many=True).data,
            },
            status=status.HTTP_200_OK
        )

    
    def list(self, request):
        if request.user.is_staff:
            queryset = Project.objects.all()
        else:
            queryset = request.user.projects
        serializer_class = UserProjectSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request):
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, [
            'name',
            'description',
            'task',
            'cover',
            'predclasses'
        ])
        if response[0] != 0:
            return response[1]
        proj={}
        proj['name'] = str(request.data['name'])
        proj['description'] = request.data['description']
        proj['cover'] = request.data['cover']
        proj['task'] = request.data['task']
        proj['predclasses'] = request.data['predclasses'].split(',')
        try:
            Project.objects.get(name=proj['name'])
            return Response(
                {'message': "A project's name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            project_serializer = ProjectSerializer(data=proj)
            if project_serializer.is_valid():
                project_serializer.save() 
            else:
                return err_invalid_input  
        create_log(user=request.user,
                   desc=f"Project: {proj['name']} has been created by {request.user.username}" )
        return Response(
            {
                'message': 'The Project has been created',
                'result': (project_serializer).data,
            },
            status=status.HTTP_200_OK
        )
    
    def update(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
            try:
                project.name = request.data["name"]
            except:
                pass
            try:
                project.task = request.data["task"]
            except:
                pass
            try:
                project.description = request.data["description"]
            except:
                pass
            try:
                project.cover = request.data["cover"]
            except:
                pass
            try:
                project.predclasses = request.data["predclasses"].split(',')
            except:
                pass
        except:
            return err_not_found
        project.save()
        return Response(
                ProjectSerializer(project, many=False).data,
                status=status.HTTP_200_OK
            )
        
    def destroy(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if "2D" in project.task:
            images = Image.objects.filter(project=project)
            for image in images:
                try:
                    predResults = PredictResult.objects.filter(image=image)
                    for result in predResults:
                        if "Classification" in project.task :
                            gradcams = Gradcam.objects.filter(predictresult=result)
                            for gradcam in gradcams:
                                os.remove(os.path.join("media",gradcam.gradcam.name))
                        else:
                            masks = Mask.objects.filter(result=result)
                            for mask in masks:
                                os.remove(os.path.join("media",mask.mask.name))
                except: 
                    pass
        else:
            images = Image3D.objects.filter(project=project)
            for image in images:
                try:
                    predResults = PredictResult.objects.filter(image3D=image)
                    for result in predResults:
                        if "Classification" in project.task :
                            gradcams = Gradcam.objects.filter(predictresult=result)
                            for gradcam in gradcams:
                                os.remove(os.path.join("media",gradcam.gradcam.name))
                        else:
                            masks = Mask.objects.filter(result=result)
                            for mask in masks:
                                os.remove(os.path.join("media",mask.mask.name))
                except: 
                    pass
        project.delete()
        return Response(status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], )    
    def add_user_batch(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        response = check_arguments(request.data, ['users',])
        if response[0] != 0:
            return response[1]
        project.users.clear()
        users = request.data["users"].split(',')
        print(f"--------{users}--------")
        if users== [""]:
            project.save()
            return Response(
            {
                'message': 'set to empty',
                'result': UserProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
            )
        else:
            for username in users:
                try:
                    user = User.objects.get(username=username)
                except:
                    return not_found('Username')
                project.users.add(user)
            project.save()
            users = ', '.join(users)
            return Response(
            {
                'message': f'{users} are joined',
                'result': UserProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
            )

    @action(detail=True, methods=['GET'], )    
    def list_pipeline(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if not request.user.is_staff and request.user not in project.users:
            return err_no_permission
        try:
            pipeline = Pipeline.objects.filter(project=project)
        except:
            return not_found('Pipeline')
        return Response(
            {
                'result': PipelineSerializer(pipeline, many=True).data,
            },
            status=status.HTTP_200_OK
        )


    @action(detail=True, methods=['POST'], )    
    def add_user(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if not request.user.is_staff:
            return err_no_permission
        response = check_arguments(request.data, ['username',])
        if response[0] != 0:
            return response[1]
        try:
            user = User.objects.get(username=request.data['username'])
        except:
            return not_found('Username')
        
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
    #not used
    @action(detail=True, methods=['DELETE'], )    
    def remove_user(self, request,pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(projects=project, username=request.GET.get('username'))
        except:
            return Response(
                {'message': "This user not in the project"},
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
    @action (detail=True, methods=['POST'],)
    def add_pipeline(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            model_type = request.data['model_type']
        except:
            return not_found('model_type')
        if model_type == 'CLARA':
            response = check_arguments(
                request.data, 
                ["name","description","pipeline_id","operator","clara_pipeline_name"]
                )
        else:
            response = check_arguments(
                request.data, 
                ["name","description","model_name"]
                )
        if response[0] != 0:
            return response[1]
        try:
            Pipeline.objects.get(name= request.data['name'])
            return Response(
                {'message': 'This name already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            pass
        pipeline = Pipeline()
        pipeline.project = project
        pipeline.name = request.data['name']
        pipeline.model_type = model_type
        pipeline.description = request.data['description']
        if model_type == "CLARA":
            pipeline.operator = request.data['operator']
            pipeline.pipeline_id = request.data['pipeline_id']
            pipeline.clara_pipeline_name = request.data['clara_pipeline_name']
        else:
            pipeline.model_name = request.data['model_name']

        pipeline.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} create {pipeline.name} (pipeline) ")
        return Response(
            {
                'message': 'Pipeline created',
                'result': PipelineSerializer(pipeline, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    @action (detail=True, methods=['GET'],)
    def list_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        try:   
            queue = Queue.objects.filter(project=project)
            for q in queue:
                if q.pipeline.model_type =="CLARA":
                    check = subprocess.check_output(f"/root/claracli/clara describe job -j {q.job} ", shell=True, encoding='UTF-8')
                    line_check = check.split('\n')
                    state = (line_check[6].split(':'))[1].strip()
                    hstatus = (line_check[5].split(':'))[1].strip()
                    if project.task == "2D Classification":
                        if ("_HEALTHY" in hstatus )and("STOPPED" in state):
                            os.makedirs("tmp2d", exist_ok=True)
                            output = subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*.csv  tmp2d/", 
                                shell=True, 
                                encoding='UTF-8'
                            )
                            q.delete()    
                        file_path= f"tmp2d/{q.image.name}.csv"
                        with open(file_path, 'r') as f: 
                            csvReader = csv.reader(f) 
                            for rows in csvReader: 
                                pred = {}
                                for result in rows[1:]:
                                    diag, precision = result.split(":")
                                    pred[diag]=precision
                                max_diag = max(pred,key=lambda k: pred[k])
                                pred=json.dumps(pred)
                                name = rows[0].split("/")[-1]
                                img = q.image
                                img.predclass = max_diag
                                img.status= 2
                                img.save()
                                predResult = PredictResult.objects.get(pipeline=q.pipeline,image=img)
                                predResult.predicted_class = pred
                                predResult.save()
                        os.remove(file_path)
                        try:
                            img_io = io.BytesIO()
                            image_path = q.image.data.name
                            img_grad = make_gradcam(pipeline=pipeline, img_path=image_path)
                            img_grad.save(img_io, format='PNG')
                            grad = InMemoryUploadedFile(img_io, None, image_path, 'image/png', img_io.tell, charset=None)
                            gradcam = Gradcam.objects.create(gradcam=grad,predictresult=result,predclass=q.image.predclass)
                            gradcam.save()
                        except:
                            create_log(
                                user=user,
                                desc=f"{user.username} is unable to create Grad-CAM for image {image.data.name} on {pipeline.clara_pipeline_name} pipeline"
                            )      
                    elif project.task == "3D Classification":
                        if ("_HEALTHY" in hstatus )and("STOPPED" in state):
                            output = subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*  media/image3D/{q.image3D.name}/", 
                                shell=True, 
                                encoding='UTF-8'
                            )
                            q.delete()    
                        files_path= glob.glob(f"media/image3D/{q.image3D.name}/*.csv")
                        for file_path in files_path:
                            with open(file_path, 'r') as f: 
                                csvReader = csv.reader(f)
                                pred = {} 
                                for rows in csvReader: 
                                    pred[rows[2]] = rows[1]
                                max_diag = max(pred,key=lambda k: pred[k])
                                pred=json.dumps(pred)
                                name = rows[0].split("/")[-1]
                                img = q.image3D
                                img.predclass = max_diag
                                img.status= 2
                                img.save()
                                predResult = PredictResult.objects.get(pipeline=q.pipeline,image3D=img)
                                predResult.predicted_class = pred
                                predResult.save()
                            os.remove(file_path)
                    elif project.task == "3D Segmentation":
                        if ("_HEALTHY" in hstatus )and("STOPPED" in state):
                            os.makedirs(f"media/image3D/{q.image3D.name}/results/", exist_ok=True)
                            output = subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*  media/image3D/{q.image3D.name}/results/", 
                                shell=True, 
                                encoding='UTF-8'
                            )
                            q.delete()
                            predResult = PredictResult.objects.get(pipeline=q.pipeline,image3D=q.image3D)    
                            mask = Mask()
                            mask.result = predResult
                            img = q.image3D
                            img.status = 2
                            img.save()
                            results_path = os.path.join("media","image3D",q.image3D.name,"results")
                            maskname = img.name+".zip"
                            with ZipFile(os.path.join(maskname), 'w') as zipObj:
                                for folderName, subfolders, filenames in os.walk(results_path):
                                    for filename in filenames:
                                        filePath = os.path.join(folderName, filename)
                                        zipObj.write(filePath, os.path.basename(filePath))

                            mask.mask = File(open(os.path.join(maskname),'rb'))
                            mask.save()
                            os.remove(maskname)
                            shutil.rmtree(results_path)
                    
        except:
            pass
        if "2D" in project.task:
            return Response(ImageProjectSerializer(project, many=False).data,
            status=status.HTTP_200_OK)
        else: return Response(Image3DProjectSerializer(project, many=False).data,
            status=status.HTTP_200_OK)

    @action (detail=True, methods=['GET'],)
    def list_uninfer_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        try:
            pipeline = Pipeline.objects.get(id=request.GET.get("pipeline"))
        except:
            return not_found('Pipeline')
        if "2D" in project.task:
            list_img = Image.objects.filter(project=project).exclude(id__in=PredictResult.objects.filter(pipeline=pipeline).values_list('image__id', flat=True))
            Serializer = ImageSerializer
        else:
            list_img = Image3D.objects.filter(project=project).exclude(id__in=PredictResult.objects.filter(pipeline=pipeline).values_list('image3D__id', flat=True))
            Serializer = Image3DSerializer
        return Response(
                {
                    'result': ImageSerializer(list_img, many=True).data,
                },
                status=status.HTTP_200_OK
            )

    @action (detail=True, methods=['POST'],)
    def upload_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['dicom',])
        if response[0] != 0:
            return response[1]
        if not request.data['dicom'].name.lower().endswith('.dcm'):
            return err_invalid_input
        
        ds = pydicom.read_file(request.data['dicom'])
        imgs={}
        imgs['patient_name']= str(ds['PatientName'].value)
        imgs['patient_id'] = str(ds['PatientID'].value)
        imgs['physician_name'] = str(ds['ReferringPhysicianName'].value)
        birth = int((ds['PatientBirthDate'].value)[:4])
        imgs['patient_age'] = datetime.now().year - birth
        imgs['content_date'] = datetime.strptime(ds['ContentDate'].value,"%Y%m%d").date()
            
        img = ds.pixel_array

        png_name = request.data['dicom'].name.replace('.dcm','.png')
        imgs['name']=png_name
        imageio.imwrite(png_name, img)
            
        f= open(png_name,'rb')
        imgs['data'] = File(f)
        imgs['status'] = 0
        imgs['project'] = project.pk
        img_serializer = UploadImageSerializer(data=imgs)
        if img_serializer.is_valid():
            img_serializer.save()
            f.close()
            os.remove(png_name)    
        else:
            f.close()
            os.remove(png_name)
            return Response({'message':img_serializer.errors},) 
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {imgs['name']}")
        return Response(
                {
                    'message': 'Image uploaded',
                    'result': ImageProjectSerializer(project, many=False).data,
                },
                status=status.HTTP_200_OK
            )

    @action (detail=True, methods=['POST'],)
    def upload_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, [
            'image',
            'patient_name',
            'patient_id',
            'physician_name',
            'patient_age',
            'content_date'
            ]
        )
        if response[0] != 0:
            return response[1]
        imgs=Image()
        imgs.patient_name = request.data['patient_name']
        imgs.patient_id =  request.data['patient_id']
        imgs.physician_name =  request.data['physician_name']
        imgs.patient_age =  request.data['patient_age']
        imgs.content_date = datetime.strptime( request.data['content_date'],"%Y%m%d").date()
        imgs.data = request.data['image']
        imgs.name = request.data['image'].name
        imgs.status = 0
        imgs.project = project
        imgs.save()
        
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {imgs.name}")
        return Response(
                {
                    'message': 'Image uploaded',
                    'result': ImageProjectSerializer(project, many=False).data,
                },
                status=status.HTTP_200_OK
            )
    ###
    @action (detail=True, methods=['POST'],)
    def upload_image3D(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, [
            'image',
            'patient_name',
            'patient_id',
            'physician_name',
            'patient_age',
            'content_date'
            ]
        )
        if response[0] != 0:
            return response[1]
        imgs=Image3D()
        imgs.patient_name= request.data['patient_name']
        imgs.patient_id =  request.data['patient_id']
        imgs.physician_name =  request.data['physician_name']
        imgs.patient_age =  request.data['patient_age']
        imgs.content_date = datetime.strptime( request.data['content_date'],"%Y%m%d").date()
        imgs.name = request.data['image'].name.split('.')[0]
        imgs.data = request.data['image']
        imgs.status = 0
        imgs.project = project
        imgs.save()
        
        dcm_path = os.path.join("media","image3D",imgs.name,"dcm")
        with ZipFile("media/"+imgs.data.name, 'r') as zipObj:
            zipObj.extractall(dcm_path)
        
        return Response(
                {
                    'message': 'Image uploaded',
                    'result': Image3DProjectSerializer(project, many=False).data,
                },
                status=status.HTTP_200_OK
            )
   
    @action (detail=True, methods=['POST'],)
    def infer_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['image_ids','pipeline'])
        if response[0] != 0:
            return response[1]
        try:
            pipeline = Pipeline.objects.get(id=request.data['pipeline'])
        except:
            return not_found('Pipeline')
        if isinstance(request.data['image_ids'], list):
            image_ids = request.data['image_ids']
        else:
            image_ids = request.data['image_ids'].split(',')
            image_ids = list(filter(None,image_ids))
        images = []
        for img in image_ids:
            try:
                if "2D" in project.task:
                    image = Image.objects.get(id=img)
                    images.append((image.data.name,image))
                else:
                    image = Image3D.objects.get(id=img)
                    images.append((image.name,image))
                image.status = 1
                image.save()
            except:
                return not_found(f'Image (id:{img})')
        if pipeline.model_type == "CLARA":
            file_path = os.path.join("media","")
            for img in images:
                if "2D" in project.task:
                    filename = os.path.join(file_path,img[0])
                else:
                    filename = file_path+"image3D/"+img[0]+"/dcm/"
                output1 = subprocess.check_output(
                    f"/root/claracli/clara create job -n {user.username} {project.name} -p {pipeline.pipeline_id} -f {filename} ", 
                    shell=True, 
                    encoding='UTF-8'
                )
                line = output1.split('\n')
                job = (line[0].split(':'))[1]
                output2 = subprocess.check_output(
                    f"/root/claracli/clara start job -j {job} ",
                    shell=True,
                    encoding='UTF-8'
                )
                try:
                    if "2D" in project.task:
                        q = Queue.objects.create(job=job,project=project,pipeline=pipeline,image=img[1])
                        result = PredictResult.objects.create(pipeline=pipeline,image=img[1])
                    else:
                        q = Queue.objects.create(job=job,project=project,pipeline=pipeline,image3D=img[1])
                        result = PredictResult.objects.create(pipeline=pipeline,image3D=img[1])
                    q.save()
                    result.save()
                except:
                    return Response(
                        {
                            "message":"This image infered with The pipeline"
                        },status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            for img in images:
                if "2D" in project.task:
                    q = Queue.objects.create(project=project,pipeline=pipeline,image=img[1])
                    result = PredictResult.objects.create(pipeline=pipeline,image=img[1])
                else:
                    q = Queue.objects.create(project=project,pipeline=pipeline,image3d=img[1])
                    result = PredictResult.objects.create(pipeline=pipeline,image3d=img[1])
                q.save()
                result.save()
                infer_image(project,pipeline,img,user)
        create_log(
            user=user,
            desc=f"{user.username} infer image id  {image_ids}"
        )
        return Response(
            {
                'message': 'Completed',
            },
            status=status.HTTP_200_OK
        )
        


class PipelineViewSet(viewsets.ModelViewSet):
    queryset = Pipeline.objects.all()
    serializer_class = PipelineSerializer

    def retrieve(self, request, pk=None):
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except:
            return not_found('Pipeline')
        if not request.user.is_staff and request.user not in pipeline.project.users:
            return err_no_permission
        serializer_class = PipelineSerializer
        return Response(serializer_class(pipeline, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Pipeline.objects.all()
        serializer_class = PipelineSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        return err_not_allowed

    def update(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except:
            return not_found('Pipeline')
        try:
            try:
                pipeline.name = request.data["name"]
            except:
                pass
            try:
                pipeline.pipeline_id = request.data["pipeline_id"]
            except:
                pass
            try:
                pipeline.operator = request.data["operator"]
            except:
                pass
            try:
                pipeline.accuracy = request.data["accuracy"]
            except:
                pass
            try:
                pipeline.description = request.data["description"]
            except:
                pass
            try:
                pipeline.clara_pipeline_name = request.data["clara_pipeline_name"]
            except:
                pass
            try:
                pipeline.model_name = request.data["model_name"]
            except:
                pass
            try:
                pipeline.model_type = request.data["model_type"]
            except:
                pass
            pipeline.save()
        except:
            return err_invalid_input
        return Response(
                PipelineSerializer(pipeline, many=False).data,
                status=status.HTTP_200_OK
            )

    def destroy(self,request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except:
            return not_found('Pipeline')
        try:
            predResults = PredictResult.objects.filter(pipeline=pipeline)
            for result in predResults:
                if "Classification" in pipeline.project.task :
                    gradcams = Gradcam.objects.filter(predictresult=result)
                    for gradcam in gradcams:
                        os.remove(os.path.join("media",gradcam.gradcam.name))
                else:
                    masks = Mask.objects.filter(result=result)
                    for mask in masks:
                        os.remove(os.path.join("media",mask.mask.name))
        except: 
            pass
        pipeline.delete()
        return Response(status=status.HTTP_200_OK)


class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def retrieve(self, request, pk=None):
        try:
            image = Image.objects.get(id=pk)
        except:
            return not_found('Image')
        if not request.user.is_staff and request.user not in image.project.users:
            return err_no_permission
        if image.status >=2 :
            result = PredictResult.objects.filter(image=image)
            return Response(
            {
                'image': ProjectImageSerializer(image, many=False).data,
                'result': PredictResultSerializer(result,many=True).data,
            },
            status=status.HTTP_200_OK
        )  
        return Response(
            {
                'image':ProjectImageSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )      
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Image.objects.all()
        serializer_class = ImageSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        return err_not_allowed
    

    @action (detail=True, methods=['PUT'],)
    def verify_image(self, request, pk=None):
        try:
            image = Image.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_class','note'])
        if response[0] != 0:
            return response[1]
        if isinstance(request.data['actual_class'], list):
            actual_class = request.data['actual_class']
        else:
            actual_class = request.data['actual_class'].split(',')
            actual_class = list(filter(None,actual_class))
        for diag in actual_class :
            if diag not in image.project.predclasses:
                return not_found('predClass')
        image.actual_class = actual_class
        image.status = 3
        image.note = request.data['note']
        image.timestamp = datetime.now()
        image.verify_by = f'{user.first_name} {user.last_name}'
        image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} verify {image.data.name}")
        return Response(
            {
                'message': 'Image Verified',
                'result': ImageSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    @action (detail=True, methods=['PUT'],)
    def verify_mask(self, request, pk=None):
        try:
            image = Image.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_mask','note'])
        if response[0] != 0:
            return response[1]
        
        image.actual_mask = request.data['actual_mask']
        image.status = 3
        image.note = request.data['note']
        image.timestamp = datetime.now()
        image.verify_by = f'{user.first_name} {user.last_name}'
        image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} verify {image.name}")
        return Response(
            {
                'message': 'Image Verified',
                'result': ImageSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        try:
            image = Image.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        try:
            predResults = PredictResult.objects.filter(image=image)
            for result in predResults:
                if "Classification" in image.project.task :
                    gradcams = Gradcam.objects.filter(predictresult=result)
                    for gradcam in gradcams:
                        os.remove(os.path.join("media",gradcam.gradcam.name))
                else:
                    masks = Mask.objects.filter(result=result)
                    for mask in masks:
                        os.remove(os.path.join("media",mask.mask.name))
        except: 
            pass
        try:
            os.remove(os.path.join("media",image.actual_mask.name))
        except:
            pass
        try:
            os.remove(os.path.join("media",image.data.name))
        except:
            Response(
            {
                'message': 'Can not delete the image',
            },
            status=status.HTTP_400_BAD_REQUEST
        )        
        image.delete()
        create_log(user=request.user,
                   desc=f"{request.user.username} delete {image.name}")
        return Response(
            {
                'message': 'Image deleted',
            },
            status=status.HTTP_200_OK
        )        

class Image3DViewSet(viewsets.ModelViewSet):
    queryset = Image3D.objects.all()
    serializer_class = Image3DSerializer

    def retrieve(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return not_found('Image3D')
        if not request.user.is_staff and request.user not in image.project.users:
            return err_no_permission
        if image.status >=2 :
            result = PredictResult.objects.filter(image3D=image)
            return Response(
            {
                'image': ProjectImage3DSerializer(image, many=False).data,
                'result': PredictResultSerializer(result,many=True).data,
            },
            status=status.HTTP_200_OK
        )  
        return Response(
            {
                'image':ProjectImage3DSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )      
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Image3D.objects.all()
        serializer_class = Image3DSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        return err_not_allowed

    @action (detail=True, methods=['PUT'],)
    def verify_image(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_class','note'])
        if response[0] != 0:
            return response[1]
        if isinstance(request.data['actual_class'], list):
            actual_class = request.data['actual_class']
        else:
            actual_class = request.data['actual_class'].split(',')
            actual_class = list(filter(None,actual_class))
        for diag in actual_class :
            if diag not in image.project.predclasses:
                return not_found('predClass')
        image.actual_class = actual_class
        image.status = 3
        image.note = request.data['note']
        image.timestamp = datetime.now()
        image.verify_by = f'{user.first_name} {user.last_name}'
        image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} verify {image.name}")
        return Response(
            {
                'message': 'Image Verified',
                'result': Image3DSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    @action (detail=True, methods=['PUT'],)
    def verify_mask(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_mask','note'])
        if response[0] != 0:
            return response[1]
        image.actual_mask = request.data['actual_mask']
        image.status = 3
        image.note = request.data['note']
        image.timestamp = datetime.now()
        image.verify_by = f'{user.first_name} {user.last_name}'
        image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} verify {image.name}")
        return Response(
            {
                'message': 'Image Verified',
                'result': Image3DSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        try:
            predResults = PredictResult.objects.filter(image3D=image)
            for result in predResults:
                if "Classification" in image.project.task :
                    gradcams = Gradcam.objects.filter(predictresult=result)
                    for gradcam in gradcams:
                        os.remove(os.path.join("media",gradcam.gradcam.name))
                else:
                    masks = Mask.objects.filter(result=result)
                    for mask in masks:
                        os.remove(os.path.join("media",mask.mask.name))
        except: 
            pass
        try:
            shutil.rmtree(os.path.join("media","image3D",image.name))
        except:
            Response(
            {
                'message': 'Can not delete the image',
            },
            status=status.HTTP_400_BAD_REQUEST
        )        
        image.delete()
        create_log(user=request.user,
                   desc=f"{request.user.username} delete {image.name}")
        return Response(
            {
                'message': 'Image deleted',
            },
            status=status.HTTP_200_OK
        )        

class PredictResultViewSet(viewsets.ModelViewSet):
    queryset = PredictResult.objects.all()
    serializer_class = PredictResultSerializer

    def retrieve(self, request, pk=None):
        try:
            result = Diag.objects.get(id=pk)
        except:
            return not_found('PredictResult')
        if not request.user.is_staff and request.user not in result.pipeline.project.users:
            return err_no_permission

        serializer_class = PredictResultSerializer
        return Response(serializer_class(result, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = PredictResult.objects.all()
        serializer_class = PredictResultSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
       return err_not_allowed
