import sys
import math


def nearest_below_exponent(n, base: int):
    assert isinstance(base, int) and base > 1, \
        "'base' must be an integer greater than 1"
    assert n > 0, "'n' must be a positive number"
    
    return math.floor(math.log(n, base))


def build_mantissa(n, base: int, length: int):
    assert isinstance(length, int) and length > 0, \
        "'length' must be a positive integer"
    
    e = nearest_below_exponent(n, base)
    mantissa = []

    k = e
    while len(mantissa) < length and abs(n) >= sys.float_info.epsilon:
        p = math.pow(base, k)

        q = int(n // p)
        mantissa.append(q)

        n %= p
        k -= 1
    
    if len(mantissa) < length:
        mantissa.extend(0 for _ in range(length - len(mantissa)))
    
    return e, tuple(mantissa)
