from lib.sock import Socket

class ClientSocket(Socket):
	def __init__(self):
		super().__init__(config={
			"host": "127.0.0.1", "port": 8000, "blocking": False, "timeout": 1.0, "is_server": False
			})
		
		# handle interrupts (CTRL+C)
		# signal.signal(signal.SIGINT, self.sigint_handler)

	def start(self):
		print("C")
		super().start(self.recv)
		print("D")
	
	def recv(self, msg):
		print(msg)

	def send(self, msg):
		self.put_send_msg(msg)
		print(f"Parent = {super().send_queue}\nChild = {self.send_queue}")

if __name__ == "__main__":
	c = ClientSocket()
	c.start()

	while not c.global_shutdown:
		pass
