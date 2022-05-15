from enum import Enum

class SenderState(Enum):
	WAIT_MSG_0 = 1
	WAIT_ACK_0 = 2
	WAIT_MSG_1 = 3
	WAIT_ACK_1 = 4

class ReceiverState(Enum):
	WAIT_MSG_0 = 1
	WAIT_MSG_1 = 2

