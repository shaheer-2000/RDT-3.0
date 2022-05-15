from models.states import ReceiverState
from lib.checksum import *
from lib.packet import *
from lib.timeout import Timeout

import socket
import signal
from threading import Thread

class Client:
	"""
	packet_size in bytes
	"""
	def __init__(self, host: str = "127.0.0.1", port: int = 8000, packet_size: int = 1):
		# socket attributes
		# over TCP rather than UDP, because this is only a simulation
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.host = host
		self.port = port

		self.shutdown = False
		self.rcv_thread = None

		# RDT 3.0 state attributes
		self.state = None
		self.pkt_size = packet_size

		# handle signals (CTRL + C)
		signal.signal(signal.SIGINT, self.sigint_handler)

	def sigint_handler(self, signum, frame):
		self._shutdown()
	
	def start(self):
		self.state = ReceiverState.WAIT_MSG_0
		# TODO: accept socket configurations as a constructor param
		self.sock.settimeout(2.0)
		self.sock.connect((self.host, self.port))

		self.rcv_thread = Thread(target=self.rcv_handler)
		self.rcv_thread.start()

	def _shutdown(self):
		self.shutdown = True
		self.rcv_thread.join()

		self.sock.shutdown(socket.SHUT_RDWR)
		self.sock.close()

	def rcv_handler(self):
		while True:
			# handle shutdown here
			if self.shutdown:
				break

			try:
				data = self.sock.recv(1024)
				if data:
					self.rdt_rcv(data)
			except TimeoutError:
				pass


	# while loop over socket.recv, if data, then pass to rdt_recv
	# while loop over socket.recv, if timeout, then do what needs to be done
	def rdt_rcv(self, rcvpkt: bytes):
		if self.state == ReceiverState.WAIT_MSG_0 or self.state == ReceiverState.WAIT_MSG_1:
			# get the headers and data
			seq_num, chksum, data = extract_pkt(rcvpkt)
			# decode data back to utf-8 here from binary
			chksum = left_pad(chksum, self.pkt_size * 8)
			# the expected seq #, 0 if waiting for seq_num 0, else 1
			expected_seq_num = 0 if self.state == ReceiverState.WAIT_MSG_0 else 1
			# is packet corrupted or is seq_num different than expected
			# data + chksum => append checksum to the data for verification
			pkt_not_corrupted = verify_chksum(data + chksum, self.pkt_size)
			# dummy data
			_data = "hello sender"
			bytes_msg = _data.encode()
			char_bytes = list(map(lambda c: (bin(c)[2:]).encode(), bytes_msg))
			_data = b""
			for c in char_bytes:
				_data += c
			if len(_data) % 8 != 0:
				_data_int = int(_data, 2)
				# pad data to a whole byte
				# (8 - len(data)) => number of bits to complete the byte
				# (len(data) - data_int.bit_length()) => number of leading 0s lost as a result of conversion
				_data = left_pad(_data_int, (8 - len(_data)) + (len(_data) - _data_int.bit_length()))

			
			print(seq_num, chksum, _data)
			# compute checksum
			chksum = generate_chksum(_data, self.pkt_size)
			
			# make packet
			# ack = seq_num if incorrect seq_num, or pkt_not_corrupted and correct seq_num
			ack = seq_num
			change_state = True
			# if pkt is corrupted and has correct seq_num, then ack = invert of seq_num (0 if 1, else 1 if 0)
			if not pkt_not_corrupted and seq_num == expected_seq_num:
				print("<Packet corrupted>")
				ack = int(not seq_num)
				change_state = False
			elif seq_num != expected_seq_num:
				print("<Packet has incorrect sequence #>")
				change_state = False
			sndpkt = make_rcvpkt(ack, chksum, _data)
			# update state
			if change_state:
				self.state = ReceiverState.WAIT_MSG_1 if ReceiverState.WAIT_MSG_0 else ReceiverState.WAIT_MSG_0
			# send over udt
			self.udt_send(sndpkt)
			if pkt_not_corrupted and seq_num == expected_seq_num:
				# do something with message here
				print("[SENDER]: ", data.decode())

	# does socket.sendall
	def udt_send(self, pkt: bytes):
		# actually send the packet here
		try:
			self.sock.sendall(pkt)
		except TimeoutError:
			pass


if __name__ == "__main__":
	client = Client()
	client.start()

	while True:
		msg = input()
		if msg == "!quit":
			client._shutdown()
			break

