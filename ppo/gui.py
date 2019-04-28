import sys
import time
from PyQt4.QtGui import *

app = QApplication(sys.argv) #ignore()
window = QWidget()
window.setWindowTitle("Hello World")
window.show()
  
# [Add widgets to the widget]

# Create some widgets (these won't appear immediately):
nameLabel = QLabel("Name:")
nameEdit = QLineEdit()
addressLabel = QLabel("Address:")
addressEdit = QTextEdit()
table = QTableWidget()

table.setWindowTitle("QTableWidget Example @pythonspot.com")
table.resize(400, 250)
table.setRowCount(4)
table.setColumnCount(2)
table.setItem(0,0, QTableWidgetItem("Item (1,1)"))
table.setItem(0,1, QTableWidgetItem("Item (1,2)"))
table.setItem(1,0, QTableWidgetItem("Item (2,1)"))
table.setItem(1,1, QTableWidgetItem("Item (2,2)"))
table.setItem(2,0, QTableWidgetItem("Item (3,1)"))
table.setItem(2,1, QTableWidgetItem("Item (3,2)"))
table.setItem(3,0, QTableWidgetItem("Item (4,1)"))
table.setItem(3,1, QTableWidgetItem("Item (4,2)"))

def timer():
    when_to_stop = 10 
    while when_to_stop > 0:
        m, s = divmod(when_to_stop, 60)
        h, m = divmod(m, 60)
        time_left = str(h).zfill(2) + ":" + str(m).zfill(2) + ":" + str(s).zfill(2)
        time.sleep(1.0)
        when_to_stop -= 1
        btn.setText(str(time_left))
        QtGui.qApp.processEvents()

btn = QPushButton(window)
btn.setObjectName("pb")
btn.clicked.connect(timer)
btn.setText("Timer1")
btn.resize(65,25)
btn.move(100,300)

# Put the widgets in a layout (now they start to appear):
layout = QGridLayout(window)
# layout.addWidget(nameLabel, 0, 0)
# layout.addWidget(nameEdit, 0, 1)
# layout.addWidget(addressLabel, 1, 0)
# layout.addWidget(addressEdit, 1, 1)
layout.addWidget(table, 2, 2)
layout.addWidget(btn, 3, 2)
layout.setRowStretch(2, 1)

# [Resizing the window]

# Let's resize the window:
window.resize(480, 160)

# The widgets are managed by the layout...
window.resize(320, 180)

# [Run the application]

# Start the event loop...
sys.exit(app.exec_())
