"""
Packet creation & extraction related utility methods
"""

import struct

"""
https://docs.python.org/3/library/struct.html#struct-format-strings

@ = system native size alignment
Char	|	C Type			|	Python Type		|	Size	|	Expected Value(s)
H		|	unsigned short	|	integer			|	2		|	(0, 1)
s		|	char[]			|	bytes			|	*		|	data in bytes
I		|	unsigned int	|	integer			|	4		|	checksum value
"""
SIZE_ALIGNMENT_CHAR = "@"
SEQ_NUM_CHAR = "H"
# DATA_LEN_CHAR = "I"
DATA_CHAR = "s"
CHKSUM_CHAR	= "I"
ACK_CHAR = "H"
SNDPKT_FMT = f"{SIZE_ALIGNMENT_CHAR}{SEQ_NUM_CHAR}{CHKSUM_CHAR}{DATA_CHAR}"
RCVPKT_FMT = f"{SIZE_ALIGNMENT_CHAR}{ACK_CHAR}{CHKSUM_CHAR}{DATA_CHAR}"

def make_sndpkt(seq_num: int, chksum: int, data: bytes):
	# append msg
	sndpkt_fmt = SNDPKT_FMT[:-1] + f"{len(data)}" + SNDPKT_FMT[-1:]

	return struct.pack(sndpkt_fmt, seq_num, chksum, data)

def make_rcvpkt(ack: int, chksum: int, data: bytes):
	# append msg
	rcvpkt_fmt = RCVPKT_FMT[:-1] + f"{len(data)}" + RCVPKT_FMT[-1:]

	return struct.pack(rcvpkt_fmt, ack, chksum, data)

def extract_pkt(pkt: bytes, is_sender: bool=True):
	pkt_header_fmt = SNDPKT_FMT[:-1] if is_sender else RCVPKT_FMT[:-1]
	pkt_header, pkt = struct.unpack(pkt_header_fmt, pkt[:8]), pkt[8:]
	data = b""
	while len(pkt):
		(s,), pkt = struct.unpack(DATA_CHAR, pkt[:1]), pkt[1:]
		data += s

	return pkt_header + (data,)

if __name__ == "__main__":
	seq_num = 0
	ack = 0
	data = b"My name is shaheer"
	chksum = 123

	sndpkt = make_sndpkt(seq_num, chksum, data)
	rcvpkt = make_rcvpkt(ack, chksum, data)

	# print(sndpkt, rcvpkt)

	_sndpkt = extract_pkt(sndpkt)
	_rcvpkt = extract_pkt(rcvpkt, is_sender=False)

	print(_sndpkt, _rcvpkt)

	assert (seq_num, chksum, data) == _sndpkt
	assert (ack, chksum, data) == _rcvpkt

