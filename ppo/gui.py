
import sys
import time

import pickle as pk
import PyQt4.QtGui as qg

class MarketMakingGui(object):
	def __init__(self, model):
		self.ob_fh = open('/home/lavi/Downloads/ob.bin', 'rb')
		self.app = qg.QApplication(sys.argv)
		self.create_window()
		self.create_button()
		self.create_labels()
		self.init_table()
		self.create_layout()
		self.app.exec_()
		sys.exit()

	def create_window(self):
		self.window = qg.QWidget()
		self.window.setWindowTitle("Market Making Simulation")
		self.window.resizeEvent = self.windowResizeCallback
		self.window.show()
	
	def create_button(self):
		self.btn = qg.QPushButton(self.window)
		self.btn.setObjectName("pb")
		self.btn.clicked.connect(self.callback)
		self.btn.setText("load book")

	def create_labels(self):
		self.main_label = qg.QLabel("Market Making Visualisation")
		font = qg.QFont()
		font.setPointSize(12)
		font.setBold(True)
		font.setWeight(75)
		self.main_label.setFont(font)
		self.inv_label = qg.QLabel("Inventory:")
		self.funds_label = qg.QLabel("Funds:")
		self.worth_label = qg.QLabel("Worth:")


	def init_table(self):
		self.table = qg.QTableWidget()
		self.table.setRowCount(25)
		self.table.setColumnCount(4)
		self.table.setHorizontalHeaderLabels\
		(['ask_amount', 'ask_price', 'bid_price', 'bit_amount'])

	def create_layout(self):
		self.layout = qg.QFormLayout(self.window)
		self.layout.addWidget(self.main_label)
		self.layout.addWidget(self.inv_label)
		self.layout.addWidget(self.worth_label)
		self.layout.addWidget(self.funds_label)
		self.layout.addWidget(self.table)
		self.layout.addWidget(self.btn)

	def organize_widgets(self):
		self.main_label.move(300, 10)
		self.inv_label.move(10, 50)
		self.worth_label.move(10, 70)
		self.funds_label.move(10, 90)
		self.table.move(200, 50)
		self.table.resize(450, 800)
		self.btn.move(10, 110)
		self.btn.resize(100, 40)

	def windowResizeCallback(self, obj):
		self.organize_widgets()

	def print_order_book(self, ob):
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

	def callback(self):
		ob = pk.load(self.ob_fh)
		self.print_order_book(ob)

def main():
	mmg = MarketMakingGui()

if __name__ == '__main__':
	main()
	