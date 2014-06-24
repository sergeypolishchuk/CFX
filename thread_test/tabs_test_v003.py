from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui
 
class TabWidget(QTabWidget):
    def addTab(self, widget, text):
        i=QTabWidget.addTab(self, widget, "")
        self.tabBar().setTabButton(i, QTabBar.LeftSide, QLabel(text, self))
 
class Widget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
 
        l=QVBoxLayout(self)
        jojo = QtGui.QPushButton('sortit')
        t=TabWidget(self)
        t.addTab(QWidget(self), "usera,userb")
        t.addTab(QWidget(self), "Tab 2")
        t.addTab(QWidget(self), "Tab\n3")
        t.addWidget(jojo)
        l.addWidget(t)
 
if __name__=="__main__":
    from sys import argv, exit
    a=QApplication(argv)
    w=Widget()
    w.show()
    w.raise_()
    exit(a.exec_())