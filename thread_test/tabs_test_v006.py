from PyQt4 import QtGui, QtCore, uic
import sys



class PalleteListModel(QtCore.QAbstractListModel):

	def  __init__(self, colors = [], parent = None):
		QtCore.QAbstractListModel.__init__(self, parent)
		self.__colors = colors

	def headerData(self, section, orientation, role):
		if role ==  QtCore.Qt.DisplayRole:

			if orientation == QtCore.Qt.Horizontal:
				return QtCore.QString("Palette")
			else:
				return QtCore.QString("Color %1").arg(section)

	def rowCount(self, parent):
		return len(self.__colors)

	def data(self, index, role):
		if role == QtCore.Qt.ToolTipRole:
			return "hex code: "+self.__colors[index.row()].name()

		if role == QtCore.Qt.DecorationRole:
			row = index.row()
			value = self.__colors[row]
			pixmap = QtGui.QPixmap(26,26)
			pixmap.fill(value)

			icon = QtGui.QIcon(pixmap)
			return icon

		if role == QtCore.Qt.DisplayRole:

			row = index.row()
			value = self.__colors[row]
			return value.name()

	def flags(self, index):

		return QtCore.Qt.ItemIsEditable | QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

	def setData(self, index, value, role = QtCore.Qt.EditRole):

		if role == QtCore.Qt.EditRole:

			row = index.row()

			color = QtGui.QColor(value)

			if color.isValid():
				self.__colors[row] = color
				self.dataChanged.emit(index, index)
				return True
		return False

if __name__ == '__main__':

	app = QtGui.QApplication(sys.argv)
	app.setStyle("plastique")


	listView = QtGui.QListView()
	listView.show()
	

	treeView = QtGui.QTreeView()
	treeView.show()

	combobox = QtGui.QComboBox()
	combobox.show()

	tableView = QtGui.QTableView()
	tableView.show()
	
	red = QtGui.QColor(255,0,0)
	green = QtGui.QColor(0,255,0)
	blue = QtGui.QColor(0,0,255)

	model = PalleteListModel([red, green, blue])

	listView.setModel(model)
	treeView.setModel(model)
	combobox.setModel(model)
	tableView.setModel(model)

	sys.exit(app.exec_())