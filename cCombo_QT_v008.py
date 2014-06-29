from PyQt4 import QtCore, QtGui
from cWriterAPI import cWriterObj
from cReaderAPI import cReaderObj
#import MDP
import sys, socket, webbrowser#, time, logging
### testing IP's of SBROKER MACHINES: () CHANGE LINES 21 & 61 ADDRESSES FOR THIS FILE TO RUN
### HOME: 192.168.1.100
### WORK: 192.168.1.9
###  GUR: ???.???.?.???

class writeMSG(QtCore.QObject):
	outWMSG = QtCore.pyqtSignal(str)
	outDLVR = QtCore.pyqtSignal(bool)
	def __init__(self):
		QtCore.QObject.__init__(self)
		self.wMrun = True# RUN VARIABLE SET TO ENABLE LOOP
		self.nodeID = socket.gethostname().upper()
		self.wmsgTRG = None
		# self.wcallRT = None
		self.verbose = '-v' in sys.argv
		self.writerC = cWriterObj("tcp://192.168.1.9:5555", self.verbose)
		self.wmsgTXT = None # 'HOW ARE YOU DOING'
		self.wstatus = True

	def loop(self):
		while self.wMrun:
			if self.wmsgTXT:
				self.writerC.cWsend(self.wmsgTRG, ([self.nodeID,self.wmsgTXT]))
				print "sent message to !!!!!!!!!!!!!!!%s!!!!!!!!!!!!!!" % self.wmsgTRG
				self.wstatus = False
				print ('BreakPOINT WriteMSG LOOP - REPLY was: %s' % self.writerC.cWrecv()) #### TMP
				self.rmsgREP = self.writerC.cWrecv()
				if self.rmsgREP is not None:
					if self.rmsgREP[0] == self.wmsgTXT:
						self.wstatus = True
# 						cback = ('ZMQ cWriterObj callback:'+self.rmsgREP[0]+':SENT DELIVERED CONFIRMED\n')
						dlvr = True
						self.outDLVR.emit(dlvr)
						#self.outWMSG.emit(str(cback))
					else:
						dlvr = False
						self.outDLVR.emit(dlvr)
						self.wstatus = True
				else:
					print 'No REPLY RECEIVED, CHECK CONNECTION to sBroker'#### TMP
					dlvr = False
					self.outDLVR.emit(dlvr)
					self.wstatus = True
					
				self.wmsgTXT = None
			# elif self.wcallRT:
			# 	self.writerC.cWcall(self.wmsgTRG, ([self.nodeID,self.wcallRT]))
			# 	print "call sent to sbroker"
			# 	self.wcallRT = None
			else:
				continue

class readMSG(QtCore.QObject):
	outSNDR = QtCore.pyqtSignal(str)
	outRMSG = QtCore.pyqtSignal(str)
	outFIFO = QtCore.pyqtSignal(str)
	outSESSIONS = QtCore.pyqtSignal(list)
	
	def __init__(self):
		QtCore.QObject.__init__(self)
		self.rMrun = True# RUN VARIABLE SET TO ENABLE LOOP
		self.nodeID = socket.gethostname().upper()
		self.verbose = '-v' in sys.argv
		self.readerC = cReaderObj("tcp://192.168.1.9:5555", self.nodeID, self.verbose)
		self.recvStatus = True
		self.readerC.recvState = self.recvStatus
		self.cSessions = None
		self.sFIFO = None
		self.powerDWN = False

	def loop(self):
		while self.rMrun and self.recvStatus:
			self.rmsg = self.readerC.recv(None)
			if self.rmsg and self.recvStatus:
				if self.readerC.cSessions:# print "<><<><>><><><> SESSION <><>><<>><<><<>><>\n"
					self.cSessions = self.readerC.sList
					if self.cSessions:
						if self.nodeID in self.cSessions: self.cSessions.remove(self.nodeID)
						self.outSESSIONS.emit(self.cSessions)
					else:
						pass
				elif self.readerC.sessionFIFO:
					print "FIFO passed to READ MESSAGES QThread"
					self.sFIFO = self.readerC.fList
					print "FIFO assigned to local variable"
					if self.sFIFO:
						self.sFIFO = self.sFIFO[len(self.sFIFO)-1]
						"FIFO SIGNALING "
						self.outRMSG.emit(("FIFO_ID:%s" % self.sFIFO))
						self.outFIFO.emit(str(self.sFIFO))
					else:
						print "something up with the FIFO, ERROR"
						pass
				else:# print "<><<><>><><><> MESSAGE <><>><<>><<><<>><>\n"
					self.outSNDR.emit(str(self.rmsg[0]))
					self.outRMSG.emit(str(self.rmsg[1]))
			elif self.powerDWN:# print "<><><<><><><<><<>POWERING DOWN<><><><><><><>\n"
				break
			else:
				self.readerC.destroy()# print "><<><<><><><><><> STOPPED <>><<><><><<><><"
				break

