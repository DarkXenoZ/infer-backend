import os
import subprocess
import psutil
from pynvml.nvml import nvmlDeviceGetHandleByIndex, nvmlDeviceGetMemoryInfo, nvmlInit
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status


class UtilViewSet(viewsets.ViewSet):
    @action(detail=False, methods=['GET'], )
    def check_usage(self, request):
        nvmlInit()
        gpu_0 = nvmlDeviceGetHandleByIndex(0)
        info = nvmlDeviceGetMemoryInfo(gpu_0)
        ram_used = psutil.virtual_memory()[2]
        return Response(
            {
                'GPU': info.used/info.total * 100,
                'MEM': ram_used
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['GET'], )
    def check_server_status(self, request):
        try:
            clara_status = subprocess.check_output(
                'kubectl get pods | grep "clara-platform" ', shell=True, encoding='UTF-8')
            clara_status = ("Running" in clara_status)
        except:
            clara_status = False
        try:
            trtis_status = subprocess.check_output(
                'docker ps | grep "deepmed_trtis" ', shell=True, encoding='UTF-8')
            trtis_status = (len(trtis_status) > 0)
        except:
            trtis_status = False
        return Response(
            {
                'trtis_status': trtis_status,
                'clara_status': clara_status
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['POST'], )
    def restart(self, request):
        subprocess.Popen(
            f'/root/claracli/clara-platform restart -y ', shell=True)
        subprocess.Popen(
            f'docker restart deepmed_trtis ', shell=True)
        return Response(
            {
                'message': "done"
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['GET'], )
    def list_local_dir(self, request):
        files_path = "/backend/data/"
        dir_name = os.listdir(files_path)
        dir_name = [path for path in dir_name if os.path.isdir(
            os.path.join(files_path, path))]
        return Response(
            {
                'dir_name': dir_name
            },
            status=status.HTTP_200_OK
        )

    @action(detail=False, methods=['GET'], )
    def list_local_files(self, request):
        files_path = "/backend/data/"
        try:
            files_path = os.path.join(files_path, request.GET.get("directory"))
        except:
            pass
        files_name = os.listdir(files_path)
        files_name = [path for path in files_name if os.path.isfile(
            os.path.join(files_path, path))]
        return Response(
            {
                'files_name': files_name
            },
            status=status.HTTP_200_OK
        )
