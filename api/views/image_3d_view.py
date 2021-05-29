import numpy as np
from api.models import Gradcam, Image3D, Mask, PredictResult
from rest_framework import viewsets
from api.serializers import Image3DSerializer, PredictResultSerializer, ProjectImage3DSerializer
from .utils import check_arguments, check_staff_permission, create_log, err_not_allowed, err_no_permission, not_found, err_not_found
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from datetime import datetime
import os
import shutil

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
        if image.status >= 2:
            result = PredictResult.objects.filter(image3D=image)
            return Response(
                {
                    'image': ProjectImage3DSerializer(image, many=False).data,
                    'result': PredictResultSerializer(result, many=True).data,
                },
                status=status.HTTP_200_OK
            )
        return Response(
            {
                'image': ProjectImage3DSerializer(image, many=False).data,
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

    @action(detail=True, methods=['PUT'],)
    def verify_image(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_class', 'note'])
        if response[0] != 0:
            return response[1]
        if isinstance(request.data['actual_class'], list):
            actual_class = request.data['actual_class']
        else:
            actual_class = request.data['actual_class'].split(',')
            actual_class = list(filter(None, actual_class))
        for diag in actual_class:
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

    @action(detail=True, methods=['PUT'],)
    def verify_mask(self, request, pk=None):
        try:
            image = Image3D.objects.get(id=pk)
        except:
            return err_not_found
        try:
            user = check_staff_permission(image.project, request)
        except:
            return err_no_permission
        response = check_arguments(request.data, ['actual_mask', 'note'])
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
                if "Classification" in image.project.task:
                    gradcams = Gradcam.objects.filter(predictresult=result)
                    for gradcam in gradcams:
                        os.remove(os.path.join("media", gradcam.gradcam.name))
                else:
                    masks = Mask.objects.filter(result=result)
                    for mask in masks:
                        os.remove(os.path.join("media", mask.mask.name))
        except:
            pass
        try:
            shutil.rmtree(os.path.join("media", "image3D", image.name))
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
