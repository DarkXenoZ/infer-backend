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
import subprocess, os, time, json, csv

# Create your views here.
from django.http import HttpResponse

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


    @action(methods=['GET'], detail=True)
    def projects(self, request, pk=None):
        user = User.objects.get(username=pk)
        project_list = user.projects
        serializer_class = ProjectSerializer
        if len(project_list) == 0:
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
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        images = Image.objects.filter(project=project)
        diag_list ={}
        status_count=[0,0,0,0]
        for each in images:
            status_count[each.status]+=1
            if each.actual_class == '' :
                pass
            else:
                diag = each.actual_class
                if diag not in diag_list:
                    diag_list[diag] = 1
                else:
                    diag_list[diag]+= 1
        total = sum(diag_list.values())
        for i in diag_list: 
            diag_list[i] = diag_list[i]/total
        
        return Response(
            {
                'project': UserProjectSerializer(project, many=False).data,
                'predicted': diag_list,
                'uploaded' : status_count[0],
                'in process': status_count[1],
                'ai-annotated' : status_count[2],
                'verified' : status_count[3],
                'result' : ImageSerializer(images,many=True).data,
            },
            status=status.HTTP_200_OK
        )
    
    def list(self, request):
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
            'task',
            'cover',
            'predclasses'
        ])
        if response[0] != 0:
            return response[1]

        name = str(request.data['name'])
        # description = request.data['description']
        # cover = request.data['cover']
        # task = request.data['task']
        # pred = request.data['predClasses']
 
        try:
            Project.objects.get(name=name)
            return Response(
                {'message': "A project's name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            project_serializer = ProjectSerializer(data=request.data)
            if project_serializer.is_valid():
                project_serializer.save() 
            else:
                return err_invalid_input  
        create_log(user=request.user,
                   desc=f"Project: {name} has been created by {request.user.username}" )
        return Response(
            {
                'message': 'The Project has been created',
                'result': (project_serializer).data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['GET'], )    
    def list_pipeline(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
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
    @action(detail=True, methods=['DELETE'], )    
    def remove_user(self, request,pk=None):
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
            user = User.objects.get(projects=project, username=request.data['username'])
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
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        response = check_arguments(request.data, ['name','pipeline_id','description','operator'])
        if response[0] != 0:
            return response[1]
        
        name = request.data['name']
        pipeline_id = request.data['pipeline_id']
        desc = request.data['description']
        operator = request.data['operator']
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
            pipeline = Pipeline.objects.create(name=name,pipeline_id=pipeline_id,description=desc,project=project,operator=operator)
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

    @action (detail=True, methods=['GET'],)
    def list_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        try:
            images = Image.objects.filter(project=project)
        except:
            return Response(
                {'message': "Empty project"},
                status=status.HTTP_400_BAD_REQUEST
            )
        try:
            images_in_process = Image.objects.filter(project=project,status=1)
            queue = Queue.objects.filter(project=project)
            for q in queue:
                check = subprocess.check_output(f"sudo clara describe job -j {job} ", shell=True, encoding='UTF-8')
                line_check = (check.split('\n'))[9]
                state = (line_check.split(':'))[1].strip()
                if "1" in status:
                    output = subprocess.check_output(
                        f"sudo clara download {q.job}:/operators/{pipeline.operator}/*.csv  tmp.csv", 
                        shell=True, 
                        encoding='UTF-8'
                    )
                    with open("tmp.csv", 'r') as f: 
                        csvReader = csv.reader(f) 
                        for rows in csvReader: 
                            pred = {}
                            for result in rows[1:]:
                                diag, precision = result.split(":")
                                pred[diag]=precision
                            pred=json.dumps(pred)
                            name = rows[0].split("/")[-1]
                            img = Image.objects.get(name=name)
                            img.status= 2
                            img.save()
                            predResult = PredictResult.objects.create(predicted_class=pred,pipeline=pipeline,image=img)
                            predResult.save()
                    os.remove("tmp.csv")
            return Response(ImageProjectSerializer(project, many=False).data,
                        status=status.HTTP_200_OK)
        except:
            return Response(ImageProjectSerializer(project, many=False).data,
                        status=status.HTTP_200_OK)

    @action (detail=True, methods=['POST'],)
    def upload_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = project.users.get(username=request.user.username)
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
        imgs['data8'] = File(f)
        imgs['data16'] = File(f)
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
            user = project.users.get(username=request.user.username)
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
        imgs={}
        imgs['patient_name']= request.data['patient_name']
        imgs['patient_id'] =  request.data['patient_id']
        imgs['physician_name'] =  request.data['physician_name']
        imgs['patient_age'] =  request.data['patient_age']
        imgs['content_date'] = datetime.strptime( request.data['content_date'],"%Y%m%d").date()
        imgs['data8'] = request.data['image']
        imgs['data16'] = request.data['image']
        imgs['name'] = request.data['image'].name
        imgs['status'] = 0
        imgs['project'] = project.pk
        img_serializer = UploadImageSerializer(data=imgs)
        if img_serializer.is_valid():
            img_serializer.save() 
        else:
            return Response({'message':img_serializer.errors},) 
        return Response(
                {
                    'message': 'Image uploaded',
                    'result': ImageProjectSerializer(project, many=False).data,
                },
                status=status.HTTP_200_OK
            )

    @action (detail=True, methods=['DELETE'],)
    def remove_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['id',])
        if response[0] != 0:
            return response[1]
        try:
            image = Image.objects.get(id=request.data['id'])
        except:
            return not_found('Image')
        image.delete()
        return Response(
            {
                'message': 'Image deleted',
                'result': ImageProjectSerializer(project, many=False).data,
            },
            status=status.HTTP_200_OK
        )        
        #edit result and save
    @action (detail=True, methods=['PUT'],)
    def verify_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['id','actual_class','note'])
        if response[0] != 0:
            return response[1]
        try:
            image = Image.objects.get(id=request.data['id'])
        except:
            return err_not_found
        if request.data['actual_class'] not in project.predclasses:
            return not_found('predClass')
        image.actual_class = request.data['actual_class']
        image.status = 3
        image.timestamp = datetime.now()
        image.verify_by = f'{user.first_name} {user.last_name}'
        image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} verify {image.data8.name}")
        return Response(
            {
                'message': 'Image Verified',
                'result': ImageSerializer(image, many=False).data,
            },
            status=status.HTTP_200_OK
        )
        #infer not finish na ja
    @action (detail=True, methods=['POST'],)
    def infer_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = project.users.get(username=request.user.username)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['image_ids',])
        if response[0] != 0:
            return response[1]
        try:
            pipeline = Pipeline.objects.filter(project=project)
        except:
            return not_found('Pipeline')
        images = []
        image_ids = request.data['image_ids']
        for img in image_ids:
            try:
                image = Image.objects.get(id=img)
                images.append(image.data8.name)
            except:
                return not_found(f'Image (id:{img})')

        tmp_path = os.path.join("tmp","")
        file_path = os.path.join("..","media","")
        os.makedirs("tmp", exist_ok=True)
        for img in images:
            img_name = img.split('/')[-1]
            os.symlink(file_path+img, tmp_path+img_name)
        output1 = subprocess.check_output(
            f"sudo clara create job -n {user.username} {project.name} -p {project.pipeline.pipeline_id} -f {tmp_path} ", 
            shell=True, 
            encoding='UTF-8'
        )
        line = output1.split('\n')
        job = (line[0].split(':'))[1]
        output2 = subprocess.check_output(
            f"sudo clara start job -j {job} ",
            shell=True,
            encoding='UTF-8'
        )
        q = Queue.objects.create(job=job,project=project,pipeline=pipeline)
        q.save()
        for img in images:
            os.unlink(tmp_path+img)
        for img in image_ids:
            image = Image.objects.get(id=img)
            image.status = 1
            image.save()

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

        serializer_class = PipelineSerializer
        return Response(serializer_class(pipeline, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        queryset = Pipeline.objects.all()
        serializer_class = PipelineSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        return err_not_allowed
    

class ImageViewSet(viewsets.ModelViewSet):
    queryset = Image.objects.all()
    serializer_class = ImageSerializer

    def retrieve(self, request, pk=None):
        try:
            image = Image.objects.get(id=pk)
        except:
            return not_found('Image')
        if image.status >=2 :
            result = PredictResult.objects.get(image=image)
            return Response(
            {
                'image': ImageSerializer(image, many=False).data,
                'result': PredictResultSerializer(result, many=False).data,
            },
            status=status.HTTP_200_OK
        )  
        return Response(ImageSerializer(image, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Image.objects.all()
        serializer_class = ImageSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
        return err_not_allowed
    

class PredictResultViewSet(viewsets.ModelViewSet):
    queryset = PredictResult.objects.all()
    serializer_class = PredictResultSerializer

    def retrieve(self, request, pk=None):
        try:
            result = Diag.objects.get(id=pk)
        except:
            return not_found('PredictResult')

        serializer_class = PredictResultSerializer
        return Response(serializer_class(result, many=False).data,
                        status=status.HTTP_200_OK, )       
    
    def list(self, request):
        queryset = PredictResult.objects.all()
        serializer_class = PredictResultSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)
    
    def create(self, request, pk=None):
       return err_not_allowed