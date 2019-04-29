
import sys
import time

import pickle as pk
import PyQt4.QtGui as qg

class MarketMakingGui(object):
	def __init__(self):
		self.ob_fh = open('/home/lavi/Downloads/ob.bin', 'rb')
		self.app = qg.QApplication(sys.argv)
		self.create_window()
		self.create_button()
		self.create_labels()
		self.init_table()
		self.create_layout()
		sys.exit(self.app.exec_())

	def create_window(self):
		self.window = qg.QWidget()
		self.window.setWindowTitle("Hello World")
		self.window.show()
	
	def create_button(self):
		self.btn = qg.QPushButton(self.window)
		self.btn.setObjectName("pb")
		self.btn.clicked.connect(self.callback)
		self.btn.setText("load book")
		self.btn.resize(65,25)
		self.btn.move(100,300)

	def create_labels(self):
		self.main_label = qg.QLabel("Market Making Visualisation")
		font = qg.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.main_label.setFont(font)

	def init_table(self):
		self.table = qg.QTableWidget()
		self.table.setWindowTitle("QTableWidget Example @pythonspot.com")
		self.table.resize(400, 250)
		self.table.setRowCount(25)
		self.table.setColumnCount(4)

	def create_layout(self):
		self.layout = qg.QGridLayout(self.window)
		self.layout.addWidget(self.main_label, 1, 3)
		self.layout.addWidget(self.table, 2, 2)
		self.layout.addWidget(self.btn, 3, 2)

	def callback(self):
		ob = pk.load(self.ob_fh)
		for ask, i in zip(ob['asks'], range(len(ob['asks']))):
			price_item = qg.QTableWidgetItem()
			price_item.setBackgroundColor(qg.QColor('green'))
			price_item.setText(str(ask['price']))
			amount_item = qg.QTableWidgetItem()
			amount_item.setBackgroundColor(qg.QColor('green'))
			amount_item.setText(str(ask['amount']))
			self.table.setItem(i,0, amount_item)
			self.table.setItem(i,1, price_item)
		for bid, i in zip(ob['bids'], range(len(ob['bids']))):
			price_item = qg.QTableWidgetItem()
			price_item.setBackgroundColor(qg.QColor('red'))
			price_item.setText(str(bid['price']))
			amount_item = qg.QTableWidgetItem()
			amount_item.setBackgroundColor(qg.QColor('red'))
			amount_item.setText(str(bid['amount']))
			self.table.setItem(i,2, price_item)
			self.table.setItem(i,3, amount_item)

def main():
	mmg = MarketMakingGui()

if __name__ == '__main__':
	main()
	