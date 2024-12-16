def bin_2_signed_int(binary_str:str) -> int:
    # Get the number of bits
    num_bits = len(binary_str)

    # Convert the binary string to an integer
    unsigned_int = int(binary_str, 2)

    # Check the most significant bit (sign bit)
    if binary_str[0] == '1':  # If the sign bit is 1
        # Compute the signed integer using two's complement
        signed_int = unsigned_int - (1 << num_bits)
    else:
        # If the sign bit is 0, the number is positive
        signed_int = unsigned_int

    return signed_int

def signed_int_2_bin(num: int, width: int) -> str:
    """
    Converts a signed integer into a binary string with the given width.

    Args:
        num (int): The signed integer to convert.
        width (int): The width of the resulting binary string.

    Returns:
        str: A binary string with the given width.
    """
    mask = (1 << width) - 1
    num &= mask

    # Convert to binary and ensure it fits the given width
    binary_str = format(num, f"0{width}b")

    return binary_str
