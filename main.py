import os
import pickle
import pymysql
import DepartmentBase
import FaceInfo
import dlib
import time
from PyQt5.QtCore import QTimer
import shutil
import numpy as np
from PIL import Image
import backup
import delete
from LoginUi import *
from Log import *
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


def get_describe_for_face(detector, pre, model, img):  # 获取图像中人脸的特征描述
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
        reply = QMessageBox.warning(FirstWindow(), "警告对话框", "未找到输入编号\t请重新输入",
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
                reply = QMessageBox.warning(FirstWindow(), "警告对话框", "未找到输入编号\t请重新输入",
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
                    record_status(MODEL_STATUS, name)
                    reply = QMessageBox.information(FirstWindow(), "通过人脸识别认证", f"{name}\n编号:{id}\n欢迎您！",
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
        reply = QMessageBox.warning(FirstWindow(), "警告对话框", "未找到输入编号\t请重新输入",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)
        return -1, 'Unknown'
    else:
        MODEL_STATUS = 3
        reply = QMessageBox.information(FirstWindow(), "通过人脸识别认证", f"{name}\n编号:{id}\n欢迎您！",
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


class LogWin(QWidget):

    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.logBut.clicked.connect(self.login)
        self.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.shadow = QtWidgets.QGraphicsDropShadowEffect(self)
        self.shadow.setOffset(0, 0)
        self.shadow.setBlurRadius(15)
        self.shadow.setColor(QtCore.Qt.black)
        self.ui.frame_92.setGraphicsEffect(self.shadow)

    def login(self):
        username = self.ui.Logname.text()
        password = self.ui.logpass.text()

        if backend.login_user(username, password):

            QMessageBox.information(self, 'Login', '登录成功')
            self.close()
            if backend.has_admin_privileges(username):
                Fin = FirstWindow()
            else:
                QMessageBox.warning(self, 'Login', '您没有管理员权限')

        else:
            QMessageBox.warning(self, 'Login', '用户名或密码错误，请重新输入')


class FirstWindow(QWidget):
    def __init__(self):

        super().__init__()
        self.last_detected_face = None
        self.ui = Ui_LoginWindow()
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
        self.ui.pushButton_in.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(0))
        self.ui.pushButton_recognize.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(1))

        self.ui.pushButton_datacon.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(2))
        self.ui.pushButton_history.clicked.connect(lambda: self.ui.stackedWidget.setCurrentIndex(3))
        self.ui.photo_Botton.clicked.connect(lambda: self.ui.stackedWidget_2.setCurrentIndex(1))
        self.ui.take_Botton.clicked.connect(lambda: self.ui.stackedWidget_2.setCurrentIndex(0))
        self.ui.pushButton_2.clicked.connect(lambda: self.ui.stackedWidget_3.setCurrentIndex(1))
        self.ui.pushButton_3.clicked.connect(lambda: self.ui.stackedWidget_3.setCurrentIndex(2))
        self.ui.pushButton_4.clicked.connect(lambda: self.ui.stackedWidget_3.setCurrentIndex(4))
        self.ui.view_all.clicked.connect(lambda: self.ui.stackedWidget_3.setCurrentIndex(0))
        self.ui.save_data_Button.clicked.connect(self.save_data)
        self.ui.save_data_Button_2.clicked.connect(self.save_data_pic)
        self.ui.open_photo_Button.clicked.connect(self.show_dialog)
        self.ui.search_button.clicked.connect(self.search_data)
        self.ui.view_all.clicked.connect(self.view_data)
        self.ui.pushButton_dep_dep.clicked.connect(self.view_depart)
        self.ui.pushButton_delete_dep.clicked.connect(self.delete_depart)
        self.ui.pushButton_9.clicked.connect(lambda: self.ui.stackedWidget_3.setCurrentIndex(3))
        self.ui.view_all_2.clicked.connect(self.view_data_2)
        self.ui.view_month_record.clicked.connect(self.view_record_month)

        self.ui.pushButton_7.clicked.connect(self.backup)
        self.ui.pushButton_10.clicked.connect(self.restore)

        self.ui.start_Button.clicked.connect(self.begin_recognize)

        self.ui.pushButton_2.clicked.connect(self.view_data)
        self.ui.pushButton_3.clicked.connect(self.view_data)
        self.ui.pushButton_4.clicked.connect(self.view_data)
        self.ui.pushButton_5.clicked.connect(self.delete_data)

        self.ui.pushButton_8.clicked.connect(self.setSchedule)

        self.ui.face_Label.setScaledContents(True)
        self.ui.image_label.setScaledContents(True)
        self.ui.cognize_label.setScaledContents(True)
        self.ui.photo_Label.setScaledContents(True)

        # 添加一个按钮用于保存人脸图像

        self.ui.save_button.clicked.connect(self.save_face_image)

        # 添加一个 QLabel 用于显示人脸图像

        # 初始化摄像头和人脸识别器
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

        self.ui.face_Label.setPixmap(pixmap)
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

    def save_face_image(self):
        if hasattr(self, 'last_detected_face'):
            print(1)
            # 裁剪人脸图像

            # 将裁剪后的图像保存到磁盘

            cv2.imwrite('detected_face.jpg', self.last_detected_face)

            pix = QPixmap('detected_face.jpg')

            self.ui.photo_Label.setPixmap(pix)

    def save_data_pic(self):
        name = self.ui.name_2.text()
        file_path = self.ui.lineEdit.text()
        password = self.ui.password_2.text()
        sex = self.ui.sex_3.currentText()
        department_id = self.ui.depart_2.text()
        role = self.ui.role_2.currentText()

        if not name or not password:
            QMessageBox.warning(self, 'Registration', '请输入姓名和密码')
            return

        if backend.register_user(name, password, sex, department_id, role):
            QMessageBox.information(self, 'Registration', '注册成功')
        else:
            QMessageBox.warning(self, 'Registration', '用户名已存在，请重新输入')
            return

        stu_id = backend.get_user_id(name)

        face_path = file_path  # 要读取的人脸图像路径
        face_fea_path = f".\\face_fea_database\\{stu_id}"  # 人脸特征文件夹路径

        os.makedirs(face_fea_path, exist_ok=True)  # 创建人脸特征文件夹

        img = np.array(Image.open(face_path))  # 打开人脸图像并转换为NumPy数组

        detector, pre, model = load_model()
        print(1)
        img_feature = get_describe_for_face(detector, pre, model, img)  # 提取特征
        print(img_feature)
        separator = ","
        vector_str = separator.join(map(str, img_feature))
        print(type(vector_str))
        fea_path = os.path.join(face_fea_path, "1.ft")  # 生成特征文件路径

        with open(fea_path, 'wb') as f:  # 打开特征文件，以二进制写模式
            pickle.dump(img_feature, f)  # 将特征数据写入特征文件

        FaceInfo.insert_facereco(stu_id, vector_str, file_path)

    def save_data(self):
        name = self.ui.name.text()
        password = self.ui.password.text()
        sex = self.ui.sex.currentText()
        department_id = self.ui.depart.text()
        role = self.ui.role.currentText()

        if not name or not password:
            QMessageBox.warning(self, 'Registration', '请输入姓名和密码')
            return

        if backend.register_user(name, password, sex, department_id, role):
            QMessageBox.information(self, 'Registration', '注册成功')
        else:
            QMessageBox.warning(self, 'Registration', '用户名已存在，或部门号不存在，请重新输入')
            return

        stu_id = backend.get_user_id(name)

        path = 'detected_face.jpg'  # 图片路径
        path2 = f'./photo/{stu_id}.jpg'

        shutil.copy2(path, path2)
        face_path = path2  # 要读取的人脸图像路径
        face_fea_path = f".\\face_fea_database\\{stu_id}"  # 人脸特征文件夹路径

        os.makedirs(face_fea_path, exist_ok=True)  # 创建人脸特征文件夹

        img = np.array(Image.open(face_path))  # 打开人脸图像并转换为NumPy数组

        detector, pre, model = load_model()
        print(1)
        img_feature = get_describe_for_face(detector, pre, model, img)  # 提取特征
        print(img_feature)
        separator = ","
        vector_str = separator.join(map(str, img_feature))
        print(type(vector_str))
        fea_path = os.path.join(face_fea_path, "1.ft")  # 生成特征文件路径

        with open(fea_path, 'wb') as f:  # 打开特征文件，以二进制写模式
            pickle.dump(img_feature, f)  # 将特征数据写入特征文件

        FaceInfo.insert_facereco(stu_id, vector_str, path2)

    def show_dialog(self):
        file_path, file_type = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                     "All Files(*);;Text Files(*.txt)")
        print(file_path)
        print(file_type)
        self.ui.lineEdit.setText(file_path)
        pixmap = QPixmap(file_path)
        self.ui.image_label.setPixmap(pixmap)

    def search_data(self):
        self.ui.search_table.setRowCount(0)
        query = self.ui.search_entry.text()

        # 查询数据并显示在表格中
        if not FaceInfo.check_duplicate(query):
            reply = QMessageBox.warning(self, "警告对话框", "未找到输入学号\t请重新输入",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
            self.ui.search_entry.clear()
            self.view_data()
        else:
            sql = "SELECT id, name, sex, role, department_id FROM Staff WHERE id=%s"
            FaceInfo.cur.execute(sql, (query,))
            result = FaceInfo.cur.fetchall()

            # 设置表格行列数以及表头
            self.ui.search_table.setRowCount(1)
            self.ui.search_table.setColumnCount(5)

            column_names = [i[0] for i in FaceInfo.cur.description]
            self.ui.search_table.setHorizontalHeaderLabels(column_names)

            # 将查询结果添加到表格中
            for row_num, row_data in enumerate(result):
                for col_num, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.ui.search_table.setItem(row_num, col_num, item)

    def view_depart(self):
        departName = self.ui.search_dep_entry.text()
        try:
            result=DepartmentBase.show_single_data(departName)

            self.ui.search_table.setRowCount(len(result))
            self.ui.search_table.setColumnCount(5)
            column_names = [i[0] for i in DepartmentBase.cur3.description]
            self.ui.search_table.setHorizontalHeaderLabels(column_names)

            for row_num, row_data in enumerate(result):
                for col_num, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.ui.search_table.setItem(row_num, col_num, item)

        except pymysql.Error as e:
            print("数据查询失败：" + str(e))

    def delete_depart(self):
        departName=self.ui.delete_dep_entry.text()
        try:
            DepartmentBase.delete_department_and_related_records(departName)
            reply = QMessageBox.information(self, "部门删除成功", f"已成功删除{departName}及其员工信息")
        except pymysql.Error as e:
            print("部门删除失败：" + str(e))

    def view_data(self):
        self.ui.search_table.setRowCount(0)
        try:
            sql = "SELECT id, name, sex, role, department_id  FROM Staff"
            FaceInfo.cur.execute(sql)
            results = FaceInfo.cur.fetchall()

            self.ui.search_table.setRowCount(len(results))
            self.ui.search_table.setColumnCount(5)
            column_names = [i[0] for i in FaceInfo.cur.description]
            self.ui.search_table.setHorizontalHeaderLabels(column_names)

            for row_num, row_data in enumerate(results):
                for col_num, col_data in enumerate(row_data):
                    item = QTableWidgetItem(str(col_data))
                    self.ui.search_table.setItem(row_num, col_num, item)
            FaceInfo.conn.commit()
        except pymysql.Error as e:
            print("数据查询失败：" + str(e))

    def view_data_2(self):
        self.ui.search_table_2.setRowCount(0)
        try:
            sql = "SELECT * FROM record"
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
            TestRecordBase.conn.commit()
        except pymysql.Error as e:
            print("数据查询失败：" + str(e))

    def view_record_month(self):
        self.ui.search_table_2.setRowCount(0)
        year=self.ui.search_year.text()
        month=self.ui.search_month.text()
        results=TestRecordBase.calculate_attendance(year+"-"+month)

        self.ui.search_table_2.setRowCount(len(results))
        self.ui.search_table_2.setColumnCount(3)
        column_names = [i[0] for i in TestRecordBase.cur2.description]
        self.ui.search_table_2.setHorizontalHeaderLabels(column_names)
        TestRecordBase.conn.commit()
        for row_num, row_data in enumerate(results):
            for col_num, col_data in enumerate(row_data):
                item = QTableWidgetItem(str(col_data))
                self.ui.search_table_2.setItem(row_num, col_num, item)


    def delete_data(self):
        employee_id = self.ui.search_entry_2.text()
        if not FaceInfo.check_duplicate(employee_id):
            reply = QMessageBox.warning(self, "警告对话框", "未找到输入学号\t请重新输入",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
            self.ui.search_entry_2.clear()
        else:
            delete.delete_employee_by_id(employee_id)
            print(f"ID为{employee_id}的员工数据已成功删除。")
            self.view_data()
            self.ui.search_entry_2.clear()

    def backup(self):
        backup.backup_database()
        reply = QMessageBox.warning(self, "数据备份", "备份成功！",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)

    def restore(self):
        backup.restore_database()
        reply = QMessageBox.warning(self, "数据恢复", "恢复成功！",
                                    QMessageBox.Yes | QMessageBox.No,
                                    QMessageBox.Yes)

    def get_pic_path(self):
        file_path, file_type = QtWidgets.QFileDialog.getOpenFileName(self, "选取文件", os.getcwd(),
                                                                     "All Files(*);;Text Files(*.txt)")
        self.ui.search_entry_4.setText(file_path)

    def setSchedule(self):
        start_time_morning=self.ui.search_entry_3.text()
        end_time_morning=self.ui.search_entry_6.text()
        start_time_afternoon=self.ui.search_entry_5.text()
        end_time_afternoon=self.ui.search_entry_4.text()
        TestRecordBase.setup_work_schedule(start_time_morning, end_time_morning, start_time_afternoon, end_time_afternoon)
        reply = QMessageBox.information(FirstWindow(), "更改时间表成功", f"上班打卡时间：{start_time_morning}-{end_time_morning}\n"
                                                                         f"下班打卡时间：{start_time_afternoon}-{end_time_afternoon}",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)

    def update_data(self):
        stu_id = self.ui.search_entry_3.text()
        name = self.ui.search_entry_5.text()
        if not FaceInfo.check_duplicate(stu_id):
            reply = QMessageBox.warning(self, "警告对话框", "未找到输入学号\t请重新输入",
                                        QMessageBox.Yes | QMessageBox.No,
                                        QMessageBox.Yes)
            self.ui.search_entry_3.clear()
        else:
            face_path = self.ui.search_entry_4.text()  # 要读取的人脸图像路径
            face_fea_path = f".\\face_fea_database\\{stu_id}"  # 人脸特征文件夹路径

            os.makedirs(face_fea_path, exist_ok=True)  # 创建人脸特征文件夹

            img = np.array(Image.open(face_path))  # 打开人脸图像并转换为NumPy数组

            detector, pre, model = load_model()
            print(1)
            img_feature = get_describe_for_face(detector, pre, model, img)  # 提取特征
            print(img_feature)
            separator = ","
            vector_str = separator.join(map(str, img_feature))
            print(type(vector_str))
            fea_path = os.path.join(face_fea_path, "1.ft")  # 生成特征文件路径

            with open(fea_path, 'wb') as f:  # 打开特征文件，以二进制写模式
                pickle.dump(img_feature, f)  # 将特征数据写入特征文件
            FaceInfo.update_name_facereco(stu_id, name, vector_str, self.ui.search_entry_4.text())
            self.view_data()


if __name__ == '__main__':
    QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    # Fin = FirstWindow()
    win = LogWin()
    win.show()

    sys.exit(app.exec_())
