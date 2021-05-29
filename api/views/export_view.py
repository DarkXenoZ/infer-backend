from rest_framework import viewsets
from api.serializers import ExportSerializer
from rest_framework.response import Response
from rest_framework import status
from api.models import Export
from .utils import err_not_allowed, err_no_permission, not_found


class ExportViewSet(viewsets.ModelViewSet):
    queryset = Export.objects.all()
    serializer_class = ExportSerializer

    def retrieve(self, request, pk=None):
        try:
            export = Export.objects.get(id=pk)
        except:
            return not_found('Export')
        if not request.user.is_staff:
            return err_no_permission

        serializer_class = ExportSerializer
        return Response(serializer_class(export, many=False).data,
                        status=status.HTTP_200_OK, )

    def list(self, request):
        if not request.user.is_staff:
            return err_no_permission
        queryset = Export.objects.all()
        serializer_class = ExportSerializer
        return Response(serializer_class(queryset, many=True).data,
                        status=status.HTTP_200_OK)

    def create(self, request, pk=None):
        return err_not_allowed
