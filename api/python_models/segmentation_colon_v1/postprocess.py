import imageio
from django.core.files import File
import os
import nrrd

def postprocess(results,image,predResult):
    results = results.round()
    results = (1- results)
    results = results.reshape((1,384,288,1))
    results = results.swapaxes(1,2)
    filename = image[0].split('/')[-1]
    my_header = {
        'dimension': 4,
        'kinds': ['list', 'domain', 'domain', 'domain'],
        
        'Segment0_ID': 'Segment_1',
        'Segment0_Name': 'Colon',
        'Segment0_Layer': '0',
        
    }
    # Write to a NRRD file
    os.makedirs("tmp", exist_ok=True)
    filepath = os.path.join("tmp",filename)
    nrrd.write(filepath, results, my_header)
    
    return filepath
