import imageio
from django.core.files import File
import os
from django.core.files.storage import FileSystemStorage

def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    os.makedirs("media/mask", exist_ok=True)

    name = image.split('/')[-1]
    filepath = "media/mask/"+ name
    imageio.imwrite(filepath,results)
    predResult.predicted_mask = filepath
    predResult.save()
    image.status = 2
    image.save()