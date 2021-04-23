import albumentations as albu
import segmentation_models_pytorch as smp
import numpy as np
import cv2

def to_tensor(x, **kwargs):
    return x.transpose(2, 0, 1).astype('float32')

def get_preprocessing_segment_colon(image):
    
    _transform = [
        albu.Lambda(image=smp.encoders.get_preprocessing_fn('resnet34', 'imagenet')),
        albu.Lambda(image=to_tensor, mask=to_tensor),
    ]
    transform = albu.Compose(_transform)
    preprocessImage = transform(image=image)["image"]
    preprocessImage = np.expand_dims(preprocessImage,0)
    return preprocessImage

def preprocess(Input):
    Input = cv2.imread(str(Input))
    print(type(Input))
    Input = get_preprocessing_segment_colon(Input)

    return Input