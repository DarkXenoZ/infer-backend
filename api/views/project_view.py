import pydicom
from api.tasks import export, infer_image, make_gradcam
import os
import csv
import json
import shutil
from rest_framework import viewsets
from django.contrib.auth.models import User
from api.serializers import Image3DProjectSerializer, Image3DSerializer, ImageProjectSerializer, ImageSerializer, PipelineSerializer, ProjectSerializer, UserProjectSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from .utils import check_staff_permission, err_no_permission, check_arguments, create_log, err_not_found, err_invalid_input, hash_file, not_found
from api.models import Gradcam, Mask, Pipeline, PredictResult, Project, Image, Image3D, Queue
import subprocess
import glob
from zipfile import ZipFile
from datetime import datetime
import imageio
from django.core.files import File


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
        status_count = [0, 0, 0, 0]
        diag_list = {}
        for each in images:
            status_count[each.status] += 1
            if each.actual_class == None:
                pass
            else:
                diags = tuple(each.actual_class)
                for diag in diags:
                    if diag not in diag_list:
                        diag_list[diag] = 1
                    else:
                        diag_list[diag] += 1
        pipelines = Pipeline.objects.filter(project=project)
        fstatus = {'uploaded': status_count[0],
                   'in process': status_count[1],
                   'ai-annotated': status_count[2],
                   'verified': status_count[3]}
        return Response(
            {
                'project': UserProjectSerializer(project, many=False).data,
                'predicted': diag_list,
                'pipelines': PipelineSerializer(pipelines, many=True).data,
                'status': fstatus,
                'result': imgSerializer(images, many=True).data,
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
        ])
        if response[0] != 0:
            return response[1]
        project = Project()
        project.name = str(request.data['name'])
        project.description = request.data['description']
        project.cover = request.data['cover']
        project.task = request.data['task']
        if "Classification" in project.task:
            try:
                project.predclasses = request.data['predclasses'].split(',')
            except:
                return err_invalid_input
        try:
            Project.objects.get(name=project.name)
            return Response(
                {'message': "A project's name already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )
        except:
            project.save()
        create_log(user=request.user,
                   desc=f"Project: {project.name} has been created by {request.user.username}")
        return Response(
            {
                'message': 'The Project has been created',
            },
            status=status.HTTP_200_OK
        )

    def update(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
            if 'name' in request.data:
                project.name = request.data["name"]
            if 'task' in request.data:
                project.task = request.data["task"]
            if 'description' in request.data:
                project.description = request.data["description"]
            if 'cover' in request.data:
                project.cover = request.data["cover"]
            if 'predclasses' in request.data:
                project.predclasses = request.data["predclasses"].split(',')
        except:
            return err_not_found
        project.save()
        return Response(
            {'message': 'Project has been updated',
             'data': ProjectSerializer(project, many=False).data},
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
                        if "Classification" in project.task:
                            gradcams = Gradcam.objects.filter(
                                predictresult=result)
                            for gradcam in gradcams:
                                os.remove(os.path.join(
                                    "media", gradcam.gradcam.name))
                        else:
                            masks = Mask.objects.filter(result=result)
                            for mask in masks:
                                os.remove(os.path.join(
                                    "media", mask.mask.name))
                except:
                    pass
        else:
            images = Image3D.objects.filter(project=project)
            for image in images:
                try:
                    predResults = PredictResult.objects.filter(image3D=image)
                    for result in predResults:
                        if "Classification" in project.task:
                            gradcams = Gradcam.objects.filter(
                                predictresult=result)
                            for gradcam in gradcams:
                                os.remove(os.path.join(
                                    "media", gradcam.gradcam.name))
                        else:
                            masks = Mask.objects.filter(result=result)
                            for mask in masks:
                                os.remove(os.path.join(
                                    "media", mask.mask.name))
                except:
                    pass
        project.delete()
        return Response({'message': 'Project has been deleted'}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['POST'], )
    def add_user_batch(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        response = check_arguments(request.data, ['users', ])
        if response[0] != 0:
            return response[1]
        project.users.clear()
        users = request.data["users"].split(',')
        print(f"--------{users}--------")
        if users == [""]:
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
                    'message': 'Users in the project have been updated',
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
        response = check_arguments(request.data, ['username', ])
        if response[0] != 0:
            return response[1]
        try:
            user = User.objects.get(username=request.data['username'])
        except:
            return not_found('Username')

        try:
            Project.objects.get(name=project.name, users=user)
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
    def remove_user(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        if not request.user.is_staff:
            return err_no_permission
        try:
            user = User.objects.get(
                projects=project, username=request.GET.get('username'))
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

    @action(detail=True, methods=['POST'],)
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
                ["name", "description", "pipeline_id",
                    "operator", "clara_pipeline_name"]
            )
        else:
            response = check_arguments(
                request.data,
                ["name", "description", "model_name"]
            )
        if response[0] != 0:
            return response[1]
        try:
            Pipeline.objects.get(name=request.data['name'])
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

    @action(detail=True, methods=['GET'],)
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
                if q.pipeline.model_type == "CLARA":
                    check = subprocess.check_output(
                        f"/root/claracli/clara describe job -j {q.job} ", shell=True, encoding='UTF-8')
                    line_check = check.split('\n')
                    state = (line_check[6].split(':'))[1].strip()
                    hstatus = (line_check[5].split(':'))[1].strip()
                    if project.task == "2D Classification":
                        if ("_HEALTHY" in hstatus) and ("STOPPED" in state):
                            os.makedirs("tmp2d", exist_ok=True)
                            subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*.csv  tmp2d/",
                                shell=True,
                                encoding='UTF-8'
                            )
                            file_path = glob.glob("tmp2d/*.csv")[0]
                            with open(file_path, 'r') as f:
                                csvReader = csv.reader(f)
                                # have only 1 row
                                for rows in csvReader:
                                    pred = {}
                                    for result in rows[1:]:
                                        diag, precision = result.split(":")
                                        pred[diag] = precision
                                    max_diag = max(pred, key=lambda k: pred[k])
                                    pred = json.dumps(pred)
                                    img = q.image
                                    img.predclass = max_diag
                                    img.status = 2
                                    img.save()
                                    predResult = PredictResult.objects.get(
                                        pipeline=q.pipeline, image=img)
                                    predResult.predicted_class = pred
                                    predResult.save()
                                    try:
                                        image_path = q.image.data.name
                                        make_gradcam.delay(
                                            queue=q.id, predictResult=predResult.id, img_path=image_path)
                                    except:
                                        create_log(
                                            user=user,
                                            desc=f"{user.username} is unable to create Grad-CAM for image {q.image.data.name} on {q.pipeline.clara_pipeline_name} pipeline"
                                        )
                            os.remove(file_path)
                        else:
                            break
                    elif project.task == "3D Classification":
                        if ("_HEALTHY" in hstatus) and ("STOPPED" in state):
                            output = subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*  media/image3D/{q.image3D.name}/",
                                shell=True,
                                encoding='UTF-8'
                            )

                            files_path = glob.glob(
                                f"media/image3D/{q.image3D.name}/*.csv")
                            for file_path in files_path:
                                with open(file_path, 'r') as f:
                                    csvReader = csv.reader(f)
                                    pred = {}
                                    for rows in csvReader:
                                        pred[rows[2]] = rows[1]
                                    max_diag = max(pred, key=lambda k: pred[k])
                                    pred = json.dumps(pred)
                                    name = rows[0].split("/")[-1]
                                    img = q.image3D
                                    img.predclass = max_diag
                                    img.status = 2
                                    img.save()
                                    predResult = PredictResult.objects.get(
                                        pipeline=q.pipeline, image3D=img)
                                    predResult.predicted_class = pred
                                    predResult.save()
                                os.remove(file_path)
                            q.delete()
                        else:
                            break
                    elif project.task == "3D Segmentation":
                        if ("_HEALTHY" in hstatus) and ("STOPPED" in state):
                            os.makedirs(
                                f"media/image3D/{q.image3D.name}/results/", exist_ok=True)
                            output = subprocess.check_output(
                                f"/root/claracli/clara download {q.job}:/operators/{q.pipeline.operator}/*  media/image3D/{q.image3D.name}/results/",
                                shell=True,
                                encoding='UTF-8'
                            )
                            predResult = PredictResult.objects.get(
                                pipeline=q.pipeline, image3D=q.image3D)
                            mask = Mask()
                            mask.result = predResult
                            img = q.image3D
                            img.status = max(2, img.status)
                            img.save()
                            results_path = os.path.join(
                                "media", "image3D", q.image3D.name, "results")
                            maskname = img.name+".zip"
                            with ZipFile(maskname, 'w') as zipObj:
                                for folderName, subfolders, filenames in os.walk(results_path):
                                    for filename in filenames:
                                        filePath = os.path.join(
                                            folderName, filename)
                                        zipObj.write(
                                            filePath, os.path.basename(filePath))

                            mask.mask = File(
                                open(os.path.join(maskname), 'rb'))
                            mask.save()
                            os.remove(maskname)
                            shutil.rmtree(results_path)
                            q.delete()
                        else:
                            break

        except:
            pass
        if "2D" in project.task:
            return Response(ImageProjectSerializer(project, many=False).data,
                            status=status.HTTP_200_OK)
        return Response(Image3DProjectSerializer(project, many=False).data,
                        status=status.HTTP_200_OK)

    @action(detail=True, methods=['GET'],)
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
            list_img = Image.objects.filter(project=project).exclude(
                id__in=PredictResult.objects.filter(pipeline=pipeline).values_list('image__id', flat=True))
            serializer = ImageSerializer
        else:
            list_img = Image3D.objects.filter(project=project).exclude(
                id__in=PredictResult.objects.filter(pipeline=pipeline).values_list('image3D__id', flat=True))
            serializer = Image3DSerializer
        return Response(
            {
                'result': serializer(list_img, many=True).data,
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'],)
    def upload_dicom(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['dicom', ])
        if response[0] != 0:
            return response[1]
        if not request.data['dicom'].name.lower().endswith('.dcm'):
            return err_invalid_input

        ds = pydicom.read_file(request.data['dicom'])
        imgs = Image()
        imgs.patient_name = str(ds['PatientName'].value)
        imgs.patient_id = str(ds['PatientID'].value)
        imgs.physician_name = str(ds['ReferringPhysicianName'].value)
        birth = int((ds['PatientBirthDate'].value)[:4])
        imgs.patient_age = datetime.now().year - birth
        imgs.content_date = datetime.strptime(
            ds['ContentDate'].value, "%Y%m%d").date()

        img = ds.pixel_array

        png_name = request.data['dicom'].name.replace('.dcm', '.png')
        imgs.name = png_name
        imageio.imwrite(png_name, img)

        f = open(png_name, 'rb')
        imgs.data = File(f)
        imgs.status = 0
        imgs.project = project
        imgs.save()
        f.close()
        imgs.encryption = hash_file(os.path.join("media", imgs.data.name))
        all_file = Image.objects.filter(project=project)
        for pj_f in all_file:
            if pj_f.encryption == imgs.encryption:
                imgs.delete()
                return Response(
                    {'message': 'A file already exists'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        imgs.save()
        os.remove(png_name)
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {imgs}")
        return Response(
            {
                'message': 'Image uploaded',
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'],)
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
        imgs = Image()
        imgs.patient_name = request.data['patient_name']
        imgs.patient_id = request.data['patient_id']
        imgs.physician_name = request.data['physician_name']
        imgs.patient_age = request.data['patient_age']
        imgs.content_date = datetime.strptime(
            request.data['content_date'], "%Y%m%d").date()
        imgs.data = request.data['image']
        imgs.name = request.data['image'].name
        imgs.status = 0
        imgs.project = project
        imgs.save()

        imgs.encryption = hash_file(os.path.join("media", imgs.data.name))
        try:
            imgs.save()
        except:
            imgs.delete()
            return Response(
                {'message': 'A file already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {imgs.name}")
        return Response(
            {
                'message': 'Image uploaded',
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'],)
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
        imgs = Image3D()
        imgs.patient_name = request.data['patient_name']
        imgs.patient_id = request.data['patient_id']
        imgs.physician_name = request.data['physician_name']
        imgs.patient_age = request.data['patient_age']
        imgs.content_date = datetime.strptime(
            request.data['content_date'], "%Y%m%d").date()
        imgs.name = request.data['image'].name.split('.')[0]
        imgs.data = request.data['image']

        imgs.status = 0
        imgs.project = project
        imgs.save()

        imgs.encryption = hash_file(os.path.join("media", imgs.data.name))
        try:
            imgs.save()
        except:
            imgs.delete()
            return Response(
                {'message': 'A file already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )
        dcm_path = os.path.join("media", "image3D", imgs.name, "dcm")
        with ZipFile("media/"+imgs.data.name, 'r') as zipObj:
            zipObj.extractall(dcm_path)
        create_log(user=request.user,
                   desc=f"{request.user.username} upload {imgs.name}")
        return Response(
            {
                'message': 'Image uploaded',
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'],)
    def upload_local(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['files_name', ])
        if response[0] != 0:
            return response[1]
        files_name = request.data['files_name']
        files_path = os.path.join("/backend", "data")
        try:
            files_path = os.path.join(files_path, request.data['directory'])
        except:
            pass
        uploaded = []
        duplicated = []
        for file_name in files_name:
            if "2D" in project.task:
                ds = pydicom.read_file(os.path.join(files_path, file_name))
                imgs = Image()
                imgs.patient_name = str(ds['PatientName'].value)
                imgs.patient_id = str(ds['PatientID'].value)
                imgs.physician_name = str(ds['ReferringPhysicianName'].value)
                birth = int((ds['PatientBirthDate'].value)[:4])
                imgs.patient_age = datetime.now().year - birth
                imgs.content_date = datetime.strptime(
                    ds['ContentDate'].value, "%Y%m%d").date()

                img = ds.pixel_array
                name = file_name
                png_name = name.replace('.dcm', '.png')

                imgs.name = png_name
                imageio.imwrite(png_name, img)

                f = open(png_name, 'rb')
                imgs.data = File(f)
                imgs.status = 0
                imgs.project = project
                imgs.save()
                f.close()
                imgs.encryption = hash_file(
                    os.path.join("media", imgs.data.name))
                try:
                    imgs.save()
                    uploaded.append(file_name)
                    create_log(user=request.user,
                               desc=f"{request.user.username} upload {imgs.name}")
                except:
                    imgs.delete()
                    duplicated.append(file_name)
                os.remove(png_name)
            elif "3D" in project.task:
                # TODO add 3D dicom and zip file
                pass
        return Response(
            {
                'message': 'Image uploaded',
                'uploaded': uploaded,
                'duplicated': duplicated
            },
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['POST'],)
    def infer_image(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['image_ids', 'pipeline'])
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
            image_ids = list(filter(None, image_ids))
        images = []
        for img in image_ids:
            try:
                if "2D" in project.task:
                    image = Image.objects.get(id=img)
                    images.append(image)
                else:
                    image = Image3D.objects.get(id=img)
                    images.append(image)
                image.status = max(1, image.status)
                image.save()
            except:
                return not_found(f'Image (id:{img})')
        if pipeline.model_type == "CLARA":
            file_path = os.path.join("media", "")
            for img in images:
                if "2D" in project.task:
                    filename = os.path.join(file_path, img.data.name)
                else:
                    filename = os.path.join(
                        file_path, "image3D", img.name, "dcm/")
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
                        q = Queue.objects.create(
                            job=job, project=project, pipeline=pipeline, image=img)
                        result = PredictResult.objects.create(
                            pipeline=pipeline, image=img)
                    else:
                        q = Queue.objects.create(
                            job=job, project=project, pipeline=pipeline, image3D=img)
                        result = PredictResult.objects.create(
                            pipeline=pipeline, image3D=img)
                    q.save()
                    result.save()
                except:
                    return Response(
                        {
                            "message": "This image infered with The pipeline"
                        }, status=status.HTTP_400_BAD_REQUEST
                    )
        else:
            for img in images:
                if "2D" in project.task:
                    q = Queue.objects.create(
                        project=project, pipeline=pipeline, image=img)
                    result = PredictResult.objects.create(
                        pipeline=pipeline, image=img)
                else:
                    q = Queue.objects.create(
                        project=project, pipeline=pipeline, image3d=img)
                    result = PredictResult.objects.create(
                        pipeline=pipeline, image3d=img)
                q.save()
                result.save()
                url = os.getenv('TRTIS_URL')
                infer_image.delay(project.id, pipeline.id,
                                  img.id, user.username, url)
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

    @action(detail=True, methods=['POST'],)
    def export(self, request, pk=None):
        try:
            project = Project.objects.get(id=pk)
        except:
            return not_found('Project')
        try:
            user = check_staff_permission(project, request)
        except:
            return err_no_permission
        export.delay(project.id)
        create_log(
            user=user,
            desc=f"{request.user.username}  export project {project.name}"
        )
        return Response(
            {
                'message': 'Completed',
            },
            status=status.HTTP_200_OK
        )
