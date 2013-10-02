#sBroker.py
#IMPORT PACKAGES
import logging
import sys
import time
import uuid
import socket
from binascii import hexlify
#IMPORT PYZMQ EXTANSION LIBRARY
import zmq
#IMPORT MESSAGE HELPER FUNCTIONS
from zhelpers import dump
#IMPORT LOCAL MAJORDOMO PROTOCOL DEFINISHIONS
import MDP

#DEFINE CLASS: CSERVICE.OBJECT (SERVICE)
#   THIS CLASS DEFINES REGISTERED ONE SERVICE AND
#   LISTS: CREADER REQUESTS / CWRITERS
class cService(object):
    """a single Service"""
    name = None# Service name
    requests = None# List of CWRITER requests
    waiting = None# List of waiting CREADERS

    def __init__(self, name):
        self.name = name
        self.requests = []
        self.waiting = []

#DEFINE CLASS: CREADER.OBJECT (WORKER) 
#   ACTIVE OR IDLE READER
class cReader(object):
    """a Worker, idle or active"""
    identity = None# hex Identity of CREADER
    address = None# Address to route to
    service = None# Owning service, if known
    expiry = None# expires at this point, unless heartbeat

    def __init__(self, identity, address, lifetime):
        self.identity = identity
        self.address = address
        self.expiry = time.time() + 1e-3*lifetime

