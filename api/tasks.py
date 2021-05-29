from celery import shared_task
from .models import *
import os
import json
import csv
import shutil
import os
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
from zipfile import ZipFile


def create_log(user, desc):
    Log.objects.create(user=user, desc=desc)


@shared_task
def make_gradcam(
    queue,
    predictResult,
    img_path
):
    queue = Queue.objects.get(id=queue)
    predictResult = PredictResult.objects.get(id=predictResult)
    pipeline = queue.pipeline
    predclass = queue.image.predclass
    queue.delete()
    try:
        img = PIL.Image.open(os.path.join('/backend/media', img_path))
        img = keras.preprocessing.image.img_to_array(img)
        preprocess_module_name = f'api.python_models.{pipeline.clara_pipeline_name}.preprocess'
        preprocessModule = importlib.import_module(preprocess_module_name)
        preprocessImage = preprocessModule.preprocess(img_path)
        gradcam_model = GradcamModel(os.path.join(
            '/backend/api', 'python_models', pipeline.clara_pipeline_name, 'model.trt.pb'))
        heatmap = gradcam_model.gradcam(preprocessImage)
        heatmap = np.uint8(255 * heatmap)
        jet = cm.get_cmap("jet")
        jet_colors = jet(np.arange(256))[:, :3]
        jet_heatmap = jet_colors[heatmap]
        jet_heatmap = keras.preprocessing.image.array_to_img(jet_heatmap)
        jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
        jet_heatmap = keras.preprocessing.image.img_to_array(jet_heatmap)
        superimposed_img = jet_heatmap * 0.4 + img
        superimposed_img = keras.preprocessing.image.array_to_img(
            superimposed_img)

        img_io = io.BytesIO()
        superimposed_img.save(img_io, format='PNG')
        grad = InMemoryUploadedFile(
            img_io, None, img_path, 'image/png', img_io.tell, charset=None)
        gradcam = Gradcam.objects.create(
            gradcam=grad, predictresult=predictResult, predclass=predclass)
        gradcam.save()
    except Exception as e:
        error = 'gradcam error:\n'+str(e)
        create_log(user=None, desc=error)


@shared_task
def infer_image(project, pipeline, image, user, url):
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

    preprocessImage = preprocessModule.preprocess(
        os.path.join('/backend/media', image.data.name))
    netInput = grpcclient.InferInput(
        netInputname, preprocessImage.shape, "FP32")
    netOutputList = []
    for outputName in netOutputname:
        netOutputList.append(grpcclient.InferRequestedOutput(outputName))
    netInput.set_data_from_numpy(preprocessImage)
    Output = tritonClient.infer(model_name=pipeline.model_name, inputs=[
                                netInput], outputs=netOutputList)

    triton_output = []
    for i in range(len(netOutputname)):
        triton_output.append(Output.as_numpy(netOutputname[i]))
    predResult = PredictResult.objects.get(pipeline=pipeline, image=image)
    postprocess_module_name = f'api.python_models.{pipeline.model_name}.postprocess'
    postprocessModule = importlib.import_module(postprocess_module_name)

    result = postprocessModule.postprocess(triton_output, image)
    if "Classification" in project.task:
        if len(result[0]) != len(project.predclasses):
            create_log(
                user, desc='Length of predclasses not equal to Length of result')
        else:
            label = dict(zip(project.predclasses, result[0]))
            pred = json.dumps(label)
            predResult.predicted_class = pred
            predResult.save()
            image.predclass = max(label, key=lambda k: label[k])
            image.status = 2
            image.save()
        if len(result) == 2 and project.task == "2D Classification":
            for classname, filepath in result[1].items():
                grad = Gradcam()
                grad.predclass = classname
                grad.gradcam = File(open(filepath, 'rb'))
                grad.predictresult = predResult
                grad.save()
                os.remove(filepath)
    elif "Segmentation" in project.task:
        mask = Mask()
        mask.result = predResult
        mask.mask = File(open(result, 'rb'))
        mask.save()
        os.remove(result)
        image.status = 2
        image.save()

    if "2D" in project.task:
        q = Queue.objects.get(project=project, pipeline=pipeline, image=image)
    else:
        q = Queue.objects.get(
            project=project, pipeline=pipeline, image3d=image)
    q.delete()


