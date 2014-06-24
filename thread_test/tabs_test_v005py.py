from PyQt4 import QtGui, QtCore, uic
import sys

if __name__ == '__main__':

	app = QtGui.QApplication(sys.argv)
	app.setStyle("cleanLooks")
	#DATA
	data =  QtCore.QStringList()
	data << 'one' << 'two' << 'three' << 'four' << 'five'

	#MODEL
	model = QtGui.QStringListModel(data)

	listView = QtGui.QListView()
	listView.show()
	
	#BIND MODEL
	listView.setModel(model)

	combobox = QtGui.QComboBox()
	combobox.show()
	#BIND MODEL
	combobox.setModel(model)
	

	listView2 = QtGui.QListView()
	listView2.show()
	#BINF MODEL
	listView2.setModel(model)

	sys.exit(app.exec_())