class mainWindow(QtGui.QMainWindow):
	def __init__(self, parent=None):
		QtGui.QMainWindow.__init__(self, parent)
		mwFrame = QtGui.QFrame()
		mwLabel = QtGui.QLabel('IAC AUX CHAT WINDOW')
		#
		sessionsLabel = QtGui.QLabel('SESSIONS LIST:')
		sendLabel = QtGui.QLabel('SEND OUT:')
		receiveLabel = QtGui.QLabel('RECEIVE IN:')
		#
		self.usersBOX_edit = QtGui.QTextEdit()
		self.sessions_DD = QtGui.QComboBox()
		self.recvBOX_edit = QtGui.QTextEdit()
		self.sendBOX_edit = QtGui.QTextEdit()
		self.sndMSG_btn = QtGui.QPushButton('SEND')
		self.sndRTC_btn = QtGui.QPushButton('START WebRTC CALL')
		self.endRTC_btn = QtGui.QPushButton('END WebRTC CALL')
		self.endRTC_btn.setEnabled(False)
		#
		mwLayout = QtGui.QVBoxLayout(mwFrame)
		#
		mwLayout.addWidget(mwLabel)#
		mwLayout.addWidget(sessionsLabel)
		mwLayout.addWidget(self.sessions_DD)
		mwLayout.addWidget(self.usersBOX_edit)
		mwLayout.addWidget(receiveLabel)
		mwLayout.addWidget(self.recvBOX_edit)
		mwLayout.addWidget(sendLabel)
		mwLayout.addWidget(self.sendBOX_edit)
		mwLayout.addWidget(self.sndMSG_btn)
		mwLayout.addWidget(self.sndRTC_btn)
		mwLayout.addWidget(self.endRTC_btn)
		#
		self.setCentralWidget(mwFrame)
		###
		self.wMthread = QtCore.QThread()
		self.rMthread = QtCore.QThread()
		#
		self.wM = writeMSG()
		self.rM = readMSG()
		#
		self.wM.moveToThread(self.wMthread)
		self.rM.moveToThread(self.rMthread)
		self.wMthread.started.connect(self.wM.loop)
		self.rMthread.started.connect(self.rM.loop)
		### CONNECT SIGNALS
		self.wM.outWMSG.connect(self.got_signal)
		self.wM.outDLVR.connect(self.got_dlvr)
		self.rM.outSNDR.connect(self.got_sender)
		self.rM.outRMSG.connect(self.got_signal)
		self.rM.outSESSIONS.connect(self.got_sessions)
		self.rM.outFIFO.connect(self.start_call)
		self.sndMSG_btn.clicked.connect(self.send_signal)
		self.sndRTC_btn.clicked.connect(self.send_call)
		self.endRTC_btn.clicked.connect(self.stop_call)
		#
		QtCore.QTimer.singleShot(0, self.wMthread.start)
		QtCore.QTimer.singleShot(0, self.rMthread.start)
		#
	def got_signal(self, mesg):
		self.recvBOX_edit.append('%s' % mesg)
		self.sndMSG_btn.setStyleSheet('QPushButton {color: black}')
	def got_sender(self, sndr):
		print "sndr:%s\n" % sndr
		if self.sessions_DD.findText(sndr) != -1:
			self.sessions_DD.setCurrentIndex(self.sessions_DD.findText(sndr))
		else:
			print "sender might have disconnected"
			pass
	def got_sessions(self, cSessions):
		sboxCitm = self.sessions_DD.currentText() if self.sessions_DD.count() > 0 else False
		self.sessions_DD.clear()
		self.usersBOX_edit.clear()
		self.sessions_DD.addItems(cSessions)
		if sboxCitm and (sboxCitm in cSessions): self.sessions_DD.setCurrentIndex(cSessions.index(sboxCitm))
		self.usersBOX_edit.append('%s' % cSessions)
	def send_signal(self):
		self.recvBOX_edit.append((self.rM.nodeID + ": "+self.sendBOX_edit.toPlainText())+"\n")
		self.sndMSG_btn.setEnabled(False)
		self.wM.wmsgTRG = str(self.sessions_DD.currentText())
		self.wM.wmsgTXT = str(self.sendBOX_edit.toPlainText())
		self.sendBOX_edit.clear()
	def send_call(self):
		self.sndRTC_btn.setEnabled(False)
		self.endRTC_btn.setEnabled(True)
		# self.wM.wmsgTRG = str(self.sessions_DD.currentText())
		# self.wM.wcallRT = str('caller')
		# self.rM.readerC.send_to_sbroker(MDP.W_WEBRTC,None, str(self.sessions_DD.currentText()))
		self.rM.readerC.send_to_sbroker('\008',None, str(self.sessions_DD.currentText()))
		#webbrowser.open('http://www.youtube.com/watch?v=5ydqjqZ_3oc')
	def start_call(self, fifo):
		print "START CALL INITIATED"
		if fifo:
			webSRV = str(fifo)
			#webSRV = "tcp://192.168.1.9:"+"8000/"+"GET?"+str(fifo) # EDIT THIS WITH DEFINED VARIABLES AND CORRECT VALUES
			#webbrowser.open('http://www.youtube.com/watch?v=5ydqjqZ_3oc')
			print "LAUNCHING CHROME with %s\n as FIFO id for the WebRTC call" % (fifo)
			webbrowser.open('http://'+webSRV)
		else:
			self.recvBOX_edit.append(("CFX did not supply a fifo id to start WebRTC call, try it again...\n"))
	def stop_call(self):
		self.sndRTC_btn.setEnabled(True)
		print "STOPPED CALL"
		self.endRTC_btn.setEnabled(False)

	def got_dlvr(self, dlvr):
		if dlvr:
			self.sndMSG_btn.setStyleSheet('QPushButton {color: green}')
			self.sndMSG_btn.setEnabled(True)
		else:
			self.sndMSG_btn.setStyleSheet('QPushButton {color: red}')
			self.sndMSG_btn.setEnabled(True)
	def closeEvent(self, event):
		self.rM.powerDWN = True
		self.wM.wMrun = False
		self.rM.rMrun = False
		self.wMthread.quit()
		self.wMthread.wait()
		self.rMthread.quit()
		self.rMthread.wait()

if __name__=="__main__":
	app = QtGui.QApplication(sys.argv)
	mw = mainWindow()
	mw.show()
	mw.raise_()# !!!!!!!
	sys.exit(app.exec_())
