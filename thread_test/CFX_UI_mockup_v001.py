# CFX UI MOCKUP
from PyQt4 import QtCore, QtGui
import os, sys, tempfile, json

from srvSELUI import Ui_CFX

# class uCFG(object):
# 	"""docstring for uCFG"""
# 	# ATTRIBUTES
# 	machinename = None
# 	username = None
# 	usernamelist = None
# 	apps = None
# 	server = None
# 	serverlist = None
# 	serverports = None
# 	loadmsgamnt = None
# 	autologin = None
# 	startintray = None
# 	lastlogintimestamp = None
# 	lastlogouttimestamp = None
# 	# def __init__(self, machinename, username, usernamelist, apps, server, serverlist, serverports, loadmsgamnt):
# 	def __init__(self, arg):
# 		super(uCFG, self).__init__()
# 		self.arg = arg
		
class uNode(object):
	"""docstring for uNode"""
	# ATTRIBUTES
	machineid = None
	username = None
	machine = None
	def __init__(self, arg):
	# def __init__(self):		
		super(uNode, self).__init__()
		self.machinename = arg
		self.machineid = arg
		self.machine = arg
		
# class Window(QtGui.QDialog):# main window class for the CFX app GUI
class Window(QtGui.QMainWindow):# main window class for the CFX app GUI
	"""docstring for Window"""
	def __init__(self, *args, **kwargs):
		super(Window, self).__init__(*args, **kwargs)# QT main window GUI inherit super class from QtGui.QDialog
		self.resize(800,600)# resize the CFX app window to default size
		self.prepWindow()# run the prepWindow fucntion to add the system tray icon object and trigger event to CFX app
		self.setWindowIcon(QtGui.QIcon('C:/Users/carl/Documents/GitHub/CFX/thread_test/UI/bad.svg'))
		self.setWindowTitle('CFX')# change the title of the CFX app to "CFX"

	def prepWindow(self): # this fucntion preps additions to the main CFX window, 
		self.dicon = QtGui.QSystemTrayIcon()# adds system tray icon FX window docking capability
		self.dicon.setIcon( QtGui.QIcon('C:/Users/carl/Documents/GitHub/CFX/thread_test/UI/bad.svg'))# this sets icon image for system tray
		self.dicon.show()# this shows the icon in the system tray
		self.dicon.activated.connect(self.showWindow)# this connects the signal from the system tyray icon to the CFX window, to be able to launch CFX wondow if it has been minimized to tray
		self.prepDMenu()# this prepares the actual context menu and then attaches it to the system tray context menu
		self.cfgPATH = self.cfg_check()
		print self.cfgPATH
		self.serverWidget(self.cfgPATH[0])
		self.show()# this shows the CFX window on application launch
		# self.hide()
	def serverWidget(self, opt):
		#self.srvFrame = QtGui.QFrame()
		self.srvW = Ui_CFX()
		self.srvW.setupUi(self)
		# self.srvFrame = Ui_CFX()
		# self.srvWidget = QtGui.QHBoxLayout(self.srvFrame)
		# self.srvGoBtn = QtGui.QPushButton('GO')
		# self.srvLstCB = QtGui.QComboBox()
		# self.srvAdFld = QtGui.QLineEdit()
		# self.srvPoFld = QtGui.QLineEdit()
		# self.srvAddBtn = QtGui.QPushButton('ADD SERVER')
		# self.srvWidget.addWidget(self.srvAdFld)
		# self.srvWidget.addWidget(self.srvPoFld)
		# self.srvWidget.addWidget(self.srvAddBtn)
		# self.srvWidget.addWidget(self.srvLstCB)
		# self.srvWidget.addWidget(self.srvGoBtn)
		#self.setCentralWidget(self.srvW)
	def closeEvent(self, event):# this is the close event for the CFX window, it alerts user with promt to choices when user licks on the close incon in CFX window
		reply = QtGui.QMessageBox.question(self, 'EXIT or HIDE',"\n'Yes'   - Shutdown.\n'No'    - Dock to tray.\n", QtGui.QMessageBox.Yes | 
		QtGui.QMessageBox.No | QtGui.QMessageBox.Cancel, QtGui.QMessageBox.No)# this sets up the prompt with 3 choices YES, NO, CANCEL
		if reply == QtGui.QMessageBox.Yes:# if user clicks on yes(EXIT/SHUTDOW CFX APP) then the CFX app will proceed to close
			event.accept()# accept closing of the CFX app
		elif reply == QtGui.QMessageBox.No:# if user clicks on no(MINIMIZE/DOCK CFX APP TO TRAY) the the CFX app will proceed to hide, and can be shown if user double clicks on the system tray icon
			self.dicon.show()# show the system tray icon 
			self.hide()# hide the CFX application
			event.ignore()# ignore closing of the application event
		else:# if user clicks on the CANCEL button on the prompt, then prompt goes away no further action is required
			event.ignore()# ignore closing of the application event

	def prepDMenu(self):# this creates a context window for the system tray icon triggered by right click
		self.dmenu = QtGui.QMenu()# create context menu object
		self.dmenuCFX = QtGui.QAction("&CFX", self, triggered=self.show)# define Action for the context menu, show CFX application if hidden
		self.dmenu.addAction(self.dmenuCFX)# add functionality to the context menu, show CFX application if hidden
		self.dmenuLogger = QtGui.QAction("&Logger", self, triggered=self.show)# define Action for the context menu, launch Logger application
		self.dmenu.addAction(self.dmenuLogger)# add functionality to the context menu, launch CFX logger app
		self.dmenu.addSeparator()# separator for the menu
		self.dmenuExit = QtGui.QAction("&Exit", self, triggered=QtGui.qApp.quit)# define Action for the context menu, quit the application
		self.dmenu.addAction(self.dmenuExit)# add functionality to the context menu, exit CFX application when clicked
		self.dicon.setContextMenu(self.dmenu)# attach the context menu object to the tray icon object

	def showWindow(self, reason):# this will show the CFX application window
		if reason== 2:
			self.show()# show CFX app UI window

	def __icon_activated(self, reason):
		if reason == self.dicon.DoubleClick:# this sets up signal for doubleclicking on the system tray icon, thus unhiding the CFX app from tray
			self.show()# shows the CFX app
		elif reason == self.dicon.Context:# this triggers the system tray context menu attached to the system tray icon, triggered by right-click
			pass

	def cfg_check(self):
		cfgFILENAME = "CFGCFX.py"
		cfgDIRNAME = "CFX"
		cfgDIR = os.path.join(os.path.dirname(tempfile.gettempdir()),cfgDIRNAME)
		cfgSTAT = 1
		if not os.path.lexists(os.path.join(cfgDIR,cfgFILENAME)):
			if not os.path.lexists(cfgDIR):
				os.makedirs(cfgDIR)
			open(os.path.join(cfgDIR, cfgFILENAME),'a').close()
			cfgSTAT = 0
			# with open(os.path.join(cfgDIR, cfgFILENAME),'w') as cfgF:
			# 	for key, value in (uNode("test").__dict__).iteritems():
			# 		cfgF.write(key+"="+value+"\n")

		cfgSTAT = [cfgSTAT,(os.path.join(cfgDIR, cfgFILENAME))]
		return cfgSTAT



if __name__ == "__main__":
	app = QtGui.QApplication(sys.argv)
	win = Window()
	sys.exit(app.exec_())