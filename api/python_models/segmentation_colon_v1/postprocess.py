import cv2
from django.core.files import File
def postprocess(results,image,predResult):
    results = results.squeeze().round()
    results = (1- results)*255
    cv2.imwrite("tmp/"+ image,results)
    f= open("tmp/"+ image,'rb')
    predResult.predicted_mask = File(f)
    predResult.save()
    image.status = 2
    image.save()