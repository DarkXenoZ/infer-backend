from api.models import PredictResult
from rest_framework import viewsets
from api.serializers import PredictResultSerializer
from .utils import err_not_allowed, err_no_permission, not_found
from rest_framework.response import Response
from rest_framework import status


class PredictResultViewSet(viewsets.ModelViewSet):
    queryset = PredictResult.objects.all()
    serializer_class = PredictResultSerializer

    def retrieve(self, request, pk=None):
        try:
            result = PredictResult.objects.get(id=pk)
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