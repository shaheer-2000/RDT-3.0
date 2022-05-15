from math import ceil
from random import random

"""
left-pad bytes with 0s
"""
def left_pad(pkt: int, width: int) -> bytes:
	return ("".zfill(width - pkt.bit_length()) + bin(pkt)[2:]).encode()

"""
Takes a packet as bytes and returns a packet with 0s
and 1s flipped randomly

only flips a single bit, leading 0s ignored
"""
def corrupt_pkt(pkt: bytes) -> bytes:
	pkt_int = int(pkt, 2)
	flip_index = ceil(random() * pkt_int.bit_length())
	flip_mask = pkt_int >> flip_index

	return left_pad(pkt_int ^ flip_mask, len(pkt))

if __name__ == "__main__":
	print(corrupt_pkt(b"00100000"))

"""
Displays the difference between original and corrupted packet
"""
def show_pkt_diff(pkt: bytes, corrupted_pkt: bytes):
	# print("Original PKT:", pkt)
	# print("Corruptd PKT:", corrupted_pkt)
	# print("              ", end="")
	_window_start = 0
	window_width = 32
	_window_end = _window_start + window_width

	while _window_start < len(pkt):
		print(pkt[_window_start:_window_end])
		print(corrupted_pkt[_window_start:_window_end])
		print("  ", end="")
		for b, c in zip(pkt[_window_start:_window_end], corrupted_pkt[_window_start:_window_end]):
			if b != c:
				print("^", end="")
			else:
				print(" ", end="")
		print("")
		_window_start += window_width
		_window_end += window_width

