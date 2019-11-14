
from openvino.inference_engine import IENetwork, IEPlugin
import cv2
import os
import threading
import time
import traceback


class ObjectDetector_Mobilenet_SSD():
    def __init__(self, device, getFrameFunc):
        self.getFrameFunc = getFrameFunc
        self.originFrame = None
        self.processedFrame = None

        # options
        #device = "MYRIAD" #생성자로 대체
        if device == 'CPU':
            model_xml = './models/FP32/mobilenet-ssd.xml'
        else:
            model_xml = './models/FP16/mobilenet-ssd.xml'

        model_bin = os.path.splitext(model_xml)[0] + ".bin"
        plugin_dir = None
        cpu_extension = '/opt/intel/openvino/inference_engine/lib/intel64/libcpu_extension_sse4.so'
        self.labels = ["None", "plane", "bicycle", "bird", "boat", "bottle", "bus", "car", "cat", "chair", "cow", "table", "dog", "horse", "motorcycle", "person", "plant", "sheep", "sofa", "train", "monitor"]

        net = IENetwork(model=model_xml, weights=model_bin)
        plugin = IEPlugin(device=device)
        if cpu_extension and 'CPU' in device:
            plugin.add_cpu_extension(cpu_extension)
        self.exec_net = plugin.load(net)

        self.input_blob = next(iter(net.inputs))
        self.out_blob = next(iter(net.outputs))
        print("Loading IR to the plugin...")

        # Read and pre-process input image
        n, c, self.h, self.w = net.inputs[self.input_blob].shape
        print(n, c, self.h, self.w)

        #랜더링 스레드에서 가져갈 데이터들
        self.detectedFaces = []
        self.infer_time = 0

        self.inferFPS = 15

        processThread =  threading.Thread(target=self.inferenceThread)
        processThread.daemon = True
        processThread.start()

    def detect(self):
        frame = cv2.resize(self.originFrame, (self.w, self.h))
        blob = cv2.dnn.blobFromImage(frame, size=(self.w, self.h), ddepth=cv2.CV_32F)

        infer_start = time.time()
        res = self.exec_net.infer({self.input_blob: blob})[self.out_blob]
        self.infer_time = time.time() - infer_start

        self.detectedFaces.clear()
        for obj in res[0][0]:
            if obj[2] > 0.75:
                xmin = obj[3]
                ymin = obj[4]
                xmax = obj[5]
                ymax = obj[6]
                if xmin < 0:
                    xmin *= -1
                if ymin < 0:
                    ymin *= -1

                class_id = int(obj[1])
                self.detectedFaces.append((xmin, ymin, xmax, ymax, class_id, obj[2]))

    def inferenceThread(self):
        while True:
            if self.getFrameFunc is not None:
                try:
                    frame = self.getFrameFunc()
                    if frame is not None:
                        self.originFrame = frame.copy()
                        self.detect()
                        time.sleep(1.0/self.inferFPS)

                except Exception as error:
                    print(error)
                    traceback.print_exc()
                    print("catch error")
    def getProcessedData(self):
        return self.infer_time, self.detectedFaces
    def setInferFPS(self, newFPS):
        self.inferFPS = newFPS

