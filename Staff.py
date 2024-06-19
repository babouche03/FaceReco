import os
import pickle
import pymysql
import FaceInfo
import Csv
import dlib
import time
from PyQt5.QtCore import QTimer
import shutil
import numpy as np
from PIL import Image
from staffWin import *
import sys
import cv2
import TestRecordBase
import backend
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QWidget, QApplication, \
    QTableWidgetItem, QMessageBox, QDialog

detector = dlib.get_frontal_face_detector()
pre = dlib.shape_predictor("./models/shape_predictor_68_face_landmarks.dat")

staffID = ""

STATUS_DICT = {0: r'等待打卡中 (*^_^*)',
               1: r'正在加载模型 (⊙o⊙)...',
               2: r'正在匹配中，请稍等...',
               3: r'o(*￣▽￣*)ブ 打卡成功！欢迎您, ',
               4: r'(ㄒoㄒ)~~ 打卡失败，请重试！'}


def Eu(a, b):  # 距离函数
    return np.linalg.norm(np.array(a) - np.array(b), ord=2)


def load_model():  # 加载人脸识别模型
    detector = dlib.get_frontal_face_detector()
    path_pre = "./models/shape_predictor_68_face_landmarks.dat"  # 68点模型
    pre = dlib.shape_predictor(path_pre)

    path_model = "./models/dlib_face_recognition_resnet_model_v1.dat"  # resent模型
    model = dlib.face_recognition_model_v1(path_model)

    return detector, pre, model


def get_describe_for_face(detector, pre, model, img):  # 获取图像中人脸的特征描述s
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    det_img = detector(gray, 0)
    try:
        shape = pre(img, det_img[0])
        know_encode = model.compute_face_descriptor(img, shape)
    except:
        return -1
    return know_encode


def rect2bb(rect):
    x1 = rect.left()
    y1 = rect.top()
    x2 = rect.right()
    y2 = rect.bottom()

    return (x1, y1), (x2, y2)


def shape_to_np(shape, dtype="int"):
    coords = np.zeros((68, 2), dtype=dtype)
    for i in range(0, 68):
        coords[i] = (shape.part(i).x, shape.part(i).y)
    return coords


def record_status(status, name=None):  # 记录识别状态
    f = open('../recog_status.txt', 'w', encoding='utf-8')
    if status == 3:  # 打卡成功
        info = STATUS_DICT[status] + name
    else:
        info = STATUS_DICT[status]
    f.write(info)
    f.close()


