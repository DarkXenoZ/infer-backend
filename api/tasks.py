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

@shared_task
def make_gradcam(
    queue,
    predictResult,
    img_path
):  
    queue = Queue.objects.get(id=queue)
    pipeline = queue.pipeline
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
        
        img_io = io.BytesIO()
        superimposed_img.save(img_io, format='PNG')
        grad = InMemoryUploadedFile(img_io, None, image_path, 'image/png', img_io.tell, charset=None)
        gradcam = Gradcam.objects.create(gradcam=grad,predictresult=predictResult,predclass=queue.image.predclass)
        gradcam.save()
    except Exception as e:
        error = 'gradcam error:\n'+str(e)
        create_log(user=None, desc=error)


@shared_task
def infer_image(project,pipeline,image,user,url):
    project = Project.objects.get(id=project)
    pipeline = Pipeline.objects.get(id=pipeline)
    if "2D" in project.task:
        image = Image.objects.get(id=image)
    else:
        image = Image3D.objects.get(id=image)
    user = User.objects.get(username=user)
    tritonClient = grpcclient.InferenceServerClient(url=url)
    preprocess_module_name = f'api.python_models.{pipeline.model_name}.preprocess'
    preprocessModule = importlib.import_module(preprocess_module_name)
    util_module_name = f'api.python_models.{pipeline.model_name}.util'
    util_module = importlib.import_module(util_module_name)
    netInputname = util_module.netInputname
    netOutputname = util_module.netOutputname

    preprocessImage = preprocessModule.preprocess(os.path.join('/backend/media',image.data.name))
    netInput = grpcclient.InferInput(netInputname, preprocessImage.shape, "FP32")
    netOutputList = []
    for outputName in netOutputname:
        netOutputList.append(grpcclient.InferRequestedOutput(outputName))
    netInput.set_data_from_numpy(preprocessImage)
    Output = tritonClient.infer(model_name=pipeline.model_name, inputs=[netInput], outputs=netOutputList)

    triton_output = []
    for i in range(len(netOutputname)):
        triton_output.append(Output.as_numpy(netOutputname[i]))
    predResult = PredictResult.objects.get(pipeline=pipeline,image=image[1])
    postprocess_module_name = f'api.python_models.{pipeline.model_name}.postprocess'
    postprocessModule = importlib.import_module(postprocess_module_name)

    result = postprocessModule.postprocess(triton_output,image)
    if "Classification" in project.task:
        if len(result[0]) != len(project.predclasses):
            create_log(user, desc='Length of predclasses not equal to Length of result')
        else:
            label = dict(zip(project.predclasses,result[0]))
            pred=json.dumps(label)
            predResult.predicted_class = pred
            predResult.save()
            image.predclass = max(label,key=lambda k: label[k])
            image.status = 2
            image.save() 
        if len(result) == 2 and project.task == "2D Classification":
            for classname,filepath in result[1].items():
                grad = Gradcam()
                grad.predclass = classname
                grad.gradcam = File(open(filepath,'rb'))
                grad.predictresult = predResult
                grad.save()
                os.remove(filepath)
    elif "Segmentation" in project.task:
        mask = Mask()
        mask.result = predResult
        mask.mask = File(open(result,'rb'))
        mask.save()
        os.remove(result)
        image.status = 2
        image.save()
    
    if "2D" in project.task:
        q = Queue.objects.get(project=project,pipeline=pipeline,image=image)
    else:
        q = Queue.objects.get(project=project,pipeline=pipeline,image3d=image)
    q.delete()

@shared_task
def export(project):
    os.makedirs("tmpZipfile", exist_ok=True)
    zip_path = "/backend/tmpZipfile"
    media_path = "/backend/media"
    project = Project.objects.get(id=project)
    if "2D" in project.task:
        images = Image.objects.filter(project=project,status__gte=3)
    else:
        images = Image3D.objects.filter(project=project,status__gte=3)
    if "Classification" in project.task:
        os.makedirs(os.path.join(zip_path,"Images"), exist_ok=True)
        files_path = []
        label =[]
        for image in images:
            files_path.append(os.path.join(media_path,image.data))
            if image.status == 3:
                label.append((image.data.name,))
            else:
                label.append((image.data.name,image.actual_class))
            predResult = PredictResult.objects.filter(image=image)

    
    
    
    try:
        pipeline = Pipeline.objects.get(id=request.data['pipeline'])
    except:
        return not_found('Pipeline')
        
