import imageio
from django.core.files import File
import os

def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    os.makedirs("media/mask", exist_ok=True)

    name = image[0].split('/')[-1]
    filepath = "media/mask/"+ name
    imageio.imwrite(filepath,results)
    if predResult.predicted_mask is None:
        predResult.predicted_mask = [f(open(filepath,'rb'))]
    else:
        predResult.predicted_mask.append(f(open(filepath,'rb')))
    predResult.save()
    image[1].status = 2
    image[1].save()