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

