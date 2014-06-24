import time, threading, zmq
from zhelpers import dump

			#dump(msg)
			#msg = None

			#socket.send("yeppers!")

# def one_thread(var, context):

class JOJO(object):
	blondie = None
	def __init__(self, verbose=True):
		self.blondie = {}
		self.one_thread_address = "inproc://one_thread"
		self.main_listen_address = "tcp://*:5555"

		self.ctx = zmq.Context()

		self.main_listen_socket = self.ctx.socket(zmq.ROUTER)
		self.main_listen_socket.linger = 0
		self.main_poller = zmq.Poller()
		self.main_poller.register(self.main_listen_socket, zmq.POLLIN)
		self.main_listen_socket.bind(self.main_listen_address)
		# bound main socket to listen for messages on port 5555 from oustide

		# one_thread_socket = ctx.socket(zmq.DEALER)
		self.one_thread_socket = self.ctx.socket(zmq.PAIR)
		self.one_thread_socket.bind(self.one_thread_address)

	def one_thread(self, context):
		socket = context.socket(zmq.PAIR)
		socket.connect("inproc://one_thread")
		while True:
			# msg = socket.recv_multipart()
			msg = socket.recv()
			if msg:
				print "I: one_thread got this:%s\n" % msg
				# manage incoming stuff
				time.sleep(1)
				# send result back to main_thread
				print "I: done work"
				self.blondie[msg] = 'star'
				print "I: one_thread: blondie says: %s\n" % self.blondie

	def main_thread(self):
		#JOJO(True)
		# one_thread_thread = threading.Thread(target=one_thread, args=(one_thread_address, ctx))
		self.one_thread_thread = threading.Thread(target=self.one_thread, args=(self.ctx, ))
		print "I: starting one_thread\n"
		print "I: main_thread: blondie says: %s\n" % self.blondie
		print self.one_thread_thread
		self.one_thread_thread.start()

		while True:
			try:
				item = self.main_poller.poll(2500)
			except KeyboardInterrupt:
				self.main_listen_socket.close()
				self.one_thread_socket.close()
				self.ctx.term()
				print "I: KILLED EVERYTHING"
				break
			if item:
				msg = self.main_listen_socket.recv_multipart()
				sender = msg.pop(0)
				empty = msg.pop(0)

				print "I: main thread got this: %s\n" % msg
				#dump(msg)

				time.sleep(1)
				print "I: sending MSG to one_thread"
				self.one_thread_socket.send(msg[0])
				self.blondie['star'] = msg[0]
				print "I: main_thread: blondie says: %s\n" % self.blondie

def main():
	verbose = True
	jj = JOJO(verbose)
	jj.main_thread()

if __name__ == "__main__":
	print "starting main_thread"
	main()
