import numpy as np
import cv2
from skimage.transform import resize
import os

def preprocess(Input):
    img = cv2.imread(os.path.join('/backend/media',Input))
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    img = resize(img, (256,256), order=1, mode='reflect',
              preserve_range=True,
              anti_aliasing=True)
    img = np.expand_dims(img, axis=0)
    return img