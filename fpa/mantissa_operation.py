from collections import deque
from .utils import equal_lengths


@equal_lengths
def compare(m1, m2):
    for x, y in range(zip(m1, m2)):
        if x > y:
            return 1
        if x < y:
            return -1
    
    return 0


@equal_lengths
def mantissa_sum(m1, m2, base):
    m = deque()

    carry = 0
    for x, y in reversed(zip(m1, m2)):
        s = x + y + carry
        s, carry = s%base, s//base

        m.appendleft(s)
    
    if carry > 0:
        m.appendleft(carry)
    
    return list(m)


@equal_lengths
def mantissa_sub(m1, m2, base):
    m = deque()

    carry = 0
    for x, y in reversed(zip(m1, m2)):
        s = x - y - carry
        s, carry = s%base, abs(s//base)

        m.appendleft(s)
    
    while(m[0] == 0):
        m.popleft()
    
    return list(m)


@equal_lengths
def number_mul(m, number, base):
    m = deque()

    carry = 0
    for x in reversed(m):
        s = x * number + carry
        s, carry = s%base, s//base

        m.appendleft(s)
    
    if carry > 0:
        m.appendleft(carry)
    
    return list(m)


@equal_lengths
def mantissa_mul(m1, m2, base):
    m = []

    for k, x in enumerate(m2, start=1):
        temp = number_mul(m1, x, base)
        temp.extend(0 for _ in range(len(m2) - k))

        m = mantissa_sum(m, temp, base)
    
    return m


@equal_lengths
def mantissa_div(m1, m2, base):
    divd = m1
    divs = m2
    res = deque()
    
    started_count = False
    i = 0
    while i < len(divs):
        if len(divd) < len(divs):
            res.append(0)
        else:
            # buscar mayor escalar q multiplicado x divs sea menor o igual q el dividendo
            j = 0
            m = None
            comp = None
            while True:
                temp = number_mul(divs, j+1, base)
                comp = compare(temp, divd)
                if comp == 1:
                    break
                else:
                    m = temp
                    j += 1
                    if comp == 0:
                        break
            
            res.append(j)

            if comp == 0:
                break

            if j > 0:
                divd = mantissa_sub(divd, m, base)
            
                if not started_count:
                    started_count = True
        
        divd.append(0)
        
        if started_count:
            i += 1
    
    # contando cantidad de 0s y quitandolos
    i = 0
    while res[0] == 0:
        res.popleft()
        i += 1
    
    return list(res), i
