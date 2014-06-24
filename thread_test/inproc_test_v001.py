import time, threading, zmq
from zhelpers import dump

def one_thread(context):
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
			JOJO.blondie['star'] = msg
			print "I: one_thread: blondie says: %s\n" % JOJO.blondie
			#dump(msg)
			#msg = None

			#socket.send("yeppers!")

# def one_thread(var, context):

class JOJO(object):
	blondie = {}
	def __init__(self, verbose=True):
		self.blondie = {"star":"bright"}



	def main_thread(self):
		#JOJO(True)
		
		one_thread_address = "inproc://one_thread"
		main_listen_address = "tcp://*:5555"

		ctx = zmq.Context()

		main_listen_socket = ctx.socket(zmq.ROUTER)
		main_listen_socket.linger = 0
		main_poller = zmq.Poller()
		main_poller.register(main_listen_socket, zmq.POLLIN)
		main_listen_socket.bind(main_listen_address)
		# bound main socket to listen for messages on port 5555 from oustide

		# one_thread_socket = ctx.socket(zmq.DEALER)
		one_thread_socket = ctx.socket(zmq.PAIR)
		one_thread_socket.bind(one_thread_address)

		# one_thread_thread = threading.Thread(target=one_thread, args=(one_thread_address, ctx))
		one_thread_thread = threading.Thread(target=one_thread, args=(ctx, ))
		print "I: starting one_thread\n"
		print "I: main_thread: blondie says: %s\n" % self.blondie
		print one_thread_thread
		one_thread_thread.start()

		while True:
			try:
				item = main_poller.poll(2500)
			except KeyboardInterrupt:
				main_listen_socket.close()
				one_thread_socket.close()
				ctx.term()
				print "I: KILLED EVERYTHING"
				break
			if item:
				msg = main_listen_socket.recv_multipart()
				sender = msg.pop(0)
				empty = msg.pop(0)

				print "I: main thread got this: %s\n" % msg
				#dump(msg)

				time.sleep(1)
				print "I: sending MSG to one_thread"
				one_thread_socket.send(msg[0])
				print "I: main_thread: blondie says: %s\n" % self.blondie

def main():
	verbose = True
	jj = JOJO(verbose)
	jj.main_thread()

if __name__ == "__main__":
	print "starting main_thread"
	main()
