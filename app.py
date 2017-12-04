import re
from io import BytesIO
from flask import Flask, send_file, request, jsonify
from PIL import Image
import requests
import numpy as np
import tensorflow as tf
from object_detection.utils import label_map_util
import os
import time

PATH_TO_CKPT = '/opt/tensorflow-models/research/ssd_mobilenet_v1_coco_11_06_2017/frozen_inference_graph.pb'

detection_graph = tf.Graph()
with detection_graph.as_default():
    od_graph_def = tf.GraphDef()
    with tf.gfile.GFile(PATH_TO_CKPT, 'rb') as fid:
        serialized_graph = fid.read()
        od_graph_def.ParseFromString(serialized_graph)
        tf.import_graph_def(od_graph_def, name='')

PATH_TO_LABELS = '/opt/tensorflow-models/research/object_detection/data/mscoco_label_map.pbtxt'
NUM_CLASSES = 90

label_map = label_map_util.load_labelmap(PATH_TO_LABELS)
categories = label_map_util.convert_label_map_to_categories(label_map, max_num_classes=NUM_CLASSES, use_display_name=True)
category_index = label_map_util.create_category_index(categories)
print('Loaded')

app = Flask(__name__)

def image2array(image):
    (w, h) = image.size
    return np.array(image.getdata()).reshape((h, w, 3)).astype(np.uint8)

def array2image(arr):
    return Image.fromarray(np.uint8(arr))

def ms():
  return int(round(time.time() * 1000))

@app.route('/api')
def api():
  started_ms = ms()

  url = request.args.get('url')
  threshold = request.args.get('threshold', 0.2)
  r = requests.get(url)
  image = Image.open(BytesIO(r.content))

  downloaded_ms = ms()

  with detection_graph.as_default():
    with tf.Session(graph=detection_graph) as sess:
      image_np = image2array(image)
      image_np_expanded = np.expand_dims(image_np, axis=0)

      image_tensor = detection_graph.get_tensor_by_name('image_tensor:0')
      boxes = detection_graph.get_tensor_by_name('detection_boxes:0')
      scores = detection_graph.get_tensor_by_name('detection_scores:0')
      classes = detection_graph.get_tensor_by_name('detection_classes:0')
      num_detections = detection_graph.get_tensor_by_name('num_detections:0')

      (boxes, scores, classes, num_detections) = sess.run(
            [boxes, scores, classes, num_detections],
            feed_dict={image_tensor: image_np_expanded})

      boxes = np.squeeze(boxes)
      classes = np.squeeze(classes).astype(np.int32)
      scores = np.squeeze(scores)

      allowed_boxes = []
      for box, score, _class in zip(boxes, scores, classes):
        if score >= threshold:
          allowed_boxes.append({
              'y0': float(box[0]),
              'x0': float(box[1]),
              'y1': float(box[2]),
              'x1': float(box[3]),
              'type': category_index[_class]['name'],
              'score': float(score),
          })

      processed_ms = ms()

  return jsonify({
    'boxes': allowed_boxes,
    'download_duration': downloaded_ms - started_ms,
    'processing_duration': processed_ms - downloaded_ms,
  })

if __name__ == '__main__':
    app.run(debug=True)
