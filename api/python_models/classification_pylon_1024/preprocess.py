import albumentations as albu
import numpy as np
import cv2
import os

def get_transformed_image(image):
    _transform = [
        albu.augmentations.transforms.Resize(height=1024, width=1024, interpolation=cv2.INTER_CUBIC),
        albu.augmentations.transforms.Normalize(mean=[0.4984], std=[0.2483])
    ]
    transform = albu.Compose(_transform)
    transformed_img = transform(image=image)["image"]
    transformed_img = np.expand_dims(transformed_img, axis=(0,1)).astype(np.float32)
    return transformed_img

def preprocess(Input):
    img = cv2.imread(Input, cv2.IMREAD_GRAYSCALE)
    transformed_img = get_transformed_image(img)
    return transformed_img