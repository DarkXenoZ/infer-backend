from celery import shared_task
from .models import *
import os
from tensorflow import keras
import numpy as np
import matplotlib.cm as cm
import PIL
import io
from django.core.files.uploadedfile import InMemoryUploadedFile

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
# To use run save_image.delay(args)
@shared_task
def save_image(project_id):
    instance = Project.objects.get(id=project_id)
    print(instance.name)

@shared_task
def infer_image(project,pipeline,image_ids):
    images = []
        image_ids = image_ids
        for img in image_ids:
            try:
                image = Image.objects.get(id=img)
                images.append((image.data8.name,image))
            except:
                return not_found(f'Image (id:{img})')

        tmp_path = os.path.join("tmp","")
        file_path = os.path.join("media","")
        os.makedirs("tmp", exist_ok=True)
        for img in images:
            output1 = subprocess.check_output(
                f"/root/claracli/clara create job -n {user.username} {project.name} -p {pipeline.pipeline_id} -f {file_path+img[0]} ", 
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
                img_nograd = img[0]
                img_io = io.BytesIO()
                img_grad = mock_heatmap(img_nograd)
                img_grad.save(img_io, format='PNG')
                result = PredictResult.objects.create(pipeline=pipeline,image=img[1])
                result.gradcam = InMemoryUploadedFile(img_io,None,img[0],'image/png',img_io.tell,charset=None)
                result.save()
            except:
                return Response(
                    {
                        "message":"This image infered with The pipeline"
                    },status=status.HTTP_400_BAD_REQUEST
                )
            q = Queue.objects.create(job=job,project=project,pipeline=pipeline,image=img[1])
            q.save()
        for img in image_ids:
            image = Image.objects.get(id=img)
            image.status = 1
            image.save()
        create_log(user=request.user,
                   desc=f"{request.user.username} infer image id  {image_ids}")
        return Response(
            {
                'message': 'Completed',
            },
            status=status.HTTP_200_OK
        )    