from lib.utility import *
from models.states import SenderState
from lib.checksum import *
from lib.packet import *
from lib.timeout import Timeout

import socket
import signal
from threading import Thread
from random import random

class Server:
	"""
	packet_size in bytes
	"""
	def __init__(self, host: str = "127.0.0.1", port: int = 8000, packet_size: int = 1, timeout_duration: int = 30):
		# socket attributes
		# over TCP rather than UDP, because this is only a simulation
		socket.setdefaulttimeout(1.0)
		self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.host = host
		self.port = port
		
		# limit to 1 connection for now
		self.conn = None
		self.shutdown = False
		self.req_thread = None
		self.rcv_thread = None

		# RDT 3.0 state attributes
		self.state = None
		self.pkt_size = packet_size
		self.timeout = Timeout()
		self.timeout_duration = timeout_duration
		self.last_sent_pkt = None

		# 
		self.last_msg = ""

		# handle signals (CTRL + C)
		signal.signal(signal.SIGINT, self.sigint_handler)

	def sigint_handler(self, signum, frame):
		self._shutdown()
	
	def start(self):
		self.state = SenderState.WAIT_MSG_0
		self.sock.bind((self.host, self.port))
		# TODO: accept socket configurations as a constructor param
		self.sock.settimeout(1.0)
		self.sock.listen(1)

		self.req_thread = Thread(target=self.req_handler)
		self.req_thread.start()

	def _shutdown(self):
		self.shutdown = True
		self.req_thread.join()
		self.rcv_thread.join()

		# self.sock.shutdown(socket.SHUT_RDWR)
		self.conn.close()
		self.sock.close()

	def req_handler(self):
		# only allow 1 connection at a time
		while True:
			if self.shutdown:
				break

			if self.conn is None:
				try:
					conn, _ = self.sock.accept()
					self.conn = conn
					self.rcv_thread = Thread(target=self.rcv_handler)
					self.rcv_thread.start()
				except TimeoutError:
					pass

	def rcv_handler(self):
		while True:
			# handle shutdown here
			if self.shutdown:
				break

			try:
				data = self.conn.recv(1024)
				if data:
					self.rdt_rcv(data)
			except TimeoutError:
				if self.timeout.has_expired():
					print("<Sender timed out>")
					print("<Resending packet>")
					self.udt_send(self.last_sent_pkt, resend=True)
				pass


	# while loop over socket.recv, if data, then pass to rdt_recv
	# while loop over socket.recv, if timeout, then do what needs to be done
	def rdt_rcv(self, rcvpkt: bytes):
		if self.state == SenderState.WAIT_MSG_0 or self.state == SenderState.WAIT_MSG_1:
			return
		elif self.state == SenderState.WAIT_ACK_0 or self.state == SenderState.WAIT_ACK_1:
			# stop the previous timer
			self.timeout.stop_timeout()
			# get the headers and data
			ack, chksum, data = extract_pkt(rcvpkt, is_sender=False)
			chksum = left_pad(chksum, self.pkt_size * 8)
			# the expected ack #, 0 if waiting for ack 0, else 1
			expected_ack = 0 if self.state == SenderState.WAIT_ACK_0 else 1

			# is packet corrupted or is packet ack different than expected_ack
			# data + chksum => append checksum to the data for verification
			if not verify_chksum(data + chksum, self.pkt_size) or ack != expected_ack:
				print("<Receiver checksum failed or has incorrect ACK>")
				self.timeout.start_timeout(self.timeout_duration)
				return # resend on timeout
			else:
				# do something with message here
				print("<Received ACK>")
				self.state = SenderState.WAIT_MSG_1 if self.state == SenderState.WAIT_ACK_0 else SenderState.WAIT_MSG_0

	def rdt_send(self, data: bytes, resend=False):
		if resend or self.state == SenderState.WAIT_MSG_0 or self.state == SenderState.WAIT_MSG_1:
			if len(data) % 8 != 0:
				data_int = int(data, 2)
				# pad data to a whole byte
				# (8 - len(data)) => number of bits to complete the byte
				# (len(data) - data_int.bit_length()) => number of leading 0s lost as a result of conversion
				data = left_pad(data_int, (8 - len(data)) + (len(data) - data_int.bit_length()))

			# compute checksum
			chksum = generate_chksum(data, self.pkt_size)
			# save correct data before corruption
			self.last_msg = data
			# corrupt packet if mishap prob > 80%
			mishap_prob = random()
			if mishap_prob > 0.8:
				print("<Packet corrupted>")
				print("<Waiting on timeout>")
				corrupted_data = corrupt_pkt(data)
				show_pkt_diff(data, corrupted_data)
				data = corrupted_data
			# make packet
			seq_num = 0 if self.state == SenderState.WAIT_MSG_0 else 1
			sndpkt = make_sndpkt(seq_num, chksum, data)
			# change state to WAIT_ACK_0 if current state is WAIT_MSG_0, else WAIT_ACK_1
			if not resend:
				self.state = SenderState.WAIT_ACK_0 if self.state == SenderState.WAIT_MSG_0 else SenderState.WAIT_ACK_1
			# send over udt
			self.udt_send(sndpkt, corrupted_pkt=(mishap_prob > 0.8))


	# does socket.sendall
	def udt_send(self, pkt: bytes, resend=False, corrupted_pkt=False):
		if resend:
			print("<Resending packet>")
			self.rdt_send(self.last_msg, resend=True)
			return
		# save the packet for resending
		self.last_sent_pkt = pkt
		# start timer
		self.timeout.start_timeout(self.timeout_duration)
		# actually send the packet here
		# TODO: simulate loss and corruption here
		try:
			mishap_prob = random()
			if mishap_prob > 0.9 and corrupted_pkt == False:
				print("<Packet lost>")
				print("<Waiting on timeout>")
			else:
				self.conn.sendall(pkt)
		except TimeoutError:
			pass


if __name__ == "__main__":
	server = Server(timeout_duration=5)
	server.start()

	while True:
		msg = input("[SERVER]: ")
		if msg == "!quit":
			server._shutdown()
			break
		if msg == "!state":
			if server.state == SenderState.WAIT_MSG_0:
				print("<Waiting on call from above - 0>")
			elif server.state == SenderState.WAIT_MSG_1:
				print("<Waiting on call from above - 1>")
			elif server.state == SenderState.WAIT_ACK_0:
				print("<Waiting on ACK - 0>")
			elif server.state == SenderState.WAIT_ACK_1:
				print("<Waiting on ACK - 0>")
			continue

		bytes_msg = msg.encode()
		char_bytes = list(map(lambda c: (bin(c)[2:]).encode(), bytes_msg))
		encoded_msg = b""
		for c in char_bytes:
			encoded_msg += c

		server.rdt_send(encoded_msg)


