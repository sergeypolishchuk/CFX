#cWriterAPI.py
#IMPORT PACKAGES
import logging
#IMPORT PYZMQ EXTANSION LIBRARY
import zmq
#IMPORT MESSAGE HELPER FUNCTIONS
from zhelpers import dump
#IMPORT LOCAL MAJORDOMO PROTOCOL DEFINISHIONS
import MDP

#DEFINE CLASS: CWRITER.OBJECT (MAJOR DOMO CLIENT)
#	THIS CLASS DEFINES REGISTERED ONE CWRITER AND
#	TIMEOUT, CONTEXT, SBROKER, POLLER

class cWriterObj(object):
	"""docstring for cWriterObj"""
	sbroker = None# STRING VARIABLE FOR SBROKER ADDRESS
	ctx = None# OBJECT VARIABLE FOR ZMQ CONTEXT
	cwriter = None# INT VARIABLE FOR SOCKET NUMBER THAT WILL BE USED TO CONNECT TO SBROKER
	poller = None# OBJECT VARIABLE FOR ZMQ POLLER
	timeout = 2500# INT VARIABLE FOR POLLER TIMEOUT, MSECONDS
	verbose = False# BOOLEAN VARIABLE FOR PRINTING CWRITEROBJ API ACTIVITY TO STDOUT
	def __init__(self, sbroker, verbose=True):
		self.sbroker = sbroker
		self.verbose = verbose
		self.ctx = zmq.Context()
		self.poller = zmq.Poller()
		logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO)
		self.reconnect_to_sbroker()
		self.powerDWN = False

	# FUNCTION IS CALLED WHENEVER CWRITEROBJ NEEDS TO RE-ESTABLISH CONNECTION TO SBROKER
	def reconnect_to_sbroker(self):
		if self.cwriter:# check if cwriter then:
			self.poller.unregister(self.cwriter)# then run zmq internal unregister command on the poller
			self.cwriter.close()# close the connection on the socket
		self.cwriter = self.ctx.socket(zmq.DEALER)# assign a DEALER object to the socket
		self.cwriter.linger = 0# assign a 0 linger value to socket, this internal zmq command eliminates the connection
		self.cwriter.connect(self.sbroker)# establish a connection to SBROKER with zmq command
		self.poller.register(self.cwriter, zmq.POLLIN)# start polling the socket by assigning POLLER to said socket
		if self.verbose:
			logging.info("I: connecting to broker at %s...\n", self.sbroker)

	# FUNCTION IS CALLED FOR SENDING MESSAGES TO CBROKER
	def cWsend(self, cservice, cWrequest):
		if not isinstance(cWrequest, list):# CHECK IF CWREQUEST IS TYPE: LIST
			cWrequest = [cWrequest]# IF NOT TURN IT INTO A LIST 
		cWrequest = ['',MDP.C_CLIENT, cservice] + cWrequest
		if self.verbose:
			logging.warn("I: send request to '%s' service\n", cservice)
			dump(cWrequest)
		self.cwriter.send_multipart(cWrequest)# SEND MESSAGE TO THE SOCKET, FOR THE SBROKER TO PROCESS

	# FUNCTION IS CALLED WHEN INITIATING WebRTC CALLS
	def cWcall(self, command, peers):
		if not isinstance(peers, list):
			peers = [peers]
		peers = ['',MDP.C_WORKER, command] + peers
		self.cwriter.send_multipart(peers)

	# FUNCTION IS CALLED WHEN MESSAGES COME BACK FROM CSERVER
	def cWrecv(self):
		try:# poll socket for reply, with timeout
			items = self.poller.poll(self.timeout)# timeout assigned to POLLER on socket
		except KeyboardInterrupt:# stop listening and looping if keyboard CTRL+C is pressed
			return

		if items:# CHECK IF REPLY CAME IN ON THE POLLER SOCKET, then:
			msg = self.cwriter.recv_multipart()# assign incoming reply to msg variable for processing
			#print "shout: cWriterAPI got message from sBroker: %s" % msg# !!!!!!!!!!
			if self.verbose:
				logging.info("I: received reply")
				dump(msg)
			assert len(msg) >= 4# assert that REPLY message list is longer then 4 items
			empty = msg.pop(0)# strip empty delimeter from reply
			header = msg.pop(0)# strip header from reply
			assert MDP.C_CLIENT == header# check if header of rely is valid and was intended for CWRITER
			cservice = msg.pop(0)# strip cservice from reply
			return msg# return sent reply, this should be the last item of the reply
		else:# if reply is invalid and doesn't pass the asserts or wasn't long enough, print information to the user
			logging.warn("W: permanent error, abandoning request")
			