@shared_task
def export(project):
    os.makedirs("tmpZipfile", exist_ok=True)
    zip_path = "/backend/tmpZipfile"
    media_path = "/backend/media"
    project = Project.objects.get(id=project)
    if "2D" in project.task:
        images = Image.objects.filter(project=project, status__gte=2)
    else:
        images = Image3D.objects.filter(project=project, status__gte=2)
    if "Classification" in project.task:
        os.makedirs(os.path.join(zip_path, "Images"), exist_ok=True)
        labels = []
        for image in images:
            shutil.copyfile(
                os.path.join(media_path, image.data.name),
                os.path.join(zip_path, "Images",
                             os.path.basename(image.data.name))
            )
            if image.status == 2:
                labels.append((os.path.basename(image.data.name), ""))
            else:
                labels.append(
                    (os.path.basename(image.data.name), image.actual_class))
        # make csv
        with open(os.path.join(zip_path, "label.csv"), 'w', newline='') as csvfile:
            fieldnames = ['filename', 'class']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for filename, label in labels:
                writer.writerow({'filename': filename, 'class': label})
        # Gradcam
        if "2D" in project.task:
            os.makedirs(os.path.join(zip_path, "Gradcam"), exist_ok=True)
            pipelines = Pipeline.objects.filter(project=project)
            for pipeline in pipelines:
                predResults = PredictResult.objects.filter(pipeline=pipeline)
                os.makedirs(os.path.join(zip_path, "Gradcam",
                                         pipeline.name), exist_ok=True)
                for predResult in predResults:
                    grads = Gradcam.objects.filter(predictresult=predResult)
                    for grad in grads:
                        shutil.copyfile(
                            os.path.join(media_path, grad.gradcam.name),
                            os.path.join(zip_path, "Gradcam", pipeline.name,
                                         os.path.basename(grad.gradcam.name))
                        )

    elif "Segmentation" in project.task:
        os.makedirs(os.path.join(zip_path, "Images"), exist_ok=True)
        os.makedirs(os.path.join(zip_path, "Mask"), exist_ok=True)
        labels = []
        for image in images:
            shutil.copyfile(
                os.path.join(media_path, image.data.name),
                os.path.join(zip_path, "Images",
                             os.path.basename(image.data.name))
            )
            if image.status == 2:
                labels.append((os.path.basename(image.data.name), ""))
            else:
                shutil.copyfile(
                    os.path.join(media_path, image.actual_mask.name),
                    os.path.join(zip_path, "Mask", os.path.basename(
                        image.actual_mask.name))
                )
                labels.append((os.path.basename(image.data.name),
                               os.path.basename(image.actual_mask.name)))
        # make csv
        with open(os.path.join(zip_path, "label.csv"), 'w', newline='') as csvfile:
            fieldnames = ['filename', 'mask']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for filename, mask in labels:
                writer.writerow({'filename': filename, 'mask': mask})
    # zipfile
    zip_name = f"{project.name}.zip"
    with ZipFile(zip_name, 'w') as zipObj:
        for folderName, subfolders, filenames in os.walk(zip_path):
            for filename in filenames:
                filePath = os.path.join(folderName, filename)
                zipObj.write(filePath, "/".join(filePath.split('/')[3:]))
    # Save
    try:
        export_file = Export.objects.get(project=project)
    except:
        export_file = Export()
        export_file.project = project
    export_file.zip_file = File(open(zip_name, 'rb'))
    export_file.save()

    os.remove(zip_name)
    shutil.rmtree(zip_path)
