import imageio
from django.core.files import File
import os
from django.core.files.storage import FileSystemStorage

def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    os.makedirs("tmp", exist_ok=True)

    name = image.split('/')[-1]
    x=imageio.imwrite("tmp/"+ name,results)
    predResult.predicted_mask = File(open("tmp/"+ name,'rb'))
    predResult.save()
    image.status = 2
    image.save()