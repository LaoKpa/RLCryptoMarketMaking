
# import sys
# import time

# import PyQt4.QtGui as qg
# import PyQt4.QtCore as qc

# app 	= qg.QApplication(sys.argv)
# table 	= qg.QTableWidget()
# tableItem 	= qg.QTableWidgetItem()

# # initiate table
# table.setWindowTitle("QTableWidget Example @pythonspot.com")
# table.resize(400, 250)
# table.setRowCount(4)
# table.setColumnCount(2)

# # set data
# table.setItem(0,0, qg.QTableWidgetItem("Item (1,1)"))
# table.setItem(0,1, qg.QTableWidgetItem("Item (1,2)"))
# table.setItem(1,0, qg.QTableWidgetItem("Item (2,1)"))
# table.setItem(1,1, qg.QTableWidgetItem("Item (2,2)"))
# table.setItem(2,0, qg.QTableWidgetItem("Item (3,1)"))
# table.setItem(2,1, qg.QTableWidgetItem("Item (3,2)"))
# table.setItem(3,0, qg.QTableWidgetItem("Item (4,1)"))
# table.setItem(3,1, qg.QTableWidgetItem("Item (4,2)"))

# table.move(50,50)

# # show table
# table.show()
# app.exec_()

# import sys
# from PyQt4.QtGui import *

# app = QApplication(sys.argv) #ignore()
# window = QWidget()
# window.setWindowTitle("Hello World")
# window.show()
  
# # [Add widgets to the widget]

# # Create some widgets (these won't appear immediately):
# nameLabel = QLabel("Name:")
# nameEdit = QLineEdit()
# addressLabel = QLabel("Address:")
# addressEdit = QTextEdit()
# table = QTableWidget()

# table.setWindowTitle("QTableWidget Example @pythonspot.com")
# table.resize(400, 250)
# table.setRowCount(4)
# table.setColumnCount(2)
# table.setItem(0,0, QTableWidgetItem("Item (1,1)"))
# table.setItem(0,1, QTableWidgetItem("Item (1,2)"))
# table.setItem(1,0, QTableWidgetItem("Item (2,1)"))
# table.setItem(1,1, QTableWidgetItem("Item (2,2)"))
# table.setItem(2,0, QTableWidgetItem("Item (3,1)"))
# table.setItem(2,1, QTableWidgetItem("Item (3,2)"))
# table.setItem(3,0, QTableWidgetItem("Item (4,1)"))
# table.setItem(3,1, QTableWidgetItem("Item (4,2)"))


# # Put the widgets in a layout (now they start to appear):
# layout = QGridLayout(window)
# layout.addWidget(nameLabel, 0, 0)
# layout.addWidget(nameEdit, 0, 1)
# layout.addWidget(addressLabel, 1, 0)
# layout.addWidget(addressEdit, 1, 1)
# layout.addWidget(table, 2, 2)
# layout.setRowStretch(2, 1)

# # [Resizing the window]

# # Let's resize the window:
# window.resize(480, 160)

# # The widgets are managed by the layout...
# window.resize(320, 180)

# # [Run the application]

# # Start the event loop...
# sys.exit(app.exec_())

import time
from PyQt4 import QtCore, QtGui
import sys


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)



class Window(QtGui.QMainWindow):

    def __init__(self):

        super(Window, self).__init__()
        self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle("PyQT tuts!")
        self.setWindowIcon(QtGui.QIcon('pythonlogo.png'))
        self.home()


    def home(self):

        self.btn = QtGui.QPushButton(self)
        self.btn.setObjectName(_fromUtf8("pb"))
        self.btn.clicked.connect(self.timer)
        self.btn.setText("Timer1")
        self.btn.resize(65,25)
        self.btn.move(100,100)

        self.btn2 = QtGui.QPushButton(self)
        self.btn2.setObjectName(_fromUtf8("pb2"))
        self.btn2.clicked.connect(self.timer2)
        self.btn2.setText("Timer2")
        self.btn2.resize(65,25)
        self.btn2.move(100,150)

        self.btn3 = QtGui.QPushButton(self)
        self.btn3.setObjectName(_fromUtf8("pb3"))
        self.btn3.clicked.connect(self.timer3)
        self.btn3.setText("Timer3")
        self.btn3.resize(65,25)
        self.btn3.move(100,200)

        self.btn4 = QtGui.QPushButton(self)
        self.btn4.setObjectName(_fromUtf8("pb4"))
        self.btn4.clicked.connect(self.timer4)
        self.btn4.setText("Timer4")
        self.btn4.resize(65,25)
        self.btn4.move(100,250)


        self.show()


    def timer(self):

        # uin = input("enter the time : ")

        when_to_stop = 10 
        # abs(int(uin))

        while when_to_stop > 0:
            m, s = divmod(when_to_stop, 60)
            h, m = divmod(m, 60)
            time_left = str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)

            # print(time_left+'\r')
            time.sleep(1.0)
            when_to_stop -= 1
            self.btn.setText(str(time_left))
            QtGui.qApp.processEvents()


    def timer2(self):

        # uin = input("enter the time : ")

        when_to_stop = 10 
        # abs(int(uin))

        while when_to_stop > 0:
            m, s = divmod(when_to_stop, 60)
            h, m = divmod(m, 60)
            time_left = str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)

            # print(time_left+'\r')
            time.sleep(1.0)
            when_to_stop -= 1
            self.btn2.setText(str(time_left))
            QtGui.qApp.processEvents()


    def timer3(self):

        # uin = input("enter the time : ")

        when_to_stop = 10
        # abs(int(uin))

        while when_to_stop > 0:
            m, s = divmod(when_to_stop, 60)
            h, m = divmod(m, 60)
            time_left = str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)

            # print(time_left+'\r')
            time.sleep(1.0)
            when_to_stop -= 1
            self.btn3.setText(str(time_left))
            QtGui.qApp.processEvents()


    def timer4(self):

        # uin = input("enter the time : ")

        when_to_stop = 10 
        # abs(int(uin))

        while when_to_stop > 0:
            m, s = divmod(when_to_stop, 60)
            h, m = divmod(m, 60)
            time_left = str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)

            # print(time_left+'\r')
            time.sleep(1.0)
            when_to_stop -= 1
            self.btn4.setText(str(time_left))
            QtGui.qApp.processEvents()




def run():


    app = QtGui.QApplication(sys.argv)
    GUI = Window()
    sys.exit(app.exec_())


run()