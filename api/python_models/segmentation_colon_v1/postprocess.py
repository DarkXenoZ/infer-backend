import imageio
from django.core.files import File
import os

def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    os.makedirs("media/mask", exist_ok=True)

    filepath = image[0].split('/')[-1]
    imageio.imwrite(filepath,results)
    
    return filepath
