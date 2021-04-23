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


def create_log(user, desc):
    Log.objects.create(user=user, desc=desc)

def not_found(Object):
    return Response(
        {'message': f'{Object} not found'},
        status=status.HTTP_404_NOT_FOUND,
    )

def mock_heatmap(img):
    img = PIL.Image.open(f'/backend/media/{img}')
    img = keras.preprocessing.image.img_to_array(img)
    heatmap = np.array([[0.0, 0.0, 0.0, 0.060153835, 0.018530082, 0.056849957, 0.16076058, 0.029267874, 0.0030434672, 0.0], [0.0, 0.0059512267, 0.047316007, 0.07859445, 0.018913312, 0.036927782, 0.07784216, 0.10817002, 0.12177537, 0.024867296], [0.0, 0.16354722, 0.22757132, 0.13121466, 0.12863775, 0.16256881, 0.10592792, 0.23340452, 0.2666252, 0.108965635], [0.0, 0.24428867, 0.42464405, 0.3415501, 0.25080183, 0.375855, 0.28178853, 0.83607703, 0.55824476, 0.16685705], [0.0044645933, 0.3042568, 0.72024715, 0.37625, 0.18151519, 0.47977218, 0.3807953, 0.999577, 0.5052649, 0.08331807], [0.0, 0.33775192, 1.0, 0.33293974, 0.067387484, 0.28264478, 0.2494458, 0.89005625, 0.41658986, 0.10319072], [0.0, 0.2931178, 0.7873706, 0.27176225, 0.013725055, 0.120599546, 0.19886586, 0.67009145, 0.43396968, 0.053489015], [0.0, 0.29158726, 0.24131052, 0.047198407, 0.0073595243, 0.05067579, 0.20869419, 0.42332587, 0.39596987, 0.06153891], [0.0, 0.112134464, 0.032313444, 0.0, 0.0, 0.014626631, 0.05828855, 0.09937754, 0.20306239, 0.041879017], [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0014828686]])
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


@shared_task
def infer_image(project,pipeline,image,user):
    url = os.getenv('TRTIS_URL')
    tritonClient = grpcclient.InferenceServerClient(url=url)

    # preprocess_module_name = "python_models."+pipeline.model_name + ".preprocess"
    # print(type(preprocess_module_name),preprocess_module_name)
    # preprocessModule = importlib.import_module(preprocess_module_name)
    exec(f'"import python_models.{pipeline.model_name}.preprocess"')
    preprocessImage = preprocess.preprocess(image[0])
    netInput = grpcclient.InferInput(pipeline.netInputname, preprocessImage.shape, "FP32")
    netOutput = grpcclient.InferRequestedOutput(pipeline.netOutputName)
    netInput.set_data_from_numpy(preprocessImage)
    Output = tritonClient.infer(model_name=pipeline.model_name, inputs=[netInput], outputs=[netOutput])
    Output = Output.as_numpy(pipeline.netOutputName) # output numpy array!
    predResult = PredictResult.objects.get(pipeline=pipeline,image=image)
    
    # postprocess_module_name = "python_models."+pipeline.model_name + ".postprocess"
    # postprocessModule = importlib.import_module(postprocess_module_name)
    exec(f'"import python_models.{pipeline.model_name}.postprocess"')
    postprocess.postprocess(Output,image,predResult)
    q = Queue.objects.get(project=project,pipeline=pipeline,image=image)
    q.delete()
    create_log(user=user,
                desc=f"{user.username} infer image id  {image.id}")
    return Response(
        {
            'message': 'Completed',
        },
        status=status.HTTP_200_OK
    )