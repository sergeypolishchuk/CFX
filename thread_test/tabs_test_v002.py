import sys
from PyQt4.QtGui import *
from PyQt4.QtCore import *
from PyQt4 import QtGui
from example_Ui import Ui_MainWindow
from filler_Ui import Form

class MainWindow(QtGui.QMainWindow, Ui_MainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.setupUi(self)

    tab_index = 1 # 1 because we already made a default tab in QtDesigner

    def LineEditChanged(self):
        findWidget = self.tabWidget.widget(self.tabWidget.currentIndex()).findChildren(QtGui.QLineEdit, "lineEdit")
        if findWidget[0].isModified() == True:
            print("LineEdit contents edited in tab page!")
            print("Name of page edited :", "'", self.tabWidget.tabText(self.tabWidget.currentIndex()),"'")

    def TabButtonPressed(self):
        print("YOU DID IT!")
        print("Current Tab Index = ", self.tabWidget.currentIndex())

    def CreateNewTab(self, tabNum):
        tab_title = "New Tab : " + str(self.tab_index)
        self.tabWidget.addTab(Form(), tab_title)

    def MainButtonPressed(self):
        self.CreateNewTab(self.tab_index)
        findWidget = self.tabWidget.widget(self.tab_index).findChildren(QtGui.QPushButton, "tabButton")
        findWidget[0].clicked.connect(self.TabButtonPressed)
        findWidget = self.tabWidget.widget(self.tab_index).findChildren(QtGui.QLineEdit, "lineEdit")
        findWidget[0].editingFinished.connect(self.LineEditChanged)
        self.tab_index += 1

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())