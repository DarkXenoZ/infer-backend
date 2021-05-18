import imageio
import os

def postprocess(triton_output,image):
    results = triton_output[0]
    results = results.squeeze().round()
    results = (1- results)*255
    os.makedirs("media/mask", exist_ok=True)

    filepath = image[0].split('/')[-1]
    imageio.imwrite(filepath,results)
    
    return filepath
