"""
Sum-Complement checksum implementation
"""

"""
Break packet into smaller chunks of pkt_size,
then sum these chunks and wrap the overflow bits (add them),
until the pkt is of pkt_size, then take 1's complement

pkt_size should be in bytes
"""
def generate_chksum(pkt: bytes, pkt_size: int=1):
	sum = 0
	pkt_int = int(pkt, 2)
	# 2 ** 8 (256) is 9 bits long, subtract 1 to get all 1s and reduce to pkt_size - 1 bits
	pkt_bits = 8 * pkt_size
	pkt_mask = (1 << pkt_bits) - 1

	# sum bits
	while pkt_int.bit_length():
		sum += pkt_int & pkt_mask
		pkt_int >>= pkt_bits
		# logical left shift
		# pkt_int = (pkt_int << pkt_bits) & ((1 << pkt_int.bit_length()) - 1)

	_sum = 0
	# wrap overflow bits and add them as well
	# assuming max overflow is pkt_size bits
	while sum.bit_length():
		_sum += sum & pkt_mask
		sum >>= pkt_bits

	"""
	Take 1s complement
	https://stackoverflow.com/questions/31151107/how-do-i-do-a-bitwise-not-operation-in-python
	"""
	complement = (1 << pkt_bits) - 1 - _sum

	# left-pad bits if leading 0s missing, to get to pkt_size
	return left_pad(complement, pkt_bits)

"""
Break packet into smaller chunks of pkt_size,
then sum these chunks and wrap the overflow bits (add them),
verify that the sum is all 1s or 0xFFFF...
"""
def verify_chksum(pkt: bytes, pkt_size: int=1):
	sum = 0
	pkt_int = int(pkt, 2)
	# 2 ** 8 (256) is 9 bits long, subtract 1 to get all 1s and reduce to pkt_size - 1 bits
	pkt_bits = 8 * pkt_size
	pkt_mask = (1 << pkt_bits) - 1

	# sum bits
	while pkt_int.bit_length():
		sum += pkt_int & pkt_mask
		pkt_int >>= pkt_bits
		# logical left shift
		# pkt_int = (pkt_int << pkt_bits) & ((1 << pkt_int.bit_length()) - 1)

	_sum = 0
	# wrap overflow bits and add them as well
	# assuming max overflow is pkt_size bits
	while sum.bit_length():
		_sum += sum & pkt_mask
		sum >>= pkt_bits

	# if all 1s, return True
	return (_sum & pkt_mask) == pkt_mask

if __name__ == "__main__":
	from utility import left_pad
	# b"1001 1001 1110 0010 0010 0100 1000 0100"
	print(generate_chksum(b"10011001111000100010010010000100", 1))
	# b"1001 1001 1110 0010 0010 0100 1000 0100" + b"1101 1010"
	print(verify_chksum(b"1001100111100010001001001000010011011010", 1))
else:
	from lib.utility import left_pad

