import tensorflow as tf
from tensorflow.python.platform import gfile
import numpy as np
import cv2
import os

tf.compat.v1.disable_v2_behavior()

class GradcamModel():
    def __init__(self, pbpath:str):
        
        tf.compat.v1.reset_default_graph()
        sess = tf.compat.v1.Session(config=tf.compat.v1.ConfigProto(
        allow_soft_placement=True, log_device_placement=True)
        )

        with gfile.FastGFile(pbpath, 'rb') as f:
            graph_def = tf.compat.v1.GraphDef()
            graph_def.ParseFromString(f.read())

        self._sess = sess
            
        with sess.as_default():
            tf.compat.v1.import_graph_def(graph_def, name='')

        self._output_layer = sess.graph.get_tensor_by_name(
            'NV_MODEL_OUTPUT:0')
        self._convolutional_output = sess.graph.get_tensor_by_name(
            [n.name for n in sess.graph_def.node if 'conv' in n.name][-1]+':0')

    
    def gradcam(self, img):
        with self._sess.graph.as_default():
            feed_dict = {'NV_MODEL_INPUT:0': img, 'NV_IS_TRAINING:0': False}

            # Get output for this action
            top_class_channel = tf.math.reduce_max(self._output_layer, axis=1)

            # Compute gradients based on last cnn layer
            target_grads = tf.compat.v1.gradients(top_class_channel, self._convolutional_output)[0]

            last_conv_layer_output, grads= self._sess.run(
                [self._convolutional_output, target_grads], feed_dict=feed_dict)
            last_conv_layer_output = last_conv_layer_output[0]

            pooled_grads = tf.reduce_mean(grads, axis=(0, 1, 2)).eval(session=self._sess)

            for i in range(pooled_grads.shape[-1]):
                last_conv_layer_output[:, :, i] *= pooled_grads[i]

            heatmap = np.mean(last_conv_layer_output, axis=-1)

            # Postprocess
            # Scale maximum value to 1.0
            heatmap = np.maximum(heatmap, 0) / np.max(heatmap)

            # # Scale back to input frame dimensions.
            # heatmap = cv2.resize(heatmap, img.shape[1:3])

            return heatmap
        
    def infer(self, img):
        with self._sess.graph.as_default():
            feed_dict = {'NV_MODEL_INPUT:0': img, 'NV_IS_TRAINING:0': False}
            return self._sess.run(self._output_layer, feed_dict=feed_dict)