#DEFINE CLASS: SBROKER.OBJECT (MAJOR DOMO SBROKER)
#   THIS CLASS DEFINES VARIOUS SBROKER ELEMENTS AND FUNCTIONS
class sBroker(object):
    # We'd normally pull these from config data file
    INTERNAL_SERVICE_PREFIX = "mmi."
    HEARTBEAT_LIVENESS = 3# 3-5 is reasonable > TUNABLE
    HEARTBEAT_INTERVAL = 2500# msecs > TUNABLE
    HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS
    # ------------------------------------------------------------
    #   zmq socket vars
    ctx = None# Our ZMQ context
    socket = None# Socket for CWRITERS & CREADERS
    poller = None# our Poller for said socket
    #   management vars
    heartbeat_at = None# When to send HEARTBEAT
    cservices = None# known CSERVICES (registered SESSIONS from CREADER & CWRITER COMBOS)
    creaders = None# known CREADERS (registered CREADER SESSIONS)
    waiting = None# idle CREADERS
    #   webserver vars
    WebRTC_SRV_addr = None # !!!!!!!!!!
    WebRTC_SRV_port = None # !!!!!!!!!!
    #   logging var
    verbose = True# Print activity to stdout, default FALSE
    # ---------------------------------------------------------------------
    # SBROKER CLASS INIT
    def __init__(self, verbose=True):#def FALSE
        """Initialize broker state."""
        self.verbose = verbose
        self.WebRTC_SRV_addr = socket.gethostbyname(socket.getfqdn())#(socket.gethostname())
        self.WebRTC_SRV_port = 8000
        #print "RE$OLVED SBROKER ADDRESS: %s\n" % self.WebRTC_SRV_addr
        self.cservices = {}
        self.creaders = {}
        self.waiting = []
        self.fifolist = []
        self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL
        self.ctx = zmq.Context()
        self.socket = self.ctx.socket(zmq.ROUTER)
        self.socket.linger = 0
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)
        logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
                level=logging.INFO)
    # ---------------------------------------------------------------------
    # SBROKER CLASS FUNCTIONS
    #   SBROKER MEDIATE FUNCTION
    def mediate(self):#Main SBROKER work happens here, TEST ALL INCOMING MESSAGES FOR VALIDITY
        while True:# LOOP
            try:
                items = self.poller.poll(self.HEARTBEAT_INTERVAL)# SET POLLING INTERVAL ON SOCKET
            except KeyboardInterrupt:#STOP LOOP IF CTRL+C IS PRESSED
                break# Interrupted
            if items:# IF DATA CAME IN ON POLLING SOCKET
                msg = self.socket.recv_multipart()# ASSIGN INCOMING MESSAGE TO 'MSG' LIST VARIABLE
                if self.verbose:
                    logging.info("I: received message:")
                    dump(msg)

                sender = msg.pop(0)# ITEM.0 IN MSG IDENTIFIES THE CWRITER
                print "00A INCOMING: sender was: %s\n" % sender
                empty = msg.pop(0)# ITEM.1 IN MSG IDENTIFIES EMPTY DELIMITER
                assert empty == ''# CHECK IF EMPTY DELIMITER IS ACTUALLY EMPTY
                print "00B INCOMING: empty was: %s\n" % empty
                header = msg.pop(0)# ITEM.2 IN MSG IDENTIFIES CWRITER THAT SENT THE MESSAGE
                print "00C INCOMING: header was: %s\n" % header

                if (MDP.C_CLIENT == header):# CHECK MDP PROTOCOL AGAINST CWRITER TO CHECK THAT CWRITER LINKED TO SOCKET
                    self.process_cwriter(sender, msg)# START PROCESSING THE CWRITER, RUN PROCESSING FUNCTION ON IT
                elif (MDP.W_WORKER == header):# CHECK MDP PROTOCOL AGAINST CREADER TO CHECK THAT CREADER LINKED TO SOCKET
                    self.process_creader(sender, msg)# START PROCESSING THE CWRITER, RUN PROCESSING FUNCTION ON IT
                else:# INVALIDATE MESSAGE IF IT DIN'T COME FROM A CREADER OR A CWRITER, OR WAS INVALIDLY CONSTRUCTED
                    logging.error("E: invalid message:")
                    dump(msg)
            self.purge_creaders()# RUN FUNCTION TO CHECK FOR REMOVED/DISCONNECTED CREADERS AND DELETE THEM AND THEIR SESSIONS
            self.send_heartbeats()# RUN FUNCTION FOR SENDING HEARTBEATS TO CREADERS THAT ARE IN ACTIVE SESSIONS LIST

    # START OF SBROKER FUNCTIONS
    #   SBROKER DESTROY FUNCTION
    def destroy(self):# DISCONNECT ALL CONNECTED CREADERS, AND DESTROY THE ZMQ CONTEXT
        while self.creaders:# RUN THROUGH ALL REGISTERED CREADERS , FOR EACH ONE :
            self.delete_creader(self.creaders[0], True)# SEND FUNCTION TO DELETE CREADER
        self.ctx.destroy(0)# AFTER DELETING ALL CREADERS, DESTROY ZMQ CONTEXT, SBROKER SAFELY TERMINATED CONNECTIONS

    #   CWRITER PROCESSING MESSAGE FUNCTION. what to do with message that came from CWRITER
    def process_cwriter(self, sender, msg):
        assert len(msg) >= 2# check if msg list has more then 2 items in it:CSERVICE + body
        cservice = msg.pop(0)# ITEM.1 IN MSG IDENTIFIES CSERVICE NAME
        msg = [sender, ''] + msg# rewrap message, setting reply message to CWRITER sender, as list 0.CSERVICE NAME,1.EMPTY DELIMITER,2.MESSAGE
        if cservice.startswith(self.INTERNAL_SERVICE_PREFIX):# IF CSERVICE ".mmc", send CWRITER REQUEST for processing to
            self.service_internal(cservice, msg)# SERVICE INTERNAL FUNCTION
        else:# IF NOT then send to:
            self.dispatch(self.require_cservice(cservice),msg)# DISPATCH FUNCTION
    #   CREADER PROCESSING MESSAGE FUNCTION. what to do with message that came from CREADER
    def process_creader(self, sender, msg):
        assert len(msg) >= 1# CHECK THAT MESSAGE HAS AT LEAST ONE ITEM, COMMAND
        command = msg.pop(0)# ITEM.0 IN MSG IDENTIFIES THE COMMAND
        print "001 INCOMING : COMMAND %s\n" % command
        creader_ready = hexlify(sender) in self.creaders# LOCATE SENDER IN CREADERS LIST
        print "002 INCOMING : CREADER_READY %s\n" % creader_ready
        creader = self.require_creader(sender)# ASSIGN TO CREADER VARIABLE
        print "003 INCOMING : CREADER %s\n" % creader
        if (MDP.W_READY == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_READY THEN:
            assert len(msg) >= 1# ASSERT IF MESSAGE IS LONG ENOUGH TO PROCESS
            cservice = msg.pop(0)# ITEM.0 IN MSG IDENTIFIES CSERVICE TO USE ON THAT MESSAGE
            # Not first command in session or Reserved cservice name
            if (creader_ready or cservice.startswith(self.INTERNAL_SERVICE_PREFIX)):# IF CREADER IS FOUND, OR RESERVED CSERVICE NAME THEN:

                self.delete_creader(creader, True)# DELETE CREADER
            else:# ELSE ATTACH CREADER TO CSERVICE AND MARK CREADER AS WAITING/IDLE
                creader.service = self.require_cservice(cservice)# FIND CSERVICE FOR CREADER
                self.creader_waiting(creader)# MARK CREADER AS WAITING/IDLE

        elif (MDP.W_REPLY == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_REPLY THEN:
            if (creader_ready):# IF CREADER IS MARKED AS READY
                # Remove & save client return envelope and insert the
                # protocol header and service name, then rewrap envelope.
                print "got REPLY message, here is what it looks like: %s\n" % msg# !!!!!!!!!!!!!!!!
                client = msg.pop(0)# ITEM.0 IDENTIFIES CLIENT THAT SENT THE MESSAGE
                empty = msg.pop(0)# ITEM.1 IDENTIFIES EMPTY DELIMITER 
                msg = [client, '', MDP.C_CLIENT, creader.service.name] + msg# REWRAP MSG ENVELOPE, IT BECOMES: [0.CLIENT,1.EMPTY,2.MDP HEADER,3.CSERVICEN,4.MESSAGE]
                self.socket.send_multipart(msg)# SEND MESSAGE TO CREADER
                self.creader_waiting(creader)# MARK CREADER AS WAITING AFTER SENDING MSG
            else:# ELSE, CREADER IS NOT READY:
                self.delete_creader(creader, True)# DELETE CREADER, BY PASSING CREADER TO CREADER_DELETE FUNCTION

        elif (MDP.W_HEARTBEAT == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_HEARTBEAT THEN:
            if (creader_ready):# IF CREADER IS MARKED AS READY
                ###TD###TESTING PURPOSES ONLY
                slist = dict.keys(self.cservices)# COLLECT ALL KEYS FROM CSERVICES DICTIONARY INTO A LIST           
                self.send_to_creader(creader, MDP.W_SESSIONS, None, slist, None)# USE A SEND COMMAND TO SEND THE LIST OF CSERVICES TO CREADER
                #print "REPLIED TO HEARTBEAT CMD FROM %s WITH LIST IF ACTIVE SESSIONS: %s TO %s" % (creader.service.name,slist,creader.service.name)# PROCESS CALLBACK
                ###TD###REMOVE PRINTING LATER
                creader.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY# RESET CREADER'S HEARTBEAT EXPIRY VALUE
                #self.creader_waiting(creader)#added
            else:# ELSE IF CREADER IS NOT READY:
                self.delete_creader(creader, True)# DELETE CREADER, BY PASSING CREADER TO CREADER_DELETE FUNCTION
                self.purge_creaders()# !!!!!!!!!!!!!!!!!!!!!!!!!!!

        elif (MDP.W_WEBRTC == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_WEBRTC THEN:
            if (creader_ready):
                print "WEBRTC COMMAND HERE IS THE MESSAGE:%s\n" % msg
                a_cRD = creader
                #print "CSERVICES: %s\n" % self.cservices
                #print "CREADERS: %s\n" % self.creaders
                print "CREADERS KEYS: %s\n" % self.creaders.keys()
                print "CREADERS VALUES: %s\n" % self.creaders.values()
                #self.maintenance(self.creaders, 'creaders.txt')
                #for x in self.creaders.keys(): if x.service and x.service == (self.require_cservice(msg[0])):
                b_cRD = self.find_creader_by_cservice(msg[0])
                fifoID = self.generate_fifo()
                print "VIDEO CALL RECEVICED BY SBROKER:A>%s is calling B>%s\n" % (a_cRD, b_cRD)
                if fifoID and a_cRD and b_cRD:
                    print "VIDEO CALL ID IS  %s\n" % fifoID
                    print "GOING TO NOTIFY EACH CREADER IN THE CALL TO ACESS THE WEBSERVER:%s ON PORT:%s\n" % (self.WebRTC_SRV_addr,self.WebRTC_SRV_port)
                    print "AND INSTRUCT TO USE DEFAULT BROWSER(CHROME) TO LOAD index.html WITH GET REQUEST FIFO_ID"
                    fifoID = (str(self.WebRTC_SRV_addr) +":"+ str(self.WebRTC_SRV_port) +"/GET?"+ str(fifoID))
                    # self.send_to_creader(creader, MDP.W_WEBRTC, None, fifoID, None)
                    self.send_to_creader(a_cRD, MDP.W_WEBRTC, None, fifoID, None)
                    self.send_to_creader(b_cRD, MDP.W_WEBRTC, None, fifoID, None)
                    print "WEBSERVER ADDRESS AND GET REQ WITH FIFO ID: %s SENT TO CALLER and CALLEE\n" % fifoID
                    pass
                else:
                    print "FAILED TO GENERATE A FIFO ID or FAILED TO RESOLVE CALLER AND CALLEE"
                    pass
            else:
                print "VIDEO CALL FAILURE"
                pass

        elif (MDP.W_POWERDOWN == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_POWERDOWN THEN:
            if (creader_ready):
                print "POWER DOWN RECEIVED BY SBROKER FOR:%s\n" % creader
                pass
            else:
                print "POWER DOWN FAILURE"
                pass

        elif (MDP.W_DISCONNECT == command):# CHECK INCOMING MESSAGE COMMAND AGAINST MDP IF IT'S W_DISCONNECT THEN:
            self.purge_creaders()# !!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.delete_creader(creader, True)# DELETE CREADER, BY PASSING CREADER TO CREADER_DELETE FUNCTION

        else:# ELSE, COMMAND IN THE MESSAGE FAILED MATCHING AGAINST THE MDP, MESSAGE WILL BE DUMPED AND STDOUT AS INVALID MESSAGE, BEACUSE IT DIDN'T MEET THE NECESSARY STRUCTURE.
            logging.error("E: invalid message:")
            dump(msg)            

    #   CREADER DELETE FUNCTION, delete CREADER session, remove corresponding CSERVICE from CSERVCIES
    def delete_creader(self, creader, disconnect):
        assert creader is not None# ASSERT THAT CREADER IS NOT NONE AND HAS BEEN PASSED TO THE DELETE FUNCTION CORRECTLY
        if disconnect:# IF DELETE CREADER: DISCONNECT VARIABLE HAS BEEN PASSED AS TRUE
            self.send_to_creader(creader, MDP.W_DISCONNECT, None, None, None)# SEND A MESSAGE TO THE CREADER TO HAVE HIM INITIATE A DISCONNECT FROM THE SBROKER
        if creader.service is not None:# IF CSERVICE HAS BEEN CONNECTED TO THE CREADER THEN:
            creader.service.waiting.remove(creader)# REMOVE THAT CSERVICE FROM THE CREADER CLASS
        self.cservices.pop(creader.service.name, None)# REMOVE THAT CSERVICE FROM THE CSERVICES LIST
        self.creaders.pop(creader.identity)# REMOVE THE CREADER.NAME FROM THE CREADERS LIST, SO WRITERS CAN NO LONGER SEND MESSAGES TO THIS READER
    #   CREADER REQUIRE FUNCTION, find CREADER to handle a message sent by CWRITER to a corresponding CSERVICE
    def require_creader(self, address):
        assert (address is not None)# ASSERT THAT ADDRESS VARIABLE HAS BEEN PASSED TO REQUIRE_CREADER FUNCTION
        print "000 PROCESS: CREADER ADDERSS: %s\n" % address
        identity = hexlify(address)# HEXLIFY THE ADDRESS AND ASSIGN IT TO VARIABLE - identity
        print "001 PROCESS: CREADER IDENTITY: %s\n" % identity
        creader = self.creaders.get(identity)# LOCATE A CREADER FROM THE REGISTERED CREADERS DICTIONARY BY IDENTITY OF THE CREADER
        print "002 PROCESS: CREADER FOUND: %s\n" % creader
        if (creader is None):# IF CREADER COULD NOT BE FOUND IN THE CREADERS DICTIONARY THEN:
            creader = cReader(identity, address, self.HEARTBEAT_EXPIRY)# CREATE CREADER, PASS(IDENTITY, ADDRESS,SET HEARTBEAT EXPIRY)
            self.creaders[identity] = creader# ADD CREADER TO LIST OF CREADERS
            if self.verbose:# OUTPUT LOGGING IF ENABLED
                logging.info("I: registering new creader: %s", identity)

        return creader# RETURN NEW CREADER OR FOUND CREADER TO WHOMEVER CALLED THIS FUNCTION
    #   CSERVICE REQUIRE FUNCTION, find CSERVICE in list of registered CSERVICES, or create a CSERVICE if cannot be found
    def require_cservice(self, name):
        assert (name is not None)# ASSERT THAT NAME VARIABLE HAS BEEN PASSED TO THE REQUIRE_SERVICE FUNCTION
        print "003 PROCESS: CSERVICE NAME: %s\n" % name
        cservice = self.cservices.get(name)# LOCATE THE CSERVICE.NAME
        print "004 PROCESS: CSERVICE FOUND: %s\n" % cservice
        if (cservice is None):# IF CSERVICE CANNOT BE FOUND THEN:
            cservice = cService(name)# ASSIGN NAME TO CSERVICE
            self.cservices[name] = cservice#

        return cservice# RETURN SERVICE TO WHOMEVER CALLED THE FUNCTION
    #   FIND CREADER BY SERVICE NAME!!!!!!!!
    def find_creader_by_cservice(self, servicename):
        for crd in self.creaders.values():
            if crd.service and crd.service == self.require_cservice(servicename):
                return crd
    #   CREADER & CWRITER BIND FUNCTION, binds to SBROKER socket
    def bind(self, endpoint):
        self.socket.bind(endpoint)# BIND SOCKET TO ENDPOINT VARIABLE
        logging.info("I: MDP.Sbroker/0.1.1 is active at %s", endpoint)# DISPLAY AFTER BINDING LOG
    #   CSERVICE INTERNAL SPEC FUNCTION, process CSERVER and MESSAGE 
    def service_internal(self, service, msg):
        returncode = "501"# ASSIGN A RETURNCODE IF MESSAGE VARIABLE IS INVALID
        if "mmi.service" == service:# CHECK IF SERVICE VARIABLE EQUALS TO mmi.service
            name = msg[-1]# GET THE NAME OF SERVICE FROM THE VERY LAST ITEM IN THE MSG LIST, ASSING IT TO name VARIABLE
            returncode = "200" if name in self.cservices else "404"# RETURN 200 IF name FOUND IN CSERVICESM ELSE RETURN 404
        msg[-1] = returncode# MODIFY MSG LSIT BY TAKING THE LAST ITEM AND CHANGING IT TO 501

        # insert the protocol header and service name after the routing envelope ([client, ''])
        msg = msg[:2] + [MDP.C_CLIENT, service] + msg[2:]# REWRAP THE ENVELOPE IT WILL BE : [ITEM.0,ITEM.1,MDP.C_CLIENT,SERVICE VARIABLE,ITEMS.2,ITEM.3 so on]
        self.socket.send_multipart(msg)# SEND THE MESSAGE AS MULTIPART TO SOCKET
    #   SBROKER TO CREADER SEND HEARTBEAT FUNCTION, send HEARTBEAT message to registered CREADERS
    def send_heartbeats(self):
        if (time.time() > self.heartbeat_at):# IF TIME.TIME() IS GREATER THEN HEARBEAT_AT VARIABLE THEN:
            for creader in self.waiting:# FOR EVERY CREADER MARKED AS WAITING DO:
                self.send_to_creader(creader, MDP.W_HEARTBEAT, None, None, None)# RUN A SEND HEARTBEAT FUNCTION TO CREADER

            self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL# SET HEARTBEAT_AT VARIABLE TO A VALUE
    #   CREADER PURGE FUNCTION, looks for HEARTBEAT expired CREADERS, used to cleanup inactive sessions left by disconnected CREADERS
    def purge_creaders(self):
        while self.waiting:# LOOP THROUGH WAITING CREADERS LIST AND:
            w = self.waiting[0]# ASSIGN WAITING[0] 1st ITEM IN LIST TO w
            if w.expiry < time.time():# IF CREADER.EXPIRY ATTRIBUTE VALUE IS LESS THEN TIME.TIME() THEN:
                logging.info("I: deleting expired creader: %s", w.identity)# SHOW LOG OUTPUT
                self.delete_creader(w,False)# DELETE CREADER, USING DELETE_CREADER FUNCTION
                self.waiting.pop(0)# REMOVE THE CREADER FROM WAITING LIST, LOOP BACK
            else:# ELSE: CREADER.EXPIRY ATTRIBUTE VALUE IS GREATER THEN TIME.TIME() THEN
                break# BREAK OUT OF LOOP
    #   CREADER WAITING FUNCTION, send CREADER to waiting list, so it becomes available to receiving messages and sending back confirmations
    def creader_waiting(self, creader):
        self.waiting.append(creader)# ADD CREADER TO WAITING LIST
        creader.service.waiting.append(creader)# ADD CREADER TO CLASS.CREADER.SERVICE.WAITING LIST
        creader.expiry = time.time() + 1e-3*self.HEARTBEAT_EXPIRY# SET CREADER.EXPIRY ATTRIBUTE TO HEARTBEAT_EXPIRY VALUE
        self.dispatch(creader.service, None)# RUN A DISPATCH FUNCTION ON THE CREADER.SERVICE ATTRIBUTE
    #   DISPATCH TO WAITING CREADERS FUNCTION, route/send messages from CWRITERS to CREADERS via CSERVICES
    def dispatch(self, cservice, msg):
        assert (cservice is not None)# ASSERT THAT CSERVICE VARIABLE HAS BEEN PASSED IN CORRECTLY
        if msg is not None:# Queue message if any
            cservice.requests.append(msg)# ADD MESSAGE TO REQUESTS LIST, QUEUEING UP THE INCOMING MESSAGES TO BE ROUTED/DISPATCHED
        self.purge_creaders()# CLEAN UP ANY DISCONNECTED CREADERS BY RUNNING PRUGE_CREADERS FUNCTION
        while cservice.waiting and cservice.requests:# LOOP THROUGH CSERVICE WAITING LIST AND REQUESTS LIST AND DO:
            msg = cservice.requests.pop(0)# ITEM.0 IDENTIFIES MSG VARIABLE DERIVED FROM REQUESTS LIST
            creader = cservice.waiting.pop(0)# ITEM.1 IDENTIFIES CREADER VARIABLE DERIVED FROM WAITING LIST
            self.waiting.remove(creader)# REMOVE CREADER FROM WAITING LIST
            self.send_to_creader(creader, MDP.W_REQUEST, None, msg, ['1'])# SEND A W_REQUEST COMMAND TO CREADER USING SEND_TO_CREADER FUNCTION
    #   SBROKER SEND MSG TO CREADER FUNCTION,given that message is provided, sends message to CREADER, with attributes to as how the CREADER should handle said message
    def send_to_creader(self, creader, command, option, msg=None, rtype=None):
        if rtype is None:#CHECK IF THERE IS A VALID VALUE PASSED TO THE rype VARIABLE, IF NOT THEN
            rtype = ['0']# ASSIGN 0 AS VALUE, MEANING NO REPLY NEEDED FROM THIS REQUEST, THIS IS USED FOR GETTING SESSIONS LIST !!!!
        if msg is None:# CHECK IF THERE IS A VALID MESSAGE BEING PASSED TO THE msg VARIABLE, IF NOT THEN:
            msg = []# TURN msg VARIABLE INTO A LIST
        elif not isinstance(msg, list):# ELSE IF, msg IS NOT AN INSTANCE OF CLASS LIST THEN:
            msg = [msg]# TURN MESSAGE msg VARIABLE INTO A LIST
        #print "send_to_creader function received message: %s for: \n%s\n" % (msg,creader)#!!!!!!!!!!!!!!!
        if option is not None:# CHECK IF OPTION VARIABLE HAS BEEN PASSED, IF NOT:
            msg = [option] + msg# REWRAP THE msg INTO: [OPTION, MESSAGE]
        msg = [creader.address, '', MDP.W_WORKER, command] + msg + rtype# REWRAP msg INTO: [CREADER.ADDRESS, '', CLASS, COMMAND, MESSAGE, REPLY(true/false)]

        if self.verbose:# IF VERBOSE IS TRUE THEN:
            logging.info("I: sending %r to creader", command)# LOG OUTPUT MESSAGE
            dump(msg)# DUMP MESSAGE
        print "A.SENT TO CREADER ADDRESS %s\nB.this message: %s\nC.reply was set:%s\n" % (creader, msg, rtype)
        self.socket.send_multipart(msg)# SEND MESSAGE
        #print "send_to_creader function sent out message: %s to: \n%s\n" % (msg,creader)#!!!!!!!!!!!!!!!
    #   SBROKER GENERATE A FIFO ID FOR WEBRTC CONNECTION BETWEEN CALLER AND CALEE, IT WILL BE USED TO CREATE OFFER/REPLY SCHEMA
    def generate_fifo(self):#, fifo):
        fifo = uuid.uuid4().hex
        if fifo not in self.fifolist:
            self.fifolist.append(fifo)
        else:
            print "random wasn't random enough"
            fifo = false
        return fifo
    #   MAINTENANCE FUNCTION -DELETE LATER
    def maintenance(self, mVar, mName):
        print "started maintenance function, opened file"
        if mVar and mName:
            mPath = "//EYEBALLX3/personal space/sergey/0000_NUKE/TESTING/LOGGING/"
            mfile = open((mPath + mName),'w')
            for key, value in mVar.iteritems():
                mout = ['KEY:',key, ' ATTRIBUTES:']
                mout.append('\n')
                if value.identity:
                    mout.append('CREADER_IDENTITY:')
                    mout.append(value.identity)
                    mout.append('\n')
                else: 
                    pass
                if value.address:
                    mout.append('CREADER_ADDRESS:')
                    mout.append(value.address)
                    mout.append('\n')
                else:
                    pass
                if value.service:
                    mout.append('CREADER_SERVICE:')
                    mout.append(value.service)
                    mout.append('\n')
                    mout.append(type(value.service))
                    mout.append('\n')
                    #for k,v in value.service.iteritems():
                    v = value.service
                    mout.append('START OF SERVICE ATTRIBUTES:')
                    mout.append('\n')
                    if v.name:
                        mout.append('CSERVICE_NAME:')
                        mout.append(v.name)
                        mout.append('\n')
                    else:
                        pass
                    if v.requests:
                        mout.append('CSERVICE_REQUESTS:')
                        mout.append(v.requests)
                        mout.append('\n')
                    else:
                        pass
                    if v.waiting:
                        mout.append('CSERVICE_WAITING:')
                        mout.append(v.waiting)
                        mout.append('\n')
                    else:
                        pass
                    mout.append('END OF SERVICE ATTRIBUTES')

                    mout.append('\n')
                    mout.append('\n')
                else:
                    pass
                if value.expiry:
                    mout.append('CREADER_EXPIRY:')
                    mout.append(value.expiry)
                    mout.append('\n')
                else:
                    pass
                if isinstance(mout, list):
                    mfile.write(str(mout)+'END OF KEY')
                else:
                    pass
            mfile.close()
            print "saved log for objects in %s\n" % mVar
        else:
            pass
        print "exited maintenance function, closed file"
    #END OF SBROKER FUNCTIONS

def main():# MAIN FUNCTION, ESTABLISHES CBORKER CONNECTION, BINDS THE SBROKER TO OPEN PORT
    verbose = '-v' in sys.argv# SET VERBOCITY
    cb = sBroker(verbose)# ASSIGN CLASS
    cb.bind("tcp://*:5555")# BIND SBROKER
    cb.mediate()# RUN MEDIATE FUNCTION

if __name__=='__main__':# ON OPEN START FUNCTION
    main()# START MAIN FUNCTION sBroker