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


def match_length(m1, m2):
    if len(m1) == len(m2):
        return m1, m2
    
    l, s = (m1, m2) if len(m1) > len(m2) else (m2, m1)

    temp = [0 for _ in range(len(l) - len(s))]
    temp.extend(s)
    s = temp

    if m1 == l:
        return l, s
    return s, l

def equal_lengths(f):
    def dec_f(*args):
        m1, m2 = match_length(args[0], args[1])
        return f(m1, m2, *args[2:])
    
    return dec_f
