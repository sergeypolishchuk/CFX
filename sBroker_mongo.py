# broker_sessions.py
# broker thread, for sessions
# class for user machine object
import threading, time, logging, zmq#, sys, socket  
from thread_test import NP# ENABLE ONCE SUBFOLDER IS RESOLVED
from binascii import hexlify
from zhelpers import dump

class uNode(object):
	# attributes
	uMname = None
	uNname = None
	identity = None
	expiry = None
	address = None
	mtype = None
	mcap = None

	def __init__(self, name, user, address, identity, mtype, mcap, lifetime):
		self.uMname = name# user machine name
		self.uNname = user# user name, who is logged in on this machine
		self.identity = None# machine identity, hex identity of the machine
		self.expiry = time.time() + 1e-3*lifetime# machine expiry value, heartbeats will keep machine alive by resetting this value
		self.address = address # machine address, messages intended for user will be routed to this address
		self.mtype = mtype# machine type , e.g. WIN OSX LINUX ADROID OS7
		self.mcap = mcap# machine capability, list of tags for type of messages this machine can recieve

# class for user name object
class userName(object):
	# attributes
	name = None
	busy = None
	ready = None

	def __init__(self, name):
		self.name = name # username of the connected user
		self.busy = [] # list of machines that are busy processing messages for the user
		self.ready = [] # list of machines that are ready to process messages for the user

class sBrokerSessions(threading.Thread):
	HEARTBEAT_LIVENESS = 3
	HEARTBEAT_INTERVAL = 2500
	HEARTBEAT_EXPIRY = HEARTBEAT_INTERVAL * HEARTBEAT_LIVENESS
	ctx = None
	socket = None
	poller = None
	heartbeat_at = None
	uNodes = None
	uNames = None
	ready = None

	def __init__(self, verbose=True):
		threading.Thread.__init__(self)
		self.verbose = verbose
		self.uNodes = {}
		self.uNames = {}
		self.ready = []
		self.heartbeat_at = time.time() + 1e-3*self.HEARTBEAT_INTERVAL
		self.ctx = zmq.Context()
		self.socket = self.ctx.socket(zmq.ROUTER)
		self.socket.linger = 0
		self.poller = zmq.Poller()
		self.poller.register(self.socket, zmq.POLLIN)
		logging.basicConfig(format="%(asctime)s %(message)s", datefmt="%Y-%m-%d %H:%M:%S",
				level=logging.INFO)

		def uSession_mngr(self):
			while True: # starting session loop
				try:
					items = self.poller.poll(self.HEARTBEAT_INTERVAL)
				except KeyboardInterrupt:
					print "Interrupted with keypress"
					break# Interrupotion
				if items:# check if something came in on the polling socket
					msg = self.socket.recv_multipart()# assign that something to msg variable
					if self.verbose:
						logging.info("I: received message from connected Node")
						dump(msg)

					sender = msg.pop(0)# get the node that sent the message
					empty = msg.pop(0)#  empty delimiter frame of the message
					assert empty == ''# check if message is formatted correctly
					header = msg.pop(0) # get the node class that sent the message
					if (NP.N_NODE == header):# check the node against node protocol
						self.uNodeProcessing(sender, msg)# add node that sent the message to sessions
					else:
						logging.error("E: invalid message to sessions thread")
					self.delete_dead_uNodes()
					self.send_heartbeats_to_uNodes()

		def uNodeProcessing(self, sender, msg):
			assert len(msg) >= 1# check that message has at least one item in it, like command
			command = msg.pop(0)
			#unode_ready = hexlify(sender) in self.uNodes
			if (NP.N_POWERUP == command):
				user = msg.pop(0)
				print("I: unode powered up under user: %s") % user
				mtype = msg.pop(0)
				print("I: unode powered up with mtype: %s") % mtype
				mcap = msg.pop(0)
				print("I: unode powered up with mcap: %s") % mcap
				unode = self.uNodeToSession(user, sender, mtype, mcap)
				print("I: unode: %s added to uNodes") % unode
				self.send_Session_List()

			else:
				logging.error("E: invalid message sent to sBrokerSessions THREAD")

		def uNodeToSession(self, user, address, mtype, mcap):
			assert (address is not None)
			if self.verbose:
				logging.info("I: processing node's address")
			identity = hexlify(address)
			unode = self.uNodes.get(identity)
			if (unode is None):
				unode = uNode(self.name, user, address, identity, mtype, mcap, self.HEARTBEAT_EXPIRY)
				self.uNodes[identity] = unode
				if self.verbose:
					logging.info("I: added a new node to uNodes")

			return unode


		def delete_dead_uNodes(self):
			pass
		def send_heartbeats_to_uNodes(self):
			pass
		def send_Session_List(self):
			pass
		def bind_zmq_socket(self):
			pass

# def sBrokerMainThread():
# 	cB = #
# 	cB.bind("tcp://*:5555")
# 	cB.route()

# def sTitanMainThread():
# 	cT = #
# 	cT.bind("tcp://*:5554")
# 	cT.process()

# if __name__=='__main__':
# 	sBrokerMainThread()
# 	sTitanMainThread()