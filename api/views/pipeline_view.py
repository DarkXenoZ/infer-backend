from api.models import Gradcam, Mask, Pipeline, PredictResult
from rest_framework import viewsets
from api.serializers import PipelineSerializer
from .utils import err_not_allowed, err_no_permission, not_found, err_invalid_input
from rest_framework.response import Response
from rest_framework import status
import os


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
            if 'name' in request.data:
                pipeline.name = request.data["name"]
            if 'pipeline_id' in request.data:
                pipeline.pipeline_id = request.data["pipeline_id"]
            if 'operator' in request.data:
                pipeline.operator = request.data["operator"]
            if 'accuracy' in request.data:
                pipeline.accuracy = request.data["accuracy"]
            if 'description' in request.data:
                pipeline.description = request.data["description"]
            if 'clara_pipeline_name' in request.data:
                pipeline.clara_pipeline_name = request.data["clara_pipeline_name"]
            if 'model_name' in request.data:
                pipeline.model_name = request.data["model_name"]
            if 'model_type' in request.data:
                pipeline.model_type = request.data["model_type"]
            pipeline.save()
        except:
            return err_invalid_input
        return Response(
            {'message': 'Pipeline has been updated',
             'data': PipelineSerializer(pipeline, many=False).data},
            status=status.HTTP_200_OK
        )

    def destroy(self, request, pk=None):
        if not request.user.is_staff:
            return err_no_permission
        try:
            pipeline = Pipeline.objects.get(id=pk)
        except:
            return not_found('Pipeline')
        try:
            predResults = PredictResult.objects.filter(pipeline=pipeline)
            for result in predResults:
                if "Classification" in pipeline.project.task:
                    gradcams = Gradcam.objects.filter(predictresult=result)
                    for gradcam in gradcams:
                        os.remove(os.path.join("media", gradcam.gradcam.name))
                else:
                    masks = Mask.objects.filter(result=result)
                    for mask in masks:
                        os.remove(os.path.join("media", mask.mask.name))
        except:
            pass
        pipeline.delete()
        return Response({'message': 'Pipeline has been deleted'}, status=status.HTTP_200_OK)
