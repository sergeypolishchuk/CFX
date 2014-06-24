from PyQt4 import QtGui, QtCore, uic
import sys

if __name__ == '__main__':

	app = QtGui.QApplication(sys.argv)
	app.setStyle("cleanLooks")

	data =  QtCore.QStringList()
	data << 'one' << 'two' << 'three' << 'four' << 'five'

	listWidget = QtGui.QListWidget()
	listWidget.show()
	listWidget.addItems(data)

	count = listWidget.count()
	for i in range(count):
		item = listWidget.item(i)
		item.setFlags(item.flags() | QtCore.Qt.ItemIsEditable)

	comboBox = QtGui.QComboBox()
	comboBox.show()
	comboBox.addItems(data)


	sys.exit(app.exec_())