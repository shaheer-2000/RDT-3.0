from math import floor
from threading import Thread
from time import time

class Timeout:
	def __init__(self):
		self.current_timeout = None
		self.interrupt = False
		self.expired = False
		self.interrupted = False

	def _timer(self, seconds: int):
		start_time = time()
		# busy-waiting
		while floor(time() - start_time) < seconds:
			if self.interrupt:
				self.interrupt = False
				self.interrupted = True
				break
			continue

		self.current_timeout = None
		if not self.interrupted:
			self.expired = True

	def start_timeout(self, seconds: int):
		if self.current_timeout is not None:
			self.stop_timeout()
			# raise AttributeError("a timeout is already running, stop the current timeout first")
		
		self.interrupted = False
		self.expired = False

		self.current_timeout = Thread(target=self._timer, args=(seconds,))
		self.current_timeout.start()


	def stop_timeout(self):
		if self.current_timeout is None:
			self.interrupt = False
			self.current_timeout = None
			self.interrupted = False
			self.expired = False
			return
		
		self.interrupt = True
		self.current_timeout.join()
		self.current_timeout = None
		self.interrupted = True
		self.expired = False

	def is_running(self):
		return self.current_timeout is not None

	def has_expired(self):
		return self.expired

	def was_interrupted(self):
		return self.interrupted


if __name__ == "__main__":
	from time import sleep
	t = Timeout()
	t.start_timeout(10)
	print("timeout started")
	sleep(5)
	t.stop_timeout()
	print("timeout halted")
	try:
		t.start_timeout(10)
		print("timeout started")
		t.start_timeout(10)
		print("timeout started")
	except AttributeError:
		pass

