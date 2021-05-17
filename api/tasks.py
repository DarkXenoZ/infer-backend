from celery import shared_task
from .models import *
from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.views import APIView
from django.core.exceptions import ValidationError
import subprocess, os, time, json, csv,shutil,glob
import os
import subprocess
from tensorflow import keras
import numpy as np
import matplotlib.cm as cm
import PIL
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import tritonclient.grpc as grpcclient
from django.core.files import File
import importlib
from .gradcam import GradcamModel
import json



def create_log(user, desc):
    Log.objects.create(user=user, desc=desc)

def not_found(Object):
    return Response(
        {'message': f'{Object} not found'},
        status=status.HTTP_404_NOT_FOUND,
    )

@shared_task
def make_gradcam(
    pipeline,
    img_path
):  
    try:
        img = PIL.Image.open(os.path.join('/backend/media',img_path))
        img = keras.preprocessing.image.img_to_array(img)
        preprocess_module_name = f'api.python_models.{pipeline.clara_pipeline_name}.preprocess'
        preprocessModule = importlib.import_module(preprocess_module_name)
        preprocessImage = preprocessModule.preprocess(img_path)
        gradcam_model = GradcamModel(os.path.join('/backend/api','python_models',pipeline.clara_pipeline_name,'model.trt.pb'))
        heatmap = gradcam_model.gradcam(preprocessImage)
        heatmap = np.uint8(255 * heatmap)
        jet = cm.get_cmap("jet")
        jet_colors = jet(np.arange(256))[:, :3]
        jet_heatmap = jet_colors[heatmap]
        jet_heatmap = keras.preprocessing.image.array_to_img(jet_heatmap)
        jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
        jet_heatmap = keras.preprocessing.image.img_to_array(jet_heatmap)
        superimposed_img = jet_heatmap * 0.4 + img
        superimposed_img = keras.preprocessing.image.array_to_img(superimposed_img)
        return superimposed_img
    except Exception as e:
        print('gradcam error:\n',str(e))
        return None


@shared_task
def infer_image(project,pipeline,image,user):
    url = os.getenv('TRTIS_URL')
    tritonClient = grpcclient.InferenceServerClient(url=url)

    preprocess_module_name = f'api.python_models.{pipeline.model_name}.preprocess'
    preprocessModule = importlib.import_module(preprocess_module_name)

    util_module_name = f'api.python_models.{pipeline.model_name}.util'
    util_module = importlib.import_module(util_module_name)
    netInputname = util_module.netInputname
    netOutputname = util_module.netOutputname
    
    preprocessImage = preprocessModule.preprocess(image[0])
    netInput = grpcclient.InferInput(netInputname, preprocessImage.shape, "FP32")
    netOutputList = []
    for outputName in netOutputName:
        netOutputList.append(grpcclient.InferRequestedOutput(outputName))
    netInput.set_data_from_numpy(preprocessImage)
    Output = tritonClient.infer(model_name=pipeline.model_name, inputs=[netInput], outputs=netOutputList)
    triton_output = []
    for i in range(len(netOutputName)):
        triton_output.append(results.as_numpy(netOutputName[i]))
    predResult = PredictResult.objects.get(pipeline=pipeline,image=image[1])
    
    postprocess_module_name = f'api.python_models.{pipeline.model_name}.postprocess'
    postprocessModule = importlib.import_module(postprocess_module_name)

    result = postprocessModule.postprocess(triton_output,image)

    #### เดียวมาแยก
    if "Classification" in project.task:
        if len(result[0]) != len(project.predclasses):
            return Response(
                {'message': 'Length of predclasses not equal to Length of result'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        label = dict(zip(project.predclasses,result[0]))
        pred=json.dumps(label)
        predResult.predicted_class = pred
        predResult.save()
        image[1].predclass = max(label,key=lambda k: label[k])
        image[1].status = 2
        image[1].save() 
        if len(result) == 2 and project.task == "2D Classification":
            for classname,filepath in result[1]:
                grad = Gradcam()
                grad.predclass = classname
                grad.gradcam = File(open(filepath,'rb'))
                grad.predictresult = predResult
                grad.save()
    elif "Segmentation" in project.task:
        mask = Mask()
        mask.result = predResult
        mask.mask = File(open(result,'rb'))
        mask.save()
        os.remove(result)
        image[1].status = 2
        image[1].save()
    
    if "2D" in project.task:
        q = Queue.objects.get(project=project,pipeline=pipeline,image=image[1])
    else:
        q = Queue.objects.get(project=project,pipeline=pipeline,image3d=image[1])
    q.delete()
    create_log(user=user,
                desc=f"{user.username} infer image id  {image[1].id}")
    return Response(
        {
            'message': 'Completed',
        },
        status=status.HTTP_200_OK
    )
