import imageio
import os
import cv2
import numpy as np
from tensorflow.keras.preprocessing.image import array_to_img, img_to_array
from matplotlib.cm import get_cmap
from scipy.special import expit

thr_dict = {"No Finding":0.3985043764,
            "Mass":0.0340008028,
            "Nodule":0.1290854067,
            "Lung Opacity":0.2623924017,
            "Patchy Opacity":0.0710924342,
            "Reticular Opacity":0.0751557872,
            "Reticulonodular Opacity":0.0219142251,
            "Nodular Opacity":0.0687219054,
            "Linear Opacity":0.0146626765,
            "Nipple Shadow":0.0109776305,
            "Osteoporosis":0.0194494389,
            "Osteopenia":0.0086441701,
            "Osteolytic Lesion":0.0037945583,
            "Fracture":0.0164119676,
            "Healed Fracture":0.0057689156,
            "Old Fracture":0.0044114138,
            "Spondylosis":0.135582611,
            "Scoliosis":0.0706555173,
            "Sclerotic Lesion":0.0074484712,
            "Mediastinal Mass":0.0034820705,
            "Cardiomegaly":0.3150766492,
            "Pleural Effusion":0.1500810385,
            "Pleural Thickening":0.0734574422,
            "Edema":0.029965058,
            "Hiatal Hernia":0.0021343548,
            "Pneumothorax":0.0055564633,
            "Atelectasis":0.0520619489,
            "Subsegmental Atelectasis":0.0070978594,
            "Elevation Of Hemidiaphragm":0.0301435925,
            "Tracheal-Mediastinal Shift":0.0052830973,
            "Volume Loss":0.0222865231,
            "Bronchiectasis":0.0110870562,
            "Enlarged Hilum":0.0042810268,
            "Atherosclerosis":0.0957187414,
            "Tortuous Aorta":0.0473294221,
            "Calcified Tortuous Aorta":0.0337250046,
            "Calcified Aorta":0.0314028598,
            "Support Devices":0.0634697229,
            "Surgical Material":0.0563883446,
            "Suboptimal Inspiration":0.0176297091}
CATEGORIES = list(thr_dict.keys())
thr_list = list(thr_dict.values())

importance_list = [
'Pneumothorax',
 'Mass',
 'Nodule',
 'Mediastinal Mass',
 'Lung Opacity',
 'Pleural Effusion',
 'Atelectasis',
 'Tracheal-Mediastinal Shift',
 'Osteolytic Lesion',
 'Fracture',
 'Sclerotic Lesion',
 'Cardiomegaly',
 'Bronchiectasis',
 'No Finding',
 'Patchy Opacity',
 'Reticular Opacity',
 'Reticulonodular Opacity',
 'Nodular Opacity',
 'Linear Opacity',
 'Nipple Shadow',
 'Osteoporosis',
 'Osteopenia',
 'Healed Fracture',
 'Old Fracture',
 'Spondylosis',
 'Scoliosis',
 'Pleural Thickening',
 'Edema',
 'Hiatal Hernia',
 'Subsegmental Atelectasis',
 'Elevation Of Hemidiaphragm',
 'Volume Loss',
 'Enlarged Hilum',
 'Atherosclerosis',
 'Tortuous Aorta',
 'Calcified Tortuous Aorta',
 'Calcified Aorta',
 'Support Devices',
 'Surgical Material',
 'Suboptimal Inspiration'
]

def blend(img, heatmap):
    img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
    heatmap = np.uint8(255 * heatmap)
    jet = get_cmap("jet")
    jet_colors = jet(np.arange(256))[:, :3]
    jet_heatmap = jet_colors[heatmap]
    jet_heatmap = array_to_img(jet_heatmap)
    jet_heatmap = jet_heatmap.resize((img.shape[1], img.shape[0]))
    jet_heatmap = img_to_array(jet_heatmap)
    superimposed_img = jet_heatmap * 0.4 + img
    superimposed_img = array_to_img(superimposed_img)
    return superimposed_img

def get_prob(prob, thr):
    if prob>thr: return 0.5+((prob-thr)/(1-thr))*0.5
    else: return (prob/thr)*0.5

def postprocess(triton_output, image):
    logits_output = triton_output[0]
    heatmap_output = triton_output[1]

    probs_output = expit(logits_output[0])
    normalized_probs = [get_prob(probs_output[i], thr_list[i]) for i in range(len(probs_output))]
    heatmap_output = expit(heatmap_output[0])

    os.makedirs("imagegrad_tmp", exist_ok=True)
    selected_class = []
    for class_name in importance_list:
        class_idx = CATEGORIES.index(class_name)
        if normalized_probs[class_idx]>0.5:
            selected_class.append(class_idx)
            if len(selected_class)==5: break
    if len(selected_class)!=5:
        for class_name in importance_list:
            class_idx = CATEGORIES.index(class_name)
            if class_idx not in selected_class:
                selected_class.append(class_idx)
                if len(selected_class)==5: break

    original_image = cv2.imread(os.path.join('/backend/media',image.data.name), cv2.IMREAD_GRAYSCALE)
    gradcam_dict = {}
    for class_idx in selected_class:
        class_name = CATEGORIES[class_idx]
        selected_heatmap = heatmap_output[class_idx]
        selected_heatmap = np.maximum(selected_heatmap, 0) / np.max(selected_heatmap)
        superimposed_img = blend(original_image, selected_heatmap)
        filename = image.data.name.split('/')[-1]
        grad_filename = filename[:filename.rfind('.')]+'_'+class_name+'.png'
        superimposed_img.save(grad_filename)
        gradcam_dict[class_name] =grad_filename

    return [normalized_probs, gradcam_dict]
