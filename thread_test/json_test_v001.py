
from collections import namedtuple
import json, os, sys, tempfile, socket, uuid, time

cfgFILENAME = "CFGCFX.json"
cfgDIRNAME = "CFX"
cfgDIR = os.path.join(os.path.dirname(tempfile.gettempdir()),cfgDIRNAME)
cfgFILE = os.path.join(cfgDIR,cfgFILENAME)

class uNode(object):
	username = None
	usemachine = None
	uid = None
	userlist = None
	serverpath = None
	"""docstring for uNode"""
	def __init__(self):
		super(uNode, self).__init__()
		self.username = "sergey"
		self.usemachine = socket.gethostname().upper()
		self.uid = uuid.uuid4().hex
		self.userlist = {"sergey":"3d","Johan":"comp","Mia":"design","maren":"design","claire":"3d"}
		self.serverpath = ["//DEADEYE/DeadlineRepository6", "//RENDEREYE/DeadlineRepository6", "//SECRETSERVE/DeadlineRepository6"]


def _json_object_hook(d): return namedtuple('X', d.keys())(*d.values())
def json2obj(data): return json.loads(data, object_hook=_json_object_hook)
# def object_decoder(obj):
# 	if '__type__' in obj and obj['__type__'] == 'uNode':
# 		return uNode(obj['username'], obj['usemachine'], obj['uid'], obj['userlist'], obj['userlist'], obj['serverpath'])

if __name__=='__main__':
	print uNode()
	with open(cfgFILE, 'w') as outfile:
		json.dump(uNode().__dict__, outfile)

	time.sleep(3)

	
	x = json2obj(open(cfgFILE).read())
	print x

	# lomo = json.loads(open(cfgFILE).read(), object_hook = object_decoder)
	# print lomo





	# lester = json.loads(open(cfgFILE).read())
	# for key, value in lester.iteritems():
	# 	if isinstance(value, dict):
	# 		print lester[key]
	# 		for key, value in lester[key].iteritems():
	# 			print value
	# 	else:
	# 		print key, value

	# lester = json.JSONDecoder().decode(open(cfgFILE).read())
	# type(lester)
	# print lester['username']

		# print (key+':'+value)

	# nuNode = open(cfgFILE).read()
	# nuNodeDC = json.JSONDecoder()
	# # vals = json.loads(nuNode)
	# print type(nuNode)
	# print type(nuNodeDC)
	# print type(nuNodeDC.decode(nuNode))
	# print nuNodeDC.decode(nuNode)
	# 	# print key
	# print vals
	# nuNode = json.JSONDecoder()
	# for part in nuNode.decode(cfgFILE):
	# 	print part
	# with open(cfgFILE, 'w') as outfile:
	# 	nuNode = json.loads(cfgFILE)
	# 	print nuNode
