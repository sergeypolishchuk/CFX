#cReaderAPI.py
#IMPORT PACKAGES
import logging
import time
#IMPORT PYZMQ EXTANSION LIBRARY
import zmq
#IMPORT MESSAGE HELPER FUNCTIONS
from zhelpers import dump
#IMPORT LOCAL MAJORDOMO PROTOCOL DEFINISHIONS
import MDP

#DEFINE CLASS: CREADER.OBJECT (MAJOR DOMO WORKER)
#	THIS CLASS DEFINES REGISTERED ONE CREADER AND
#	HEARTBEAT_LIVENESS, CONTEXT, SBROKER, CSERVICE
#	SOCKET, HEARTBEAT VARS, CONNECTION VARS, REPLY
class cReaderObj(object):
	"""docstring for cReaderObj"""
	HEARTBEAT_LIVENESS = 3# INT VARIABLE FOR HEARTBEAT FREQUENCY
	sbroker = None# STRING VARIABLE FOR SBROKER ADDRESS
	ctx = None# STRING VARIABLE FOR ZMQ CONTEXT
	cservice = None# STRING VARIABLE FOR CSERVICE ASSIGNED TO CREADEROBJ
	# ------------------------------------------------------------
	creader = None# INT VARIBALE FOR SOCKET NUMBER THAT WILL BE USED TO CONNECT TO SBROKER
	heartbeat_at = 0# INT VARIABLE FOR WHEN TO SEND HEARTBEAT (RELATIVE TO TIME.TIME(), IN SECONDS)
	liveness = 0# INT VARIABLE FOR HOW MANY ATTEMPTS LEFT TO TRY RECONNECTION TO SBROKER
	heartbeat = 2500# INT VARIABLE FOR HEARTBEAT DELAY, MSECONDS
	reconnect = 2500# INT VARIABLE FOR RECONNECT DELAT, MSECONDS
	# INTERNAL STATE VARIABLES
	expect_reply = False# BOOLEAN VARIBALE FOR REPLYING TO INCOMING MESSAGE(CURRENTLY FALSE AT START)
	timeout = 2500# INT VARIABLE FOR POLLER TIMEOUT, MSECONDS
	verbose = False# BOOLEAN VARIABLE FOR PRINTING CREADEROBJ API ACTIVITY TO STDOUT
	# RETURN ADDRESS IF ANY
	reply_to = False# STRING VARIABLE FOR SENDER(CWRITER) ADDRESS, IF PROVIDED IN MESSAGE
	sList = None
	cSessions = None
	# ------------------------------------------------------------

	def __init__(self, sbroker, cservice, verbose=True):#verbose=False
		self.sbroker = sbroker
		self.cservice = cservice
		self.verbose = verbose
		self.ctx = zmq.Context()
		self.poller = zmq.Poller()
		self.sList = []# SESSION LIST
		self.recvState = True
		self.powerDWN = False
		self.cSessions = False
		logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
				level=logging.INFO)
		self.reconnect_to_sbroker()

	# ------------------------------------------------------------

	#CONNECT OR RECONNECT TO SBROKER FUNCTION
	def reconnect_to_sbroker(self):# FUNCTION IS CALLED WHENEVER CREADEROBJ NEEDS TO RE-ESTABLISH CONNECTION TO SBROKER
		if self.creader:# check if creader then:
			self.poller.unregister(self.creader)# then run the zmq internal unregister command on the poller
			self.creader.close()# close the connection on the socket
		self.creader = self.ctx.socket(zmq.DEALER)# assing a DEALER object to the socket
		self.creader.linger = 0# assign a 0 linger value to socket, this internal zmq command eliminates the connection
		self.creader.connect(self.sbroker)# establish connection to SBROKER with this zmq command
		self.poller.register(self.creader, zmq.POLLIN)# start polling the socket by assigning POLLER to said socket
		if self.verbose:
			logging.info("I: connecting to SBROKER at %s...", self.sbroker)
		self.send_to_sbroker(MDP.W_READY, self.cservice, [])# send an empty message to SBROCKER, to register CREADER
		self.liveness = self.HEARTBEAT_LIVENESS# If liveness hits zero, queue is considered disconnected
		self.heartbeat_at = time.time() + 1e-3 * self.heartbeat# set the heartbeat varibale

	#SEND TO SBROKER, FUNCTION		
	def send_to_sbroker(self, command, option=None, msg=None):# FUNCTION IS CALLED FOR SENDING MESSAGES TO SBROKER
		if msg is None:# CHECK IF MESSAGE IS PROVIED TO THE FUNCTION
			msg = []# IF NOT THEN SET MESSAGE TO EMPTY LIST
		elif not isinstance(msg, list):# CHECK THAT MESSAGE THAT HAS BEEN PROVIED IS TYPE LIST
			msg = [msg]# IF NOT THEN MAKE PROVIED MESSAGE INTO A LIST

		if option:# IF OPTION IS PROVIED THEN REWRAP THE MESSAGE BY PLACING OPTION FIRST:
			msg = [option] + msg# NOW THE MESSAGE LOOKS LIKE THIS: [[OPTION],[MESSAGE]]

		msg = ['', MDP.W_WORKER, command] + msg# REWRAP THE MESSAGE AGAIN WITH EMPTY DELIMITER, CREADER ID AND COMMAND:
		if self.verbose:# ['', MDP.W_WORKER, COMMAND, [OPTION], [MESSAGE]]
			logging.info("I: sending %s to broker\n", command)
			dump(msg)
		self.creader.send_multipart(msg)# SEND THE MESSAGE TO THE SOCKET, FOR THE SBROKER TO PROCESS

	#RECEIVE MESSAGES FROM SBROKER AND PROCESS THEM WITH CREADER FUNCTION
	def recv(self, reply=None):#, status=True):
		while self.recvState:# start a loop for receive function, this will listen to socket via POLLIN 
			try:# Poll socket for a reply, with timeout
				items = self.poller.poll(self.timeout)# timeout assigned to POLLER on socket
			except KeyboardInterrupt:# stop listening and looping if keyboard CTRL+C is pressed
				break # Interrupted

			if items and self.recvState:# CHECK IF MESSAGE CAME IN ON THE POLLER SOCKET, then:
				msg = self.creader.recv_multipart()# assing incoming message to msg variable for processing
				# if self.verbose:
				# 	logging.info("I: received message from broker: \n")
				# 	dump(msg)
				self.liveness = self.HEARTBEAT_LIVENESS# Once message comes in, invoke HEARTBEAT FREQUENCY = 3
				assert len(msg) >= 3# Don't try to handle errors, just assert noisily
				empty = msg.pop(0)# strip the empty delimiter in the incoming message to empty variable
				assert empty == ''# assert that emtpy delimeter is infact empty
				header = msg.pop(0)# strip the header from the massage and assign in to the header variable
				assert header == MDP.W_WORKER# assert that header is valid
				command = msg.pop(0)# strip the command from the message and assign it to the command variable
				if command == MDP.W_REQUEST:# check if command is a REQUEST, is so then:
					print "request message arrived at CREADER here it is: %s\n" % msg
					# We should pop and save as many addresses as there are
					# up to a null part, but for now, just save one...
					self.reply_to = msg.pop(0)# strip out the reply_to address from the message and assign it to variable
					print "received MDP.REQUEST type message, going to reply with confirmation to: %s\n" % self.reply_to#!!!!!!!
					rtype = msg.pop(len(msg)-1)# strip out the last item in the message: reply/no_reply 0/1 and assign it to the rtype variable !!!!!!!!!
					assert rtype != ''# assert that rtype variable was passed with request !!!!!!!!!!!
					if rtype != [0]:
						print "reply has been requested for this request: rtype arg %s\n" % rtype# !!!!!!!!!!!!!
						cWrep = [self.reply_to, '']+[msg[len(msg)-1]]# !!!!!!!!!!!!!!
						print cWrep
						self.send_to_sbroker(MDP.W_REPLY,msg=cWrep)# added 
					else:
						print "message received by CREADER has rtype set to: %s\n" % rtype# !!!!!!!!!!!!!!!
						print "no request needed for this message\n"# !!!!!!!!!!!!!!!
					assert msg.pop(0) == ''# assert that the next part of the incoming message is an empty delimeter
					self.cSessions = False
					return msg # return actual message portion from the message, We now have a request to process
				elif command == MDP.W_HEARTBEAT:# check if command is a HEARTBEAT, is so then:
					# Do nothing for heartbeats
					pass
				elif command == MDP.W_SESSIONS:# check if command is a SESSIONS REQUEST, is so then:
					self.cSessions = True
					msg.pop(len(msg)-1)
					self.sList = msg#['sList']+msg# PRINT OUT ACTIVE SESSIONS LIST, print msg
					return self.cSessions
				elif command == MDP.W_DISCONNECT:# check if command is a DISCONNECT, is so then:
					# if self.powerDWN:
					# 	print "powering down, disconnecting 000"
					# 	self.disconnect_from_sbroker()
					# 	break
					# else:
						self.reconnect_to_sbroker()# run the reconnect to sbroker command
				else :# finally if message was not formed correctly by the CWRITER and SBROKER, let the user know
					logging.error("E: invalid input message: ")
					dump(msg)

			else:# if items did not come in then
				self.liveness -= 1# set liveness: decrease it by one
				if self.liveness == 0:# if liveness is 0 then:
					if self.verbose:# the user know that CREADER has dies and needs to re-connect to the SBROKER
						logging.warn("W: disconnected from broker - retrying...")
					try:# give it some time for the connection to die out
						time.sleep(1e-3*self.reconnect)# sleep for a bit
					except KeyboardInterrupt:# unless the script is interrupted by a CTRL+C command by suer
						break
					self.reconnect_to_sbroker()# try to reconnec to the SBROKER

			# Send HEARTBEAT if it's time
			if time.time() > self.heartbeat_at:
				self.send_to_sbroker(MDP.W_HEARTBEAT)
				self.heartbeat_at = time.time() + 1e-3*self.heartbeat

		logging.warn("W: interrupt received, killing worker...")
		self.cSessions = False
		return None

	#DESTROY CNTEXT FUNCTION IS CALLED WHEN CONTEXT CONNECTION TO SBROKER OR SOCKET NEEDS TO BE COMPLETELY DESTROYED
	def destroy(self):
		# context.destroy depends on pyzmq >= 2.1.10
		self.ctx.destroy(0)
