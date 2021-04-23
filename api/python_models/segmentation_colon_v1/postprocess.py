import imageio
from django.core.files import File
import os
def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    print(results)
    os.makedirs("tmp", exist_ok=True)

    name = image.split('/')[-1]
    x=imageio.imwrite("tmp/"+ name,results)
    print(x)
    f= open("tmp/"+ name,'rb')
    predResult.predicted_mask = File(f)
    predResult.save()
    image.status = 2
    image.save()