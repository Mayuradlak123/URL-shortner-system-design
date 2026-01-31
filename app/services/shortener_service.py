import string
import random

BASE62_ALPHABET = string.digits + string.ascii_lowercase + string.ascii_uppercase

def encode_base62(num):
    if num == 0:
        return BASE62_ALPHABET[0]
    arr = []
    base = len(BASE62_ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(BASE62_ALPHABET[rem])
    arr.reverse()
    return ''.join(arr)

def decode_base62(s):
    base = len(BASE62_ALPHABET)
    num = 0
    for char in s:
        num = num * base + BASE62_ALPHABET.index(char)
    return num

def generate_short_code(length=7):
    """
    Generates a random short code of specified length using Base62 alphabet.
    """
    return ''.join(random.choices(BASE62_ALPHABET, k=length))
