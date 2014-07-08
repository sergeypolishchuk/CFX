# searching/creating 'cConfig.conf' file
# Network Configuration Functions
# this file will request, save, load and return server node's ip address
# for the current network
import inspect, os, sys, socket
import os
import sys
from platform import platform
from PyQt4 import QtGui

class cfgUI(QtGui.QDialog):# server IP Dialog
    def __init__(self, parent=None):#
        print 'ENTERING cfgUI CLASS'#
        QtGui.QDialog.__init__(self, parent)# INITIATE QT DIALOG OBJECT
        self.serverIP = QtGui.QLineEdit(self)# DEFINE IP ENTRY ELEMENT
        self.cfgIPbtn = QtGui.QPushButton('ACCEPT', self)# DEFINE ACCEPT BUTTON ELEMENT
        self.cfgIPbtn.clicked.connect(self.cfgIPValidator)# CONNECT cfgIPValidator SIGNAL TO BIND WITH ACCEPT BUTTON ACTION
        layout = QtGui.QVBoxLayout(self)# DEFINE LAYOUT for the GUI:QVBoxLayout
        layout.addWidget(self.serverIP)# ADD IP ENTRY ELEMENT TO THE LAYOUT
        layout.addWidget(self.cfgIPbtn)# ADD BUTTON ELEMENT TO THE LAYOUT

    def cfgIPValidator(self):# IP address validator
        print 'VALIDATING...'# check if user entered anything in to the IP ENTRY ELEMENT
        if self.serverIP.text():# if yes
            self.cfgIPchk(str(self.serverIP.text()))# run the cfgIPchk function on the entered string of values
        else:# if not
            print 'REJECTED'
            QtGui.QMessageBox.warning(self, 'Error', 'Please Enter a VALID IP Address')# raise an error, do not let the user proceed

    def cfgIPchk(self, cfgIP):# IP address resolver
        validIP = False# default value if resolver cannot resolve the supplied address
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)# use socket lib to check the IP
        print 'VALIDATING FORMAT'
        try:
            socket.inet_aton(cfgIP)# check if the supplied IP is in correct 'IP'-like format i.e 192.168.1.9
            print 'VALID IP FORMAT'
            try:
                s.connect((cfgIP, 5555))# check if there is a valid server machine tied to that IP, we will validate the IP if the machine responds
                print 'PORT 5555 reachable'
                print 'ACCEPTED'
                validIP = True# passed validation, going to return this at the end of the function
                self.accept()# run PyQt4 internal function for the QtGui.QDialog box called accept()
            except socket.error as e:
                print 'REJECTED, ERROR: %s' % e
                QtGui.QMessageBox.warning(self, 'Error', 'COULD NOT CONNECT TO SERVER')
        except socket.error as e:
            print 'REJECTED, ERROR: %s' % e
            QtGui.QMessageBox.warning(self, 'Error', 'INVALID IP Address Entered')
        return validIP# returning valid ip to who ever called this function

def osCheck():# check what machine the client has been executed on
    osName = []
    if os.name == 'nt':# WINDOWS
        osName = ['']
        print 'WIN'
    elif os.name == 'posix':# OSX OR LINUX
        if platform().upper().split('-')[0] == 'LINUX':# LINUX
            osName = ['home']
            print 'LIN'
        elif platform().upper().split('-')[0] == 'DARWIN':# OSX
            osName = ['home']
            print "OSX"
    return osName[0]

# CHECK IF cConfig.conf EXISTS IN THE APP DIRECTORY
def cfgChk(cfgFile):
    cfg = False# default value if cfgChk cannot the cfg file at the specified location
    if os.path.lexists(os.path.abspath('\\'.join(cfgFile))):# join path and check if file exists i.e. c:\\drobox\\cfx\\cConfig.conf
        print "CFG FILE EXISTS"
        cfg = True
    else:
        print "CFG FILE IS MISSING"
        cfg = False
    return cfg

# MAIN FUNCTION for cConfigurator.py is ran when this file is called
def main():#
    print "THIS IS THE OS WE ARE RUNNING ON"
    cfgOS = osCheck()# check what clinet os
    cfg = []# global array, this will have a collection of values after this function runs
    cfgF = 'cConfig.conf'# default name for the configuration file we are looking for
    cfgIP = ''# IP address string we are trying to obtain
    cfg.append(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))# get'pwd', find absolute path to this file, add to array
    cfg.append(cfgF)# take config file name add to array
    app = QtGui.QApplication(sys.argv)# start an instance of the QT application
    if cfgChk(cfg):# check the default location for the config file, if found then
        print "OPENING CFG FILE"
        with open(os.path.abspath('\\'.join(cfg)) , 'r') as f:# open and read the file
            print "READING CFG FILE"
            cfgIP = f.readline()# read first line
        print 'VERIFYING IP'
        cfgInput = cfgUI()# get an instance of server IP Dialog
        if cfgInput.cfgIPchk(cfgIP):# run the IP address we read form the config file though a verification function in server IP Dialog is valid:
            print 'IP VERIFIED'
            cfg.append(cfgIP)# add the IP address to a list of values to return
            cfg.append([True])
        else:# if the IP addess did not verify , we need to raise UI for the user to input a new value and verify it before proceeding
            if cfgInput.exec_() == QtGui.QDialog.Accepted:# open up the server IP Dialog, if verified then
                cfgIP = cfgInput.serverIP.text()# get the verified IP address from the USER input
                print ("HERE IS THE VERIFIED IP: %s" % cfgIP)
                f = open(os.path.abspath('\\'.join(cfg)), 'w')# lets write this verified address to the config file, create a config file
                f.write(cfgIP)# write the value
                f.close()# close the config file
                print "WRITTEN CFG FILE"
                cfg.append(cfgIP)# add the IP address to a list of values to return
                cfg.append([True])
    else:# if file was not found then
        print "USER NEEDS TO PROVIDE CFG FILE"
        cfgInput = cfgUI()# get an instance of server IP Dialog
        if cfgInput.exec_() == QtGui.QDialog.Accepted:# open up the server IP Dialog, if verified then
            cfgIP = cfgInput.serverIP.text()# get the verified IP address from the USER input
            print ("HERE IS THE VERIFIED IP: %s" % cfgIP)
            f = open(os.path.abspath('\\'.join(cfg)), 'w')# lets write this verified address to the config file, create a config file
            f.write(cfgIP)# write the value
            f.close()# close the config file
            print "WRITTEN CFG FILE"
            cfg.append(cfgIP)# add the IP address to a list of values to return
            cfg.append([True])

    [cfgOS]+cfg# add the OS value to the list of values

    return cfg# return arrayu of config value i.e. ['WIN'][dir_path]['cConfig.conf'][192.168.1.9][True]
if __name__ == '__main__':
    print 'CHECKING CONFIGURATION'
    print main()

