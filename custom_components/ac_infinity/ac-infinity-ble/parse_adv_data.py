import sys

def generate_table(byte_array_str):
    # Convert the byte array string to an actual byte array
    byte_array = eval(byte_array_str.strip())
    
    # Ensure it's a bytearray
    if not isinstance(byte_array, bytearray):
        print("Input is not a valid bytearray string.")
        return
    
    # Generate the table header
    print(f"{'Index':<7} | {'Hex':<4} | {'Dec':<4} | {'Char':<4}")
    print("-" * 30)
    
    # Generate the table content
    for index, byte in enumerate(byte_array):
        hex_value = f"{byte:02x}"
        dec_value = byte
        char_value = chr(byte) if 32 <= byte <= 126 else '.'
        print(f"{index:<7} | {hex_value:<4} | {dec_value:<4} | {char_value:<4}")

if __name__ == "__main__":
    print("Please paste the bytearray string and press Enter:")
    byte_array_str = input()
    print("...")
    generate_table(byte_array_str)
