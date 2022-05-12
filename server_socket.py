from lib.sock import Socket

class ServerSocket(Socket):
	def __init__(self):
		super().__init__(config={
			"host": "127.0.0.1", "port": 8000, "backlog": 0, "blocking": False, "is_server": True, "timeout": 1.0
			})

	def start(self):
		print("A")
		super().start(self.recv)
		print("B")
	
	def recv(self, msg):
		print(msg)

	def send(self, msg):
		self.put_send_msg(msg)
		print(f"Parent = {super().send_queue}\nChild = {self.send_queue}")


if __name__ == "__main__":
	s = ServerSocket()
	s.start()

	while not s.global_shutdown:
		pass

