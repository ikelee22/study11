# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'Tello_Gui_E_ver.ui'
#
# Created by: PyQt5 UI code generator 5.10.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets
import tello
import cv2
import traceback
import datetime

class Ui_Dialog(object):
    def __init__(self, Dialog, device, bObjectDetection):
        super().__init__()
        self.setupUi(Dialog)
        self.bindFuncs()


        ######
        self.carRenderW = 100
        self.carRenderH = 100
        self.bCaptureCar = False
        self.carDateTime = None
        self.dogRenderW = 100
        self.dogRenderH = 100
        self.bCaptureDog = False
        self.dogDateTime = None
        ######

        self.logBuffer = []
        self.logWriteTimer = QtCore.QTimer()
        self.logWriteTimer.timeout.connect(self.TimerEvent10ms)
        self.logWriteTimer.start(10)

        self.is_Connect=False
        self.delta_height=20
        self.delta_rotate=45
        self.delta_LR=20
        self.delta_FB=20
        self.delta_LD=20
        self.delta_RD=20

        self.tello = tello.Tello(self.log, self.stateReceive)
        self.updateIP()

        self.stateDict = {
            "pitch": "0",
            "roll": "0",
            "yaw": "0",
            "vgx": "0",
            "vgy": "0",
            "vgz": "0",
            "templ": "0",
            "temph": "0",
            "tof": "0",
            "h": "0",
            "bat": "0",
            "baro": "0.0",
            "time": "0",
            "agx": '0.0',
            "agy": '0.0',
            "agz": '0.0',
            "wifi": '99'
        }

        self.originFrame = None

        self.bObjectDetection = bObjectDetection
        if self.bObjectDetection:
            print('Object Detector initialize...')
            from ObjectDetector_Mobilenet_SSD import ObjectDetector_Mobilenet_SSD
            self.objDetector = ObjectDetector_Mobilenet_SSD(device, self.getOriginFrame)
        self.requestSNR = False

        self.button_on_off(False)

    def TimerEvent10ms(self):
        self.updateImage()
        for logStr in self.logBuffer:
            self.loglist.append(logStr)
        if len(self.logBuffer) > 0:
            self.loglist.verticalScrollBar().setValue(self.loglist.verticalScrollBar().maximum())
            self.logBuffer.clear()
        self.updateState()
    def log(self, logStr):
        logStr = logStr.strip()
        self.logBuffer.append(logStr)
    def stateReceive(self, stateData):
        stateData = stateData.decode('utf-8')
        states = stateData.split(';')[:-1]
        for state in states:
            keyValue = state.split(':')
            key = keyValue[0]
            value = keyValue[1]
            self.stateDict[key] = value
        #self.updateState()
        return self.stateDict
    def updateState(self):
        self.TOF.setText(self.TOF_TextFormat % int(self.stateDict['tof']))
        self.Height.setText(self.HeightTextFormat % int(self.stateDict['h']))
        sec = int(self.stateDict['time'])
        hour = int(sec / 3600)
        sec = sec - hour * 3600
        minute = int(sec / 60)
        sec = sec - minute * 60
        self.F_Time.setText(self.F_TimeTextFormat % (hour, minute, sec))
        self.temp.setText(self.tempTextFormat % (int(self.stateDict['templ']), int(self.stateDict['temph'])))
        self.Battery.setProperty("value", int(self.stateDict['bat']))
        if self.requestSNR:
            try:
                wifi_SNR = int(self.tello.response)
                self.wifi_snr.setProperty('value', wifi_SNR)
            except:
                pass
    def updateImage(self):
        try:
            if self.tello.cap is not None:
                self.originFrame = self.tello.readFrame()
                if self.originFrame is not None:
                    renderImg = cv2.cvtColor(self.originFrame, cv2.COLOR_BGR2RGB)
                    originW = self.getCapW()
                    originH = self.getCapH()
                    renderingW = 600
                    renderingH = 450
                    #현재시간
                    curTime = datetime.datetime.now()
                    millisecond = int(curTime.microsecond / 10000)
                    #Car 시간 업데이트
                    if not self.bCaptureCar:
                        self.Qt_CarTime1.display(curTime.minute)
                        self.Qt_CarTime2.display(curTime.second)
                        self.Qt_CarTime3.display(millisecond)
                        self.carDateTime = curTime
                    #Dog 시간 업데이트
                    if not self.bCaptureDog:
                        self.Qt_DogTime1.display(curTime.minute)
                        self.Qt_DogTime2.display(curTime.second)
                        self.Qt_DogTime3.display(millisecond)
                        self.dogDateTime = curTime
                    # 최종 걸린시간 계산
                    timerDateTime = self.carDateTime - self.dogDateTime
                    allSec = timerDateTime.seconds
                    minute = int(allSec/60)
                    sec = allSec - minute*60
                    self.Qt_ResultTime1.display(minute)
                    self.Qt_ResultTime2.display(sec)
                    self.Qt_ResultTime3.display(int(timerDateTime.microseconds/10000))

                    if self.bObjectDetection:
                        # 추론결과물 받기
                        infer_time, detectedObjects = self.objDetector.getProcessedData()
                        if detectedObjects is not None:
                            for object in detectedObjects:
                                obj3, obj4, obj5, obj6, class_id, percent = object
                                xmin = int(obj3 * originW)
                                ymin = int(obj4 * originH)
                                xmax = int(obj5 * originW)
                                ymax = int(obj6 * originH)

                                if not self.bCaptureCar and self.objDetector.labels[class_id] == 'car':
                                    onlyCarFrame = self.originFrame[ymin:ymax, xmin:xmax]
                                    onlyCarFrame = cv2.cvtColor(onlyCarFrame,cv2.COLOR_BGR2RGB)
                                    renderCarImg = cv2.resize(onlyCarFrame, (self.carRenderW, self.carRenderH))
                                    bytesPerLine = 3 * self.carRenderW
                                    qImg = QtGui.QImage(renderCarImg.data, self.carRenderW, self.carRenderH, bytesPerLine, QtGui.QImage.Format_RGB888)
                                    self.Qt_CarImgLabel.setPixmap(QtGui.QPixmap(qImg))
                                    self.bCaptureCar=True
                                    self.log('car captured')

                                if not self.bCaptureDog and self.objDetector.labels[class_id] == 'dog':
                                    onlyDogFrame = self.originFrame[ymin:ymax, xmin:xmax]
                                    onlyDogFrame = cv2.cvtColor(onlyDogFrame,cv2.COLOR_BGR2RGB)
                                    renderDogImg = cv2.resize(onlyDogFrame, (self.dogRenderW, self.dogRenderH))
                                    bytesPerLine = 3 * self.dogRenderW
                                    qImg = QtGui.QImage(renderDogImg.data, self.dogRenderW, self.dogRenderH, bytesPerLine, QtGui.QImage.Format_RGB888)
                                    self.Qt_DogImgLabel.setPixmap(QtGui.QPixmap(qImg))
                                    self.bCaptureDog=True
                                    self.log('dog captured')
                                # face그리기
                                cv2.rectangle(renderImg, (xmin,ymin),
                                              (xmax, ymax), (0,0,0), 2)
                                cv2.putText(renderImg, self.objDetector.labels[class_id], (xmin, ymin), cv2.FONT_HERSHEY_COMPLEX, 1.5,
                                            (200, 10, 10), 1)

                    #QtLabel에 뿌리기
                    renderRimg = cv2.resize(renderImg, (renderingW, renderingH))

                    if self.bObjectDetection:
                        # frame에대한 정보 그리기
                        inf_time_message = "Inference time: {:.3f} ms".format(infer_time * 1000)
                        cv2.putText(renderRimg, inf_time_message, (15, 15), cv2.FONT_HERSHEY_COMPLEX, 0.5,
                                    (200, 10, 10), 1)

                    bytesPerLine = 3 * renderingW
                    qImg = QtGui.QImage(renderRimg.data, renderingW, renderingH, bytesPerLine, QtGui.QImage.Format_RGB888)
                    self.videoimg.setPixmap(QtGui.QPixmap(qImg))

        except Exception as error:
                traceback.print_exc()
                print("catch error")
    def resetTimer(self):
        self.bCaptureDog = False
        self.bCaptureCar = False
        self.Qt_CarTime1.display(0)
        self.Qt_CarTime2.display(0)
        self.Qt_CarTime3.display(0)
        self.Qt_DogTime1.display(0)
        self.Qt_DogTime2.display(0)
        self.Qt_DogTime3.display(0)
        self.Qt_ResultTime1.display(0)
        self.Qt_ResultTime2.display(0)
        self.Qt_ResultTime3.display(0)
        self.Qt_CarImgLabel.setPixmap(QtGui.QPixmap("./res/.car.jpg"))
        self.Qt_DogImgLabel.setPixmap(QtGui.QPixmap(":/Picture/dog.jpg"))
    def getCapW(self):
        if self.tello.cap is not None:
            return self.tello.cap.get(3)
        return -1
    def getCapH(self):
        if self.tello.cap is not None:
            return self.tello.cap.get(4)
        return -1
    def getOriginFrame(self):
        return self.originFrame

    #########QT###########
    def bindFuncs(self):
        # forward
        self.Forward_M1.clicked.connect(self.moveforward)
        self.Forward_M2.clicked.connect(self.moveforward)
        # backward
        self.Backward_M1.clicked.connect(self.movebackward)
        self.Backward_M2.clicked.connect(self.movebackward)
        # left
        self.Left_M1.clicked.connect(self.moveleft)
        self.Left_M2.clicked.connect(self.moveleft)
        # right
        self.Right_M1.clicked.connect(self.moveright)
        # right_M2 = right_M2_2
        self.Right_M2.clicked.connect(self.moveright)
        # Up
        self.Up_M1.clicked.connect(self.Up)
        self.Up_M2.clicked.connect(self.Up)
        # Down
        self.Down_M1.clicked.connect(self.Down)
        self.Down_M2.clicked.connect(self.Down)
        # CW
        self.CW_M1.clicked.connect(self.rotateCW)
        self.CW_M2.clicked.connect(self.rotateCW)
        # CCW
        self.CCW_M1.clicked.connect(self.rotateCCW)
        self.CCW_M2.clicked.connect(self.rotateCCW)
        # takeoff
        self.TakeOff_M1.clicked.connect(self.takeoff)
        self.TakeOff_M2.clicked.connect(self.takeoff)
        # connect
        self.Connect_M1.clicked.connect(self.connect)
        self.Connect_M2.clicked.connect(self.connect)
        # land
        self.Land_M1.clicked.connect(self.land)
        self.Land_M2.clicked.connect(self.land)
        # snf check
        self.SNR_Check.clicked.connect(self.check)

        # spinbox
        # height
        self.Height_Spinbox.valueChanged.connect(self.updateHeight)
        # rotate
        self.Rotation_Spinbox.valueChanged.connect(self.updateRotation)
        # master
        self.Master_Spinbox.valueChanged.connect(self.updateAll)
        self.L_R_Spinbox.valueChanged.connect(self.updateLR)
        self.F_B_SpinBox.valueChanged.connect(self.updateFB)

        # radio button
        # master
        self.radioButton1.clicked.connect(self.enable)
        # semi-master
        # private
        self.radioButton3.clicked.connect(self.enable)
        # ipaddress
        self.IPAddress.textChanged.connect(self.updateIP)

        self.TimerReset.clicked.connect(self.resetTimer)

    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(1229, 750)
        Dialog.setMinimumSize(QtCore.QSize(1229, 750))
        Dialog.setMaximumSize(QtCore.QSize(1229, 750))
        self.horizontalLayout_5 = QtWidgets.QHBoxLayout(Dialog)
        self.horizontalLayout_5.setObjectName("horizontalLayout_5")
        self.verticalLayout_3 = QtWidgets.QVBoxLayout()
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.videoimg = QtWidgets.QLabel(Dialog)
        self.videoimg.setMinimumSize(QtCore.QSize(600, 450))
        self.videoimg.setMaximumSize(QtCore.QSize(600, 450))
        self.videoimg.setText("")
        self.videoimg.setPixmap(QtGui.QPixmap(":/Picture/sponsor.jpg"))
        self.videoimg.setObjectName("videoimg")
        self.verticalLayout_3.addWidget(self.videoimg)
        self.contorlWidget = QtWidgets.QTabWidget(Dialog)
        self.contorlWidget.setObjectName("contorlWidget")
        self.mode1 = QtWidgets.QWidget()
        self.mode1.setObjectName("mode1")
        self.gridLayout_6 = QtWidgets.QGridLayout(self.mode1)
        self.gridLayout_6.setObjectName("gridLayout_6")
        self.gridLayout_5 = QtWidgets.QGridLayout()
        self.gridLayout_5.setObjectName("gridLayout_5")
        self.Forward_M1 = QtWidgets.QPushButton(self.mode1)
        self.Forward_M1.setEnabled(False)
        self.Forward_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Forward_M1.setFont(font)
        self.Forward_M1.setObjectName("Forward_M1")
        self.gridLayout_5.addWidget(self.Forward_M1, 0, 1, 1, 1)
        self.Left_M1 = QtWidgets.QPushButton(self.mode1)
        self.Left_M1.setEnabled(False)
        self.Left_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Left_M1.setFont(font)
        self.Left_M1.setObjectName("Left_M1")
        self.gridLayout_5.addWidget(self.Left_M1, 1, 0, 1, 1)
        self.Right_M1 = QtWidgets.QPushButton(self.mode1)
        self.Right_M1.setEnabled(False)
        self.Right_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Right_M1.setFont(font)
        self.Right_M1.setObjectName("Right_M1")
        self.gridLayout_5.addWidget(self.Right_M1, 1, 2, 1, 1)
        self.Backward_M1 = QtWidgets.QPushButton(self.mode1)
        self.Backward_M1.setEnabled(False)
        self.Backward_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Backward_M1.setFont(font)
        self.Backward_M1.setObjectName("Backward_M1")
        self.gridLayout_5.addWidget(self.Backward_M1, 2, 1, 1, 1)
        self.gridLayout_6.addLayout(self.gridLayout_5, 0, 2, 1, 1)
        self.verticalLayout_2 = QtWidgets.QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.TakeOff_M1 = QtWidgets.QPushButton(self.mode1)
        self.TakeOff_M1.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.TakeOff_M1.setFont(font)
        self.TakeOff_M1.setObjectName("TakeOff_M1")
        self.verticalLayout_2.addWidget(self.TakeOff_M1)
        self.Connect_M1 = QtWidgets.QPushButton(self.mode1)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Connect_M1.setFont(font)
        self.Connect_M1.setObjectName("Connect_M1")
        self.verticalLayout_2.addWidget(self.Connect_M1)
        self.Land_M1 = QtWidgets.QPushButton(self.mode1)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Land_M1.setFont(font)
        self.Land_M1.setObjectName("Land_M1")
        self.verticalLayout_2.addWidget(self.Land_M1)
        self.gridLayout_6.addLayout(self.verticalLayout_2, 0, 1, 1, 1)
        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.gridLayout_4.setObjectName("gridLayout_4")
        self.Up_M1 = QtWidgets.QPushButton(self.mode1)
        self.Up_M1.setEnabled(False)
        self.Up_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Up_M1.setFont(font)
        self.Up_M1.setObjectName("Up_M1")
        self.gridLayout_4.addWidget(self.Up_M1, 0, 1, 1, 1)
        self.CCW_M1 = QtWidgets.QPushButton(self.mode1)
        self.CCW_M1.setEnabled(False)
        self.CCW_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.CCW_M1.setFont(font)
        self.CCW_M1.setObjectName("CCW_M1")
        self.gridLayout_4.addWidget(self.CCW_M1, 1, 0, 1, 1)
        self.CW_M1 = QtWidgets.QPushButton(self.mode1)
        self.CW_M1.setEnabled(False)
        self.CW_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.CW_M1.setFont(font)
        self.CW_M1.setObjectName("CW_M1")
        self.gridLayout_4.addWidget(self.CW_M1, 1, 2, 1, 1)
        self.Down_M1 = QtWidgets.QPushButton(self.mode1)
        self.Down_M1.setEnabled(False)
        self.Down_M1.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Down_M1.setFont(font)
        self.Down_M1.setObjectName("Down_M1")
        self.gridLayout_4.addWidget(self.Down_M1, 2, 1, 1, 1)
        self.gridLayout_6.addLayout(self.gridLayout_4, 0, 0, 1, 1)
        self.contorlWidget.addTab(self.mode1, "")
        self.tab2 = QtWidgets.QWidget()
        self.tab2.setObjectName("tab2")
        self.gridLayout_3 = QtWidgets.QGridLayout(self.tab2)
        self.gridLayout_3.setObjectName("gridLayout_3")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.Forward_M2 = QtWidgets.QPushButton(self.tab2)
        self.Forward_M2.setEnabled(False)
        self.Forward_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Forward_M2.setFont(font)
        self.Forward_M2.setObjectName("Forward_M2")
        self.gridLayout.addWidget(self.Forward_M2, 0, 1, 1, 1)
        self.CCW_M2 = QtWidgets.QPushButton(self.tab2)
        self.CCW_M2.setEnabled(False)
        self.CCW_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.CCW_M2.setFont(font)
        self.CCW_M2.setObjectName("CCW_M2")
        self.gridLayout.addWidget(self.CCW_M2, 1, 0, 1, 1)
        self.CW_M2 = QtWidgets.QPushButton(self.tab2)
        self.CW_M2.setEnabled(False)
        self.CW_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.CW_M2.setFont(font)
        self.CW_M2.setObjectName("CW_M2")
        self.gridLayout.addWidget(self.CW_M2, 1, 2, 1, 1)
        self.Backward_M2 = QtWidgets.QPushButton(self.tab2)
        self.Backward_M2.setEnabled(False)
        self.Backward_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Backward_M2.setFont(font)
        self.Backward_M2.setObjectName("Backward_M2")
        self.gridLayout.addWidget(self.Backward_M2, 2, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.TakeOff_M2 = QtWidgets.QPushButton(self.tab2)
        self.TakeOff_M2.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.TakeOff_M2.setFont(font)
        self.TakeOff_M2.setObjectName("TakeOff_M2")
        self.verticalLayout.addWidget(self.TakeOff_M2)
        self.Connect_M2 = QtWidgets.QPushButton(self.tab2)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Connect_M2.setFont(font)
        self.Connect_M2.setObjectName("Connect_M2")
        self.verticalLayout.addWidget(self.Connect_M2)
        self.Land_M2 = QtWidgets.QPushButton(self.tab2)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Land_M2.setFont(font)
        self.Land_M2.setObjectName("Land_M2")
        self.verticalLayout.addWidget(self.Land_M2)
        self.gridLayout_3.addLayout(self.verticalLayout, 0, 1, 1, 1)
        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.Up_M2 = QtWidgets.QPushButton(self.tab2)
        self.Up_M2.setEnabled(False)
        self.Up_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Up_M2.setFont(font)
        self.Up_M2.setObjectName("Up_M2")
        self.gridLayout_2.addWidget(self.Up_M2, 0, 1, 1, 1)
        self.Left_M2 = QtWidgets.QPushButton(self.tab2)
        self.Left_M2.setEnabled(False)
        self.Left_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Left_M2.setFont(font)
        self.Left_M2.setObjectName("Left_M2")
        self.gridLayout_2.addWidget(self.Left_M2, 1, 0, 1, 1)
        self.Right_M2 = QtWidgets.QPushButton(self.tab2)
        self.Right_M2.setEnabled(False)
        self.Right_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Right_M2.setFont(font)
        self.Right_M2.setObjectName("Right_M2")
        self.gridLayout_2.addWidget(self.Right_M2, 1, 2, 1, 1)
        self.Down_M2 = QtWidgets.QPushButton(self.tab2)
        self.Down_M2.setEnabled(False)
        self.Down_M2.setMinimumSize(QtCore.QSize(60, 60))
        font = QtGui.QFont()
        font.setPointSize(20)
        self.Down_M2.setFont(font)
        self.Down_M2.setObjectName("Down_M2")
        self.gridLayout_2.addWidget(self.Down_M2, 2, 1, 1, 1)
        self.gridLayout_3.addLayout(self.gridLayout_2, 0, 2, 1, 1)
        self.contorlWidget.addTab(self.tab2, "")
        self.verticalLayout_3.addWidget(self.contorlWidget)
        self.horizontalLayout_5.addLayout(self.verticalLayout_3)
        self.verticalLayout_8 = QtWidgets.QVBoxLayout()
        self.verticalLayout_8.setObjectName("verticalLayout_8")
        self.TimerReset = QtWidgets.QPushButton(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.TimerReset.setFont(font)
        self.TimerReset.setObjectName("TimerReset")
        self.verticalLayout_8.addWidget(self.TimerReset)
        self.verticalLayout_4 = QtWidgets.QVBoxLayout()
        self.verticalLayout_4.setObjectName("verticalLayout_4")
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.label_53 = QtWidgets.QLabel(Dialog)
        self.label_53.setText("")
        self.label_53.setPixmap(QtGui.QPixmap(":/Picture/time.jpg"))
        self.label_53.setObjectName("label_53")
        self.horizontalLayout_2.addWidget(self.label_53)
        self.Qt_ResultTime1 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_ResultTime1.setDigitCount(2)
        self.Qt_ResultTime1.setProperty("intValue", 99)
        self.Qt_ResultTime1.setObjectName("T1")
        self.horizontalLayout_2.addWidget(self.Qt_ResultTime1)
        self.label = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label.setFont(font)
        self.label.setObjectName("label")
        self.horizontalLayout_2.addWidget(self.label)
        self.Qt_ResultTime2 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_ResultTime2.setDigitCount(2)
        self.Qt_ResultTime2.setProperty("intValue", 99)
        self.Qt_ResultTime2.setObjectName("T2")
        self.horizontalLayout_2.addWidget(self.Qt_ResultTime2)
        self.label_2 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_2.setFont(font)
        self.label_2.setObjectName("label_2")
        self.horizontalLayout_2.addWidget(self.label_2)
        self.Qt_ResultTime3 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_ResultTime3.setDigitCount(2)
        self.Qt_ResultTime3.setProperty("intValue", 99)
        self.Qt_ResultTime3.setObjectName("T3")
        self.horizontalLayout_2.addWidget(self.Qt_ResultTime3)
        self.verticalLayout_4.addLayout(self.horizontalLayout_2)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.Qt_DogImgLabel = QtWidgets.QLabel(Dialog)
        self.Qt_DogImgLabel.setText("")
        self.Qt_DogImgLabel.setPixmap(QtGui.QPixmap(":/Picture/dog.jpg"))
        self.Qt_DogImgLabel.setObjectName("dogimg")
        self.horizontalLayout_3.addWidget(self.Qt_DogImgLabel)
        self.Qt_DogTime1 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_DogTime1.setDigitCount(2)
        self.Qt_DogTime1.setProperty("intValue", 99)
        self.Qt_DogTime1.setObjectName("D1")
        self.horizontalLayout_3.addWidget(self.Qt_DogTime1)
        self.label_7 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_7.setFont(font)
        self.label_7.setObjectName("label_7")
        self.horizontalLayout_3.addWidget(self.label_7)
        self.Qt_DogTime2 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_DogTime2.setDigitCount(2)
        self.Qt_DogTime2.setProperty("intValue", 99)
        self.Qt_DogTime2.setObjectName("D2")
        self.horizontalLayout_3.addWidget(self.Qt_DogTime2)
        self.label_12 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_12.setFont(font)
        self.label_12.setObjectName("label_12")
        self.horizontalLayout_3.addWidget(self.label_12)
        self.Qt_DogTime3 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_DogTime3.setDigitCount(2)
        self.Qt_DogTime3.setProperty("intValue", 99)
        self.Qt_DogTime3.setObjectName("D3")
        self.horizontalLayout_3.addWidget(self.Qt_DogTime3)
        self.verticalLayout_4.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_4 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_4.setObjectName("horizontalLayout_4")
        self.Qt_CarImgLabel = QtWidgets.QLabel(Dialog)
        self.Qt_CarImgLabel.setText("")
        self.Qt_CarImgLabel.setPixmap(QtGui.QPixmap("./res/car.jpg"))
        self.Qt_CarImgLabel.setObjectName("catimg")
        self.horizontalLayout_4.addWidget(self.Qt_CarImgLabel)
        self.Qt_CarTime1 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_CarTime1.setDigitCount(2)
        self.Qt_CarTime1.setProperty("intValue", 99)
        self.Qt_CarTime1.setObjectName("C1")
        self.horizontalLayout_4.addWidget(self.Qt_CarTime1)
        self.label_49 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_49.setFont(font)
        self.label_49.setObjectName("label_49")
        self.horizontalLayout_4.addWidget(self.label_49)
        self.Qt_CarTime2 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_CarTime2.setDigitCount(2)
        self.Qt_CarTime2.setProperty("intValue", 99)
        self.Qt_CarTime2.setObjectName("C2")
        self.horizontalLayout_4.addWidget(self.Qt_CarTime2)
        self.label_50 = QtWidgets.QLabel(Dialog)
        font = QtGui.QFont()
        font.setPointSize(25)
        self.label_50.setFont(font)
        self.label_50.setObjectName("label_50")
        self.horizontalLayout_4.addWidget(self.label_50)
        self.Qt_CarTime3 = QtWidgets.QLCDNumber(Dialog)
        self.Qt_CarTime3.setDigitCount(2)
        self.Qt_CarTime3.setProperty("intValue", 99)
        self.Qt_CarTime3.setObjectName("C3")
        self.horizontalLayout_4.addWidget(self.Qt_CarTime3)
        self.verticalLayout_4.addLayout(self.horizontalLayout_4)
        self.verticalLayout_8.addLayout(self.verticalLayout_4)
        self.table = QtWidgets.QTabWidget(Dialog)
        self.table.setObjectName("table")
        self.droneinfo = QtWidgets.QWidget()
        self.droneinfo.setObjectName("droneinfo")
        self.verticalLayout_6 = QtWidgets.QVBoxLayout(self.droneinfo)
        self.verticalLayout_6.setObjectName("verticalLayout_6")
        self.horizontalLayout_10 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_10.setObjectName("horizontalLayout_10")
        self.label_5 = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_5.setFont(font)
        self.label_5.setObjectName("label_5")
        self.horizontalLayout_10.addWidget(self.label_5)
        self.Battery = QtWidgets.QProgressBar(self.droneinfo)
        self.Battery.setProperty("value", 100)
        self.Battery.setObjectName("Battery")
        self.horizontalLayout_10.addWidget(self.Battery)
        self.verticalLayout_6.addLayout(self.horizontalLayout_10)
        self.horizontalLayout_11 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_11.setObjectName("horizontalLayout_11")
        self.label_6 = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_6.setFont(font)
        self.label_6.setObjectName("label_6")
        self.horizontalLayout_11.addWidget(self.label_6)
        self.wifi_snr = QtWidgets.QProgressBar(self.droneinfo)
        self.wifi_snr.setProperty("value", 99)
        self.wifi_snr.setObjectName("wifi_snr")
        self.horizontalLayout_11.addWidget(self.wifi_snr)
        self.SNR_Check = QtWidgets.QPushButton(self.droneinfo)
        self.SNR_Check.setObjectName("SNR_Check")
        self.horizontalLayout_11.addWidget(self.SNR_Check)
        self.verticalLayout_6.addLayout(self.horizontalLayout_11)
        self.horizontalLayout_12 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_12.setObjectName("horizontalLayout_12")
        self.Height = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Height.setFont(font)
        self.Height.setObjectName("Height")
        self.horizontalLayout_12.addWidget(self.Height)
        self.TOF = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.TOF.setFont(font)
        self.TOF.setAcceptDrops(False)
        self.TOF.setObjectName("TOF")
        self.horizontalLayout_12.addWidget(self.TOF)
        self.verticalLayout_6.addLayout(self.horizontalLayout_12)
        self.F_Time = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.F_Time.setFont(font)
        self.F_Time.setObjectName("F_Time")
        self.verticalLayout_6.addWidget(self.F_Time)
        self.verticalLayout_5 = QtWidgets.QVBoxLayout()
        self.verticalLayout_5.setObjectName("verticalLayout_5")
        self.label_9 = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_9.setFont(font)
        self.label_9.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)
        self.label_9.setObjectName("label_9")
        self.verticalLayout_5.addWidget(self.label_9)
        self.temp = QtWidgets.QLabel(self.droneinfo)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.temp.setFont(font)
        self.temp.setObjectName("temp")
        self.verticalLayout_5.addWidget(self.temp)
        self.verticalLayout_6.addLayout(self.verticalLayout_5)
        self.table.addTab(self.droneinfo, "")
        self.setting = QtWidgets.QWidget()
        self.setting.setObjectName("setting")
        self.verticalLayout_7 = QtWidgets.QVBoxLayout(self.setting)
        self.verticalLayout_7.setObjectName("verticalLayout_7")
        self.horizontalLayout_16 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_16.setObjectName("horizontalLayout_16")
        self.label_11 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_11.setFont(font)
        self.label_11.setAlignment(QtCore.Qt.AlignCenter)
        self.label_11.setObjectName("label_11")
        self.horizontalLayout_16.addWidget(self.label_11)
        self.IPAddress = QtWidgets.QLineEdit(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.IPAddress.setFont(font)
        self.IPAddress.setAlignment(QtCore.Qt.AlignCenter)
        self.IPAddress.setObjectName("IPAddress")
        self.horizontalLayout_16.addWidget(self.IPAddress)
        self.verticalLayout_7.addLayout(self.horizontalLayout_16)
        self.horizontalLayout_15 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_15.setObjectName("horizontalLayout_15")
        self.horizontalLayout_14 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_14.setObjectName("horizontalLayout_14")
        self.label_27 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_27.setFont(font)
        self.label_27.setObjectName("label_27")
        self.horizontalLayout_14.addWidget(self.label_27)
        self.Height_Spinbox = QtWidgets.QSpinBox(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Height_Spinbox.setFont(font)
        self.Height_Spinbox.setMinimum(20)
        self.Height_Spinbox.setMaximum(500)
        self.Height_Spinbox.setObjectName("Height_Spinbox")
        self.horizontalLayout_14.addWidget(self.Height_Spinbox)
        self.label_28 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_28.setFont(font)
        self.label_28.setObjectName("label_28")
        self.horizontalLayout_14.addWidget(self.label_28)
        self.horizontalLayout_15.addLayout(self.horizontalLayout_14)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_15.addItem(spacerItem)
        self.horizontalLayout_13 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_13.setObjectName("horizontalLayout_13")
        self.label_31 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_31.setFont(font)
        self.label_31.setObjectName("label_31")
        self.horizontalLayout_13.addWidget(self.label_31)
        self.Rotation_Spinbox = QtWidgets.QSpinBox(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Rotation_Spinbox.setFont(font)
        self.Rotation_Spinbox.setMaximum(360)
        self.Rotation_Spinbox.setProperty("value", 45)
        self.Rotation_Spinbox.setObjectName("Rotation_Spinbox")
        self.horizontalLayout_13.addWidget(self.Rotation_Spinbox)
        self.label_32 = QtWidgets.QLabel(self.setting)
        self.label_32.setObjectName("label_32")
        self.horizontalLayout_13.addWidget(self.label_32)
        self.horizontalLayout_15.addLayout(self.horizontalLayout_13)
        self.verticalLayout_7.addLayout(self.horizontalLayout_15)
        self.horizontalLayout_33 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_33.setObjectName("horizontalLayout_33")
        self.radioButton1 = QtWidgets.QRadioButton(self.setting)
        self.radioButton1.setText("")
        self.radioButton1.setChecked(True)
        self.radioButton1.setObjectName("radioButton1")
        self.horizontalLayout_33.addWidget(self.radioButton1)
        self.horizontalLayout_34 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_34.setObjectName("horizontalLayout_34")
        self.label_35 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_35.setFont(font)
        self.label_35.setObjectName("label_35")
        self.horizontalLayout_34.addWidget(self.label_35)
        self.Master_Spinbox = QtWidgets.QSpinBox(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.Master_Spinbox.setFont(font)
        self.Master_Spinbox.setMinimum(20)
        self.Master_Spinbox.setMaximum(500)
        self.Master_Spinbox.setProperty("value", 20)
        self.Master_Spinbox.setObjectName("Master_Spinbox")
        self.horizontalLayout_34.addWidget(self.Master_Spinbox)
        self.label_36 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_36.setFont(font)
        self.label_36.setObjectName("label_36")
        self.horizontalLayout_34.addWidget(self.label_36)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_34.addItem(spacerItem1)
        self.horizontalLayout_33.addLayout(self.horizontalLayout_34)
        self.verticalLayout_7.addLayout(self.horizontalLayout_33)
        self.horizontalLayout_9 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_9.setObjectName("horizontalLayout_9")
        self.radioButton3 = QtWidgets.QRadioButton(self.setting)
        self.radioButton3.setText("")
        self.radioButton3.setObjectName("radioButton3")
        self.horizontalLayout_9.addWidget(self.radioButton3)
        self.horizontalLayout_8 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_8.setObjectName("horizontalLayout_8")
        self.horizontalLayout_41 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_41.setObjectName("horizontalLayout_41")
        self.label_41 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_41.setFont(font)
        self.label_41.setObjectName("label_41")
        self.horizontalLayout_41.addWidget(self.label_41)
        self.F_B_SpinBox = QtWidgets.QSpinBox(self.setting)
        self.F_B_SpinBox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.F_B_SpinBox.setFont(font)
        self.F_B_SpinBox.setMinimum(20)
        self.F_B_SpinBox.setMaximum(500)
        self.F_B_SpinBox.setProperty("value", 20)
        self.F_B_SpinBox.setObjectName("F_B_SpinBox")
        self.horizontalLayout_41.addWidget(self.F_B_SpinBox)
        self.label_42 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_42.setFont(font)
        self.label_42.setObjectName("label_42")
        self.horizontalLayout_41.addWidget(self.label_42)
        self.horizontalLayout_8.addLayout(self.horizontalLayout_41)
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.label_43 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_43.setFont(font)
        self.label_43.setObjectName("label_43")
        self.horizontalLayout.addWidget(self.label_43)
        self.L_R_Spinbox = QtWidgets.QSpinBox(self.setting)
        self.L_R_Spinbox.setEnabled(False)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.L_R_Spinbox.setFont(font)
        self.L_R_Spinbox.setMinimum(20)
        self.L_R_Spinbox.setMaximum(500)
        self.L_R_Spinbox.setProperty("value", 20)
        self.L_R_Spinbox.setObjectName("L_R_Spinbox")
        self.horizontalLayout.addWidget(self.L_R_Spinbox)
        self.label_44 = QtWidgets.QLabel(self.setting)
        font = QtGui.QFont()
        font.setPointSize(15)
        self.label_44.setFont(font)
        self.label_44.setObjectName("label_44")
        self.horizontalLayout.addWidget(self.label_44)
        self.horizontalLayout_8.addLayout(self.horizontalLayout)
        self.horizontalLayout_9.addLayout(self.horizontalLayout_8)
        self.verticalLayout_7.addLayout(self.horizontalLayout_9)
        self.table.addTab(self.setting, "")
        self.verticalLayout_8.addWidget(self.table)
        self.loglist = QtWidgets.QTextEdit(Dialog)
        self.loglist.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)
        self.loglist.setObjectName("loglist")
        self.verticalLayout_8.addWidget(self.loglist)
        self.horizontalLayout_5.addLayout(self.verticalLayout_8)

        self.retranslateUi(Dialog)
        self.contorlWidget.setCurrentIndex(1)
        self.table.setCurrentIndex(1)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Tello_Gui_E_ver"))
        self.Forward_M1.setText(_translate("Dialog", "↑"))
        self.Left_M1.setText(_translate("Dialog", "← "))
        self.Right_M1.setText(_translate("Dialog", "→ "))
        self.Backward_M1.setText(_translate("Dialog", "↓"))
        self.TakeOff_M1.setText(_translate("Dialog", "Take Off"))
        self.Connect_M1.setText(_translate("Dialog", "Connect"))
        self.Land_M1.setText(_translate("Dialog", "Land"))
        self.Up_M1.setText(_translate("Dialog", "Up"))
        self.CCW_M1.setText(_translate("Dialog", "CCW"))
        self.CW_M1.setText(_translate("Dialog", "CW"))
        self.Down_M1.setText(_translate("Dialog", "Down"))
        self.contorlWidget.setTabText(self.contorlWidget.indexOf(self.mode1), _translate("Dialog", "Mode1"))
        self.Forward_M2.setText(_translate("Dialog", "↑"))
        self.CCW_M2.setText(_translate("Dialog", "CCW"))
        self.CW_M2.setText(_translate("Dialog", "CW"))
        self.Backward_M2.setText(_translate("Dialog", "↓"))
        self.TakeOff_M2.setText(_translate("Dialog", "Take Off"))
        self.Connect_M2.setText(_translate("Dialog", "Connect"))
        self.Land_M2.setText(_translate("Dialog", "Land"))
        self.Up_M2.setText(_translate("Dialog", "Up"))
        self.Left_M2.setText(_translate("Dialog", "← "))
        self.Right_M2.setText(_translate("Dialog", "→ "))
        self.Down_M2.setText(_translate("Dialog", "Down"))
        self.contorlWidget.setTabText(self.contorlWidget.indexOf(self.tab2), _translate("Dialog", "Mode2"))
        self.TimerReset.setText(_translate("Dialog", "RESET"))
        self.label.setText(_translate("Dialog", "분"))
        self.label_2.setText(_translate("Dialog", "초"))
        self.label_7.setText(_translate("Dialog", "분"))
        self.label_12.setText(_translate("Dialog", "초"))
        self.label_49.setText(_translate("Dialog", "분"))
        self.label_50.setText(_translate("Dialog", "초"))
        self.label_5.setText(_translate("Dialog", "BATTERY"))
        self.label_6.setText(_translate("Dialog", "Wi-Fi SNR"))
        self.SNR_Check.setText(_translate("Dialog", "Check"))
        self.Height.setText(_translate("Dialog", "Height: 1234cm"))
        self.HeightTextFormat = "Height: %4dcm"
        self.TOF.setText(_translate("Dialog", "TOF: 1234cm"))
        self.TOF_TextFormat = "TOF: %4dcm"
        self.F_Time.setText(_translate("Dialog", "Flight Time: 00:00:00"))
        self.F_TimeTextFormat = "Flight Time: %02d:%02d:%02d"
        self.label_9.setText(_translate("Dialog", "Temperature"))
        self.temp.setText(_translate("Dialog", "Min: 00ºC Max: 00ºC"))
        self.tempTextFormat = "Min: %02dºC Max: %02dºC"
        self.table.setTabText(self.table.indexOf(self.droneinfo), _translate("Dialog", "Drone info"))
        self.label_11.setText(_translate("Dialog", "My IP  Address"))
        self.IPAddress.setText(_translate("Dialog", "192.168.10.2"))
        self.label_27.setText(_translate("Dialog", "Height(Up,Down)"))
        self.label_28.setText(_translate("Dialog", "CM"))
        self.label_31.setText(_translate("Dialog", "CCW,CW"))
        self.label_32.setText(_translate("Dialog", "º"))
        self.label_35.setText(_translate("Dialog", "Move(↑,↓,←, →,)"))
        self.label_36.setText(_translate("Dialog", "CM"))
        self.label_41.setText(_translate("Dialog", "Forward,Back(↑,↓)"))
        self.label_42.setText(_translate("Dialog", "CM"))
        self.label_43.setText(_translate("Dialog", "Left,Right(←, →) "))
        self.label_44.setText(_translate("Dialog", "CM"))
        self.table.setTabText(self.table.indexOf(self.setting), _translate("Dialog", "Setting"))

    def updateIP(self):
        ip = self.IPAddress.text()
        self.tello.local_main_ip = ip
        self.log('IP updated : %s' % ip)
    def enable(self):
        if self.radioButton1.isChecked():
            self.Master_Spinbox.setEnabled(True)
            self.F_B_SpinBox.setEnabled(False)
            self.L_R_Spinbox.setEnabled(False)
            self.updateAll()
        else:
            self.Master_Spinbox.setEnabled(False)
            self.F_B_SpinBox.setEnabled(True)
            self.L_R_Spinbox.setEnabled(True)
            self.updateLR()
            self.updateFB()
    def updateLR(self):
        self.delta_LR = self.L_R_Spinbox.value()
    def updateFB(self):
        self.delta_FB = self.F_B_SpinBox.value()
    def updateAll(self):
        self.delta_FB = self.Master_Spinbox.value()
        self.delta_LR = self.Master_Spinbox.value()
    def updateRotation(self):
        self.delta_rotate = self.Rotation_Spinbox.value()
    def updateHeight(self):
        self.delta_height = self.Height_Spinbox.value()
    def connect(self):
        _translate = QtCore.QCoreApplication.translate
        print('Connecting...')
        if self.tello.tryConnect():
            print("Connected Successful")
            self.Connect_M1.setText(_translate("Dialog", "DisConnect"))
            self.Connect_M2.setText(_translate("Dialog", "DisConnect"))
            self.Connect_M1.clicked.disconnect()
            self.Connect_M2.clicked.disconnect()
            self.Connect_M1.clicked.connect(self.disconnect)
            self.Connect_M2.clicked.connect(self.disconnect)
            self.button_on_off(True)
            self.log('connected')
        else:
            print("Connection failed")
            self.log("연결실패")
    def disconnect(self):
        _translate = QtCore.QCoreApplication.translate
        self.tello.disconnect()
        self.Connect_M1.setText(_translate("Dialog", "Connect"))
        self.Connect_M2.setText(_translate("Dialog", "Connect"))
        self.Connect_M1.clicked.disconnect()
        self.Connect_M2.clicked.disconnect()
        self.Connect_M1.clicked.connect(self.connect)
        self.Connect_M2.clicked.connect(self.connect)
        self.videoimg.setPixmap(QtGui.QPixmap(":/Picture/sponsor.jpg"))
        self.button_on_off(False)
        self.log('disconnected')
    def button_on_off(self, state):
        self.Forward_M1.setEnabled(state)
        self.Forward_M2.setEnabled(state)
        # backward
        self.Backward_M1.setEnabled(state)
        self.Backward_M2.setEnabled(state)
        # left
        self.Left_M1.setEnabled(state)
        self.Left_M2.setEnabled(state)
        # right
        self.Right_M1.setEnabled(state)
        self.Right_M2.setEnabled(state)
        # Up
        self.Up_M1.setEnabled(state)
        self.Up_M2.setEnabled(state)
        # Down
        self.Down_M1.setEnabled(state)
        self.Down_M2.setEnabled(state)
        # CW
        self.CW_M1.setEnabled(state)
        self.CW_M2.setEnabled(state)
        # CCW
        self.CCW_M1.setEnabled(state)
        self.CCW_M2.setEnabled(state)
        # takeoff
        self.TakeOff_M1.setEnabled(state)
        self.TakeOff_M2.setEnabled(state)
        # SNR Check
        self.SNR_Check.setEnabled(state)
        self.SNR_Check.setEnabled(state)
    def takeoff(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "takeoff"
        self.log(cmd)
        self.tello.send_command(cmd)
    def land(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "land"
        self.log(cmd)
        self.tello.send_command(cmd)
    def moveforward(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "forward %d" % self.delta_FB
        self.log(cmd)
        self.tello.send_command(cmd)
    def movebackward(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "back %d" % self.delta_FB
        self.log(cmd)
        self.tello.send_command(cmd)
    def moveleft(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "left %d" % self.delta_LR
        self.log(cmd)
        self.tello.send_command(cmd)
    def moveright(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "right %d" % self.delta_LR
        self.log(cmd)
        self.tello.send_command(cmd)
    def Up(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "up %d" % self.delta_height
        self.log(cmd)
        self.tello.send_command(cmd)
    def Down(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "down %d" % self.delta_height
        self.log(cmd)
        self.tello.send_command(cmd)
    def rotateCW(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "cw %d" % self.delta_rotate
        self.log(cmd)
        self.tello.send_command(cmd)
    def rotateCCW(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        cmd = "ccw %d" % self.delta_rotate
        self.log(cmd)
        self.tello.send_command(cmd)
    def check(self):
        if self.tello.socket is None:
            self.log("tello is not connected.")
            return
        self.requestSNR = True
        cmd = "wifi?"
        self.log(cmd)
        self.tello.send_command(cmd)
import Tello_rc

if __name__ == "__main__":

    import sys
    app = QtWidgets.QApplication(sys.argv)
    Dialog = QtWidgets.QDialog()
    if len(sys.argv) < 2:
        print("usage : python Tello_Gui_E_ver.py [True|False]")
        exit(0)
    if sys.argv[1] == "False":
        bObjectDetection =  False
    elif sys.argv[1] == "True":
        bObjectDetection = True
    else:
        print("잘못된 매개변수 : %s"%sys.argv[1])
        exit(0)
    ui = Ui_Dialog(Dialog, 'GPU', bObjectDetection)
    Dialog.show()
    o = app.exec_()
    if ui.tello.cap is not None:
        ui.tello.cap.release()
        print('cap release')
    sys.exit(o)
