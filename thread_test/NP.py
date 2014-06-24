N_NODE = "NP01"

N_POWERUP		=	"\001"
N_HEARTBEAT		=	"\002"
N_POWERDOWN		=	"\003"

states = [None, "POWERUP", "HEARTBEAT", "POWERDOWN"]

W_READY         =   "\001"
W_REQUEST       =   "\002"
W_REPLY         =   "\003"
W_HEARTBEAT     =   "\004"
W_DISCONNECT    =   "\005"
W_SESSIONS      =   "\006" #!!!!!
W_POWERDOWN     =   "\007" #!!!!!
W_WEBRTC        =   "\008" #!!!!!

commands = [None, "READY", "REQUEST", "REPLY", "HEARTBEAT", "DISCONNECT", "SESSIONS", "POWERDOWN", "VIDEOCALL"]

N_TYPE_WIN		=	"1"
N_TYPE_OSX		=	"2"
N_TYPE_LINUX	=	"3"
N_TYPE_ANDROID	=	"4"
N_TYPE_OS7		=	"5"