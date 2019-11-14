import sys

from openvino.inference_engine import IENetwork, IEPlugin
import cv2
import os
import threading
import time
import traceback

class ObjectClassifier_Cifar10():
    def __init__(self, device, getFrameFunc):
        self.getFrameFunc = getFrameFunc
        self.originFrame = None
        self.processedFrame = None

        # options
        #device = "MYRIAD" #생성자로 대체
        model_xml = './models/cifar_0.xml'

        model_bin = os.path.splitext(model_xml)[0] + ".bin"
        plugin_dir = None
        cpu_extension = '/opt/intel/openvino/inference_engine/lib/intel64/libcpu_extension_sse4.so'
        self.labels = ["airplane", "automobile", "bird", "cat", "deer", "dog", "frog", "horse", "ship", "truck","rock","scissors","paper","LG","KISTI","Intel"]

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
        self.sortedClassifiedList = []
        self.infer_time = 0

        self.inferFPS = 15

        processThread =  threading.Thread(target=self.inferenceThread)
        processThread.daemon = True
        processThread.start()
        print('faceDetectionThread started')

    def detect(self):
        frame = cv2.resize(self.originFrame, (self.w, self.h))
        blob = cv2.dnn.blobFromImage(frame, size=(self.w, self.h), ddepth=cv2.CV_32F)

        infer_start = time.time()
        res = self.exec_net.infer({self.input_blob: blob})[self.out_blob]
        self.infer_time = time.time() - infer_start

        # maximum = max(res[0])
        # maximumIdx = res[0].index(maximum)
        index_max = max(range(len(res[0])), key=res[0].__getitem__)

        self.sortedClassifiedList.clear()
        sortedList = sorted(range(len(res[0])), key=lambda i: res[0][i], reverse=True)
        for idx in sortedList:
            self.sortedClassifiedList.append((idx,res[0][idx]))

    def inferenceThread(self):
        while True:
            frame = self.getFrameFunc()
            if frame is not None:
                try:
                    self.originFrame = frame.copy()
                    self.detect()
                    time.sleep(1.0/self.inferFPS)

                except Exception as error:
                    print(error)
                    traceback.print_exc()
                    print("catch error")
    def getProcessedData(self):
        return self.infer_time, self.sortedClassifiedList
    def setInferFPS(self, newFPS):
        self.inferFPS = newFPS

