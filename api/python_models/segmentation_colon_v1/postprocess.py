import imageio
from django.core.files import File
import os
import nrrd

def postprocess(results,image,predResult):
    results = results.round()
    results = (1- results)
    results = results.reshape((1,384,288,1))
    # results = results.swapaxes(1,2)
    filename = image[0].split('/')[-1]
    filename = filename.split('.')[0] +".seg.nrrd"
    my_header = {
        'dimension': 4,
        'kinds': ['list', 'domain', 'domain', 'domain'],
        
        'Segment0_ID': 'Segment_1',
        'Segment0_Name': 'Colon',
        'Segment0_Layer': '0',
        
    }
    # Write to a NRRD file
    nrrd.write(filename, results, my_header)
    
    return filename
