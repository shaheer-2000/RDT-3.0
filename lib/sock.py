import socket
import threading
import signal

class Socket:
	def __init__(self, config=None):
		self.shutdown = False
		self.global_shutdown = False

		# try:
		# 	socket.setdefaulttimeout(config["timeout"])
		# except KeyError:
		# 	socket.setdefaulttimeout(0.0)

		self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.config = config

		# limit to a single connection
		self.accept_conns = True

		self.connected_conn = None

		# self.recv_queue = []
		self.send_queue = []

		# handle interrupts (CTRL+C)
		signal.signal(signal.SIGINT, self.sigint_handler)

	def sigint_handler(self, signum, frame):
		print("!!!!")
		self.shutdown = True
	
		try:
			if self.recv_handler_thread:
				self.recv_handler_thread.join()
		except AttributeError:
			pass

		try:
			if self.send_handler_thread:
				self.send_handler_thread.join()
		except AttributeError:
			pass

		if self.connected_conn:
			self.connected_conn.close()
		
		try:	
			if self.req_handler_thread:
				self.req_handler_thread.join()
				# close the server/client
				self._socket.close()
		except AttributeError:
			pass

		self.global_shutdown = True

	def start(self, recv_cb):
		if self.config is None:
			raise ValueError("config must be a dict")

		# try:
		# 	self._socket.setblocking(self.config["blocking"])
		# except KeyError:
		# 	self._socket.setblocking(False)
		
		try:
			self._socket.settimeout(self.config["timeout"])
		except KeyError:
			self._socket.settimeout(1)

		# if server, then serve, else just communicate
		try:
			self.is_server = self.config["is_server"]
		except KeyError:
			self.is_server = True

		try:
			if self.is_server:
				self._socket.bind((self.config["host"], self.config["port"]))
				self._socket.listen(self.config["backlog"])
			else:
				self._socket.connect((self.config["host"], self.config["port"]))
		except TimeoutError:
			pass
		except KeyError as e:
			print(f"Error in `Socket.config`: {e}")
		except OSError as e:
			print(f"Error starting the socket: {e}")
			return

		self.req_handler_thread = threading.Thread(target=self.req_handler, args=(recv_cb,))

		self.req_handler_thread.start()
		# self.req_handler_thread.join()

	def req_handler(self, recv_cb):
		if self.is_server:
			# Add while loop to allow more connections to be accepted
			# if self.shutdown or (self.is_server and self.accept_conns):
			# 	break
			# socket is listening
			while True:
				# set socket to blocking and wait here
				# https://stackoverflow.com/questions/59743649/blockingioerror-winerror-10035-a-non-blocking-socket-operation-could-not-be-com
				try:
					if self.shutdown or not self.accept_conns:
						break

					conn, addr = self._socket.accept()
				
					# pass connection socket to some handler
					if conn and self.accept_conns:
						self.accept_conns = False

						self.connected_conn = conn
						self.recv_handler_thread = threading.Thread(target=self.recv_handler, args=(conn, addr, recv_cb))
						self.send_handler_thread = threading.Thread(target=self.send_handler, args=(conn, addr))
						break
				except TimeoutError:
					pass
		else:
			self.recv_handler_thread = threading.Thread(target=self.recv_handler, args=(self._socket, "", recv_cb))
			self.send_handler_thread = threading.Thread(target=self.send_handler, args=(self._socket, ""))

		try:
			self.recv_handler_thread.start()
			self.send_handler_thread.start()
		except AttributeError:
			pass

		# Main thread is busy with .join() so it doesn't listen for the SIGINT
		# https://stackoverflow.com/questions/29660830/python-sigint-not-caught
		# self.recv_handler_thread.join()
		# self.send_handler_thread.join()

		# close the connection
		# if self.is_server:
		# 	conn.close()

	def recv_handler(self, conn, addr, recv_cb):
		while True:
			if self.shutdown:
				break

			try:
				data = conn.recv(1024)
			except TimeoutError:
				continue
			except ConnectionResetError:
				continue

			if data:
				msg = data.decode()

				# handle_msg_here
				recv_cb(msg)

				self.put_recv_msg(msg)

	def send_handler(self, conn, addr):
		while True:
			if self.shutdown:
				break
				
			if self.send_queue:
				msg = self.get_send_msg()
				data = msg.encode()
	
				if len(data):
					# # handle_data_here
					# data = send_cb(data)

					conn.sendall(data)

	def put_send_msg(self, msg):
		self.send_queue.append(msg)

	def get_send_msg(self):
		self.send_queue.pop(0)

	def put_recv_msg(self, msg):
		self.recv_queue.append(msg)

	def get_recv_msg(self):
		self.recv_queue.pop(0)


if __name__ == "__main__":
	s = Socket(config={
		"host": "127.0.0.1",
		"port": 8000,
		"timeout": 1.0,
		"is_server": True,
		"backlog": 1
	})
	
	c = Socket(config={
		"host": "127.0.0.1",
		"port": 8000,
		"timeout": 1.0,
		"is_server": False
	})

	s.start(recv_cb=lambda x: print("Server", x))
	c.start(recv_cb=lambda x: print("Client", x))

	# keep the main thread alive
	while not s.shutdown or not c.shutdown:
		pass