def match_face(unknown_img, face_dir, stu_lists, detector, pre, model, thres=0.4, min_thres=0.45):
    print(90)
    global staffID
    '''
    
    :param unknown_img: 待检测图片
    :param face_dir: 人脸库
    :param stu_lists: 该课程的所有学生列表，【（id, name）】
    :param detector: 检测器
    :param pre: 关键点模型
    :param model: 检测模型
    :return: 匹配结果
    通过人脸识别匹配待检测图片和人脸库中的人脸
    '''

    MODEL_STATUS = 1
    record_status(MODEL_STATUS)

    # detector, pre, model = load_model()

    MODEL_STATUS = 2
    record_status(MODEL_STATUS)

    # 获取待检测图片的encode
    unknown_encod = get_describe_for_face(detector, pre, model, np.array(unknown_img))

    print("提取特征向量成功")
    if unknown_encod == -1:
        record_status(4)
        print('无法识别摄像头中的人脸')
        reply = QMessageBox.warning(Staff(), "警告对话框", "无法识别摄像头中的人脸",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        return -1, 'Unknown'

    stus_conf = {stu[0]: [stu[1], 2] for stu in stu_lists}
    for id, name in stu_lists:
        # 获取当前学生的人脸地址
        stu_face_dir = face_dir + '/' + str(id)
        for img_name in os.listdir(stu_face_dir):
            img_path = os.path.join(stu_face_dir, img_name)
            # get encode if necessary
            # img = np.array(Image.open(img_path))
            # know_encode = get_describe_for_face(detector, pre, model, img)
            ########## 这里是已经预处理好了特征，直接用，更快一些  ##########
            f = open(img_path, 'rb')
            know_encode = pickle.load(f)
            if know_encode == -1:
                record_status(4)
                print('无法识别人脸库中的人脸')
                reply = QMessageBox.warning(Staff(), "警告对话框", "无法识别人脸库中的人脸",
                                            QMessageBox.Yes | QMessageBox.No,
                                            QMessageBox.Yes)
                return -1, 'Unknown'  # 人脸库一般不存在这种情况！！！必须保证高质量人脸
            # 如果检测到差距小于阈值，认为检测成功， 退出
            distance = Eu(know_encode, unknown_encod)

            if distance > min_thres:
                break  # 这个人必然不是
            else:
                if distance < thres:  # 阈值很小了
                    MODEL_STATUS = 3

                    staffID = id
                    record_status(MODEL_STATUS, name)
                    reply = QMessageBox.information(Staff(), "通过人脸识别认证", f"{name}\n员工号:{id}\n欢迎您！",
                                                    QMessageBox.Yes | QMessageBox.No,
                                                    QMessageBox.Yes)
                    TestRecordBase.insert_record(id, name,
                                                 time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

                    print(id, name)
                    return id, name
                else:  # 阈值一般
                    stus_conf[id][1] = min(stus_conf[id][1], distance)
    # print(stus_conf)
    res = sorted(stus_conf.items(), key=lambda x: x[1][1])[0]
    print(res)

    id, (name, conf) = res
    if conf > min_thres:
        MODEL_STATUS = 4
        record_status(MODEL_STATUS)
        reply = QMessageBox.warning(Staff(), "警告对话框", "未找到输入编号\t请重新输入",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        return -1, 'Unknown'
    else:
        MODEL_STATUS = 3

        staffID = id
        reply = QMessageBox.information(Staff(), "通过人脸识别认证", f"{name}\n员工号:{id}\n欢迎您！",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
        TestRecordBase.insert_record(id, name, time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))
        record_status(MODEL_STATUS, name)
        print(id, name)

        return id, name


def compare_face(img):
    print(img)
    detector, pre, model = load_model()
    stu_lists = FaceInfo.order()
    # stu_lists = [(20221000, '杨幂'), (20221001, '钱全'), (20221002, '葛娟'), (20221003, '卫雅'), (20221004, '王宁'),
    #             (20221005, '韩惠'),(20221006, '邹慧'), (20221010, '李鑫')]
    result = match_face(img, './face_fea_database', stu_lists, detector, pre, model)
    print(result)


class Staff(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QtCore.Qt.black)
        self.ui.frame.setGraphicsEffect(self.shadow)

        self.ui.pushButton.clicked.connect(QApplication.quit)
        self.ui.pushButton_6.clicked.connect(self.showMinimized)
        self.ui.pushButton_recognize.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))
        self.ui.pushButton_history.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))
        self.ui.view_all_2.clicked.connect(self.view_data_2)

        self.ui.start_Button.clicked.connect(self.begin_recognize)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

        # 启动界面更新定时器
        self.update_timer = QTimer(self)
        self.update_timer.timeout.connect(self.update_frame)
        self.update_timer.start(100)  # 更新频率为每100毫秒

        self.faces = []

        self.show()

    def update_frame(self):

        ret, frame = self.cap.read()
        if not ret:
            return
        rects = detector(frame, 0)

        for obj in rects:
            # print(dir(obj))
            pt1, pt2 = rect2bb(obj)
            cv2.rectangle(frame, pt1, pt2, (0, 255, 0), 2)

            shapes = pre(frame, obj)
            shapes = shape_to_np(shapes)
            for (x, y) in shapes:
                cv2.circle(frame, (x, y), 1, (255, 0, 0), -1)

        # 将图像显示在界面上
        rgb_image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = 3 * w
        q_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format_RGB888)

        pixmap = QPixmap.fromImage(q_image)

        self.ui.cognize_label.setPixmap(pixmap)

        # 存储最后检测到的人脸图像
        self.last_detected_face = frame

    def begin_recognize(self):
        print(self.last_detected_face)
        cv2.imwrite('unknown_face.jpg', self.last_detected_face)
        print(8)
        img = Image.open('unknown_face.jpg')
        print("br成功")
        compare_face(img)

    def view_data_2(self):
        self.ui.search_table_2.setRowCount(0)
        global staffID
        if staffID == "":
            reply = QMessageBox.warning(Staff(), "警告对话框", "您未登录\t请先进行人脸识别",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
            return
        try:
            TestRecordBase.select_own_record(staffID)
            sql = "SELECT * FROM own_record"
            TestRecordBase.cur2.execute(sql)
            results = TestRecordBase.cur2.fetchall()

            self.ui.search_table_2.setRowCount(len(results))
            self.ui.search_table_2.setColumnCount(4)
            column_names = [i[0] for i in TestRecordBase.cur2.description]
            self.ui.search_table_2.setHorizontalHeaderLabels(column_names)

            for row_num, row_data in enumerate(results):
                for col_num, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.ui.search_table_2.setItem(row_num, col_num, item)
        except pymysql.Error as e:
            print("数据查询失败：" + str(e))

if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)

    win = Staff()
    win.show()

    sys.exit(app.exec_())
