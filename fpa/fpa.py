import math

from .utils import build_mantissa
from .mantissa_operation import compare, mantissa_sum, mantissa_sub, mantissa_mul, mantissa_div


class FPANumber:
    def __init__(self, base, exponent, mantissa, sign):
        self._base = base
        self._exponent = exponent
        self._mantissa = mantissa
        self._sign = sign

    @classmethod
    def create(cls, n, base, mantissa_length):
        if n == 0:
            return cls(base, 0, [0 for _ in range(mantissa_length)], 1)
        
        s = 1 if n > 0 else -1
        e, m = build_mantissa(abs(n), base, mantissa_length)

        return cls(base, e, m, s)

    def is_nan(self):
        return self._sign == 0

    def is_negative(self):
        return self._sign == -1

    def is_positive(self):
        return self._sign == 1

    def is_zero(self):
        return (not self.is_nan()) and all(x == 0 for x in self._mantissa)

    def is_integer(self):
        if self.is_nan():
            return False
        
        if len(self._mantissa) > self._exponent:
            return all(x == 0 for x in self._mantissa[self._exponent+1:])
    
        return True


    def abs(self):
        if not self.is_nan():
            return FPANumber(self._base, self._exponent, self._mantissa, 1)
        return self


    def export(self):
        if self.is_nan():
            return None
        
        res = 0
        b = math.pow(self._base, self._exponent - len(self._mantissa) + 1)
        for k in reversed(self._mantissa):
            res += k*b
            b *= b
        
        return self._sign * res


def _nan_safe(f):
    def dec_f(*args):
        for x in args:
            if isinstance(x, FPANumber) and x.is_nan():
                raise Exception(f'Operation failed: trying to do a {f.__name__} with NaN.')
        
        return f(*args)
    
    return dec_f

def _same_fpa(f):
    def dec_f(*args):
        fpa = args[0]
        for x in args[1:]:
            if not isinstance(x, FPANumber):
                continue
            if (x._base != fpa._base or
                not (fpa._m <= x._exponent <= fpa._M) or
                len(x._mantissa) != fpa._mantissa_length):
                raise Exception(f'Operation failed: trying to do a {f.__name__} with a number '
                                'which doesn\'t belong to this FPA.')
        
        return f(*args)
    
    return dec_f

def _overflow(f):
    def dec_f(*args):
        res = f(*args)
        fpa = args[0]

        if (not res.is_nan()) and res._exponent > fpa._M:
            return fpa._plus_inf if res._sign == 1 else fpa._minus_inf
        return res
    
    return dec_f

def _underflow(f):
    def dec_f(*args):
        res = f(*args)
        fpa = args[0]

        if (not res.is_nan()) and res._exponent < fpa._m:
            return fpa._plus_zero if res._sign == 1 else fpa._minus_zero
        return res
    
    return dec_f


class FPA:
    def __init__(self, base, mantissa_length, m, M):
        self._base = base
        self._mantissa_length = mantissa_length
        self._m = m
        self._M = M

        self._plus_zero = FPANumber.create(0, base, mantissa_length)
        self._minus_zero = FPANumber.create(0, base, mantissa_length)
        self._minus_zero._sign = -1

        infinity_mantissa = [1 for _ in range(mantissa_length)]
        self._minus_inf = FPANumber(base, M, infinity_mantissa, -1)
        self._plus_inf = FPANumber(base, M, infinity_mantissa, 1)

        epsilon_mantissa = [1]
        epsilon_mantissa.extend(0 for _ in range(mantissa_length - 1))
        self._minus_epsilon = FPANumber(base, m, epsilon_mantissa, -1)
        self._plus_epsilon = FPANumber(base, m, epsilon_mantissa, 1)

        self._nan = FPANumber.create(0, base, mantissa_length)
        self._nan._sign = 0

        self._pi = FPANumber.create(math.pi, base, mantissa_length)


    def new(self, n):
        return FPANumber.create(n, self._base, self._mantissa_length)


    def _equal(self, x: FPANumber, y: FPANumber):
        return x._exponent == y._exponent and \
            x._sign == y._sign and \
            all(a == b for a, b in zip(x._mantissa, y._mantissa))

    @_nan_safe
    @_same_fpa
    def equal(self, x: FPANumber, y: FPANumber):
        return self._equal(x, y)


    def _less_than(self, x: FPANumber, y: FPANumber):
        if x._sign != y._sign or x._exponent > y._exponent:
            return x.is_negative()
        if x._exponent < y._exponent:
            return x.is_positive()
        return x._sign * compare(x._mantissa, y._mantissa) == -1

    @_nan_safe
    @_same_fpa
    def less_than(self, x: FPANumber, y: FPANumber):
        return self._less_than(x, y)


    def _great_than(self, x: FPANumber, y: FPANumber):
        return not (self._less_than(x, y) or self._equal(x, y))

    @_nan_safe
    @_same_fpa
    def great_than(self, x: FPANumber, y: FPANumber):
        self._great_than(x, y)


    def _less_or_equal(self, x: FPANumber, y: FPANumber):
        return not self._great_than(x, y)

    @_nan_safe
    @_same_fpa
    def less_or_equal(self, x: FPANumber, y: FPANumber):
        return self._less_or_equal(x, y)


    def _great_or_equal(self, x: FPANumber, y: FPANumber):
        return not self._less_than(x, y)

    @_nan_safe
    @_same_fpa
    def great_or_equal(self, x: FPANumber, y: FPANumber):
        return not self._great_or_equal(x, y)


    def _is_pair(self, x: FPANumber):
        if x.is_integer():
            two = self.new(2)
            x = self._div(x, two)
            return x.is_integer()
        
        return False

    @_nan_safe
    @_same_fpa
    def is_pair(self, x: FPANumber):
        return self._is_pair(x)


    def _is_inf(self, x: FPANumber):
        return self._equal(x.abs(), self._plus_inf)

    @_nan_safe
    @_same_fpa
    def is_inf(self, x: FPANumber):
        return self._is_inf(x)


    def _sum(self, x: FPANumber, y: FPANumber):
        x_s, y_s = x._sign, y._sign
        x, y = x.abs(), y.abs()
        x, x_s, y, y_s = x, x_s, y, y_s if self.great_or_equal(x, y) else y, y_s, x, x_s

        mx, my = x._mantissa, y._mantissa
        mx.extend(0 for _ in range(x._exponent - y._exponent))

        if x_s == y_s:
            # sumar
            m = mantissa_sum(mx, my, self._base)
            e = x._exponent + (len(m) - len(mx))
            return FPANumber(self._base, e, m[:self._mantissa_length], x_s)
        
        #restar
        m = mantissa_sub(mx, my, self._base)
        m.extend(0 for _ in range(self._mantissa_length - len(m)))
        e = x._exponent - (len(mx) - len(m))
        return FPANumber(self._base, e, m, x_s)

    @_nan_safe
    @_same_fpa
    @_overflow
    @_underflow
    def sum(self, x: FPANumber, y: FPANumber):
        return self._sum(x, y)


    def _sub(self, x: FPANumber, y: FPANumber):
        y = FPANumber(y._base, y._exponent, y._mantissa, -1*y._sign)
        return self._sum(x, y)

    def sub(self, x: FPANumber, y: FPANumber):
        y = FPANumber(y._base, y._exponent, y._mantissa, -1*y._sign)
        return self.sum(x, y)


    def _mul(self, x: FPANumber, y: FPANumber):
        if (x.is_zero() and self._is_inf(y)) or (self._is_inf(x) and y.is_zero()):
            return self._nan

        e = x._exponent + y._exponent
        res_expected_length = 2 * self._mantissa_length - 1

        m = mantissa_mul(x._mantissa, y._mantissa, self._base)
        e += len(m) - res_expected_length
        return FPANumber(self._base, e, m[:self._mantissa_length], x._sign * y._sign)

    @_nan_safe
    @_same_fpa
    @_overflow
    @_underflow
    def mul(self, x: FPANumber, y: FPANumber):
        return self._mul(x, y)


    def _div(self, x: FPANumber, y: FPANumber):
        if y.is_zero():
            if x.is_zero():
                return self._nan
            if y._sign == x._sign:
                return self._plus_inf
            return self._minus_inf
        
        if x.is_zero() and self._is_inf(y):
            if x._sign == y._sign:
                return self._plus_zero
            return self._minus_zero
        
        e = x._exponent - y._exponent
        m, zc = mantissa_div(x._mantissa, y._mantissa, self._base)

        if len(m) < self._mantissa_length:
            m.extend(0 for _ in range(self._mantissa_length - len(m)))
        e -= zc
        return FPANumber(self._base, e, m, x._sign * y._sign)

    @_nan_safe
    @_same_fpa
    @_overflow
    @_underflow
    def div(self, x: FPANumber, y: FPANumber):
        return self._div(x, y)


    def _raw_exp(self, x: FPANumber, iterations):
        one = self.new(1)

        k = iterations
        n = self.new(k)
        res = self.new(1)
        while k > 0:
            temp = self._sum(one, self._div(self._mul(x, res), n))
            if self._equal(temp, res):
                break

            res = temp
            n = self._sub(n, one)
            k -= 1
        
        return res

    def _exp(self, x: FPANumber, iterations=100):
        if x.is_negative():
            one = self.new(1)
            return self._div(one, self._raw_exp(x.abs(), iterations))
        
        return self._raw_exp(x, iterations)

    @_nan_safe
    @_same_fpa
    @_overflow
    @_underflow
    def exp(self, x: FPANumber, iterations=100):
        return self._exp(x, iterations)


    def _raw_log(self, x: FPANumber, iterations):
        one = self.new(1)
        x = self._div(x, self._sub(x, one))

        k = 1
        n = self.new(k)
        denm = self.new(1)
        res = self.new(0)
        while k <= iterations:
            denm = self._mul(denm, x)
            temp = self._sum(res, self._div(one, self._mul(n, denm)))
            if self._equal(temp, res):
                break

            res = temp
            n = self._sum(n, one)
            k += 1
        
        return res

    def _log(self, x: FPANumber, iterations=1000):
        if x.is_negative() or x.is_zero():
            return self._nan
        
        # x = ab and b = base^ex
        # ln(x) = ln(ab) = ln(a) + ln(b) = ln(a) + exln(base)
        b_mantissa = [1]
        b_mantissa.extend(0 for _ in range(self._mantissa_length - 1))
        b = FPANumber(self._base, x._exponent, b_mantissa, x._sign)
        a = self._div(x, b)

        lnb = self.new(x._exponent * math.log(self._base))
        lna = self._raw_log(a, iterations)

        return self._sum(lna, lnb)


    @_nan_safe
    @_same_fpa
    @_underflow
    def log(self, x: FPANumber, iterations=1000):
        return self._log(x, iterations)

    @_nan_safe
    @_same_fpa
    def log_any(self, x: FPANumber, y: FPANumber):
        if x.is_positive() and not x.is_zero() and not self._equal(x, self.new(1)):
            return self._div(self._log(y), self._log(x))
        # exception


    def _pow(self, x: FPANumber, y: FPANumber):
        if y.is_integer():
            iterations = int(y.export())
            res = self.new(1)
            for _ in range(iterations):
                res = self._mul(res, x)
            
            return res
        
        return self._exp(self._mul(y, self._log(x)), 100)

    @_nan_safe
    @_same_fpa
    @_overflow
    @_underflow
    def pow(self, x: FPANumber, y: FPANumber):
        one = self.new(1)

        if self._equal(x, one):
            return x
        
        if x.is_zero():
            if y.is_negative() and not y.is_zero():
                return x
            # excepcion
        
        if y.is_negative():
            return self._div(one, self._pow(x, y.abs()))
        
        if x.is_negative() and not y.is_integer():
            # exception
            pass
        
        return self._pow(x, y)


    def _sin(self, x: FPANumber, iterations):
        twopi = self._mul(self.new(2), self._pi)
        while self._less_or_equal(x, self._minus_zero):
            x = self._sum(x, twopi)
        while self._great_or_equal(x, twopi):
            x = self._sub(x, twopi)
        
        res = self.new(0)
        num = x
        one = self.new(1)
        den_c = self.new(1)
        den = self.new(1)
        to_sum = True
        for _ in range(iterations):
            if to_sum:
                temp = self._sum(res, self._div(num, den))
            else:
                temp = self._sub(res, self._div(num, den))
            
            if self._equal(temp, res):
                break

            res = temp

            num = self._mul(num, x)
            num = self._mul(num, x)

            den_c = self._sum(den_c, one)
            den = self._mul(den, den_c)
            den_c = self._sum(den_c, one)
            den = self._mul(den, den_c)

            to_sum = not to_sum
        
        return res

    @_nan_safe
    @_same_fpa
    @_underflow
    def sin(self, x: FPANumber, iterations=100):
        return self._sin(x, iterations)


    def _cos(self, x: FPANumber, iterations):
        twopi = self._mul(self.new(2), self._pi)
        while self._less_or_equal(x, self._minus_zero):
            x = self._sum(x, twopi)
        while self._great_or_equal(x, twopi):
            x = self._sub(x, twopi)
        
        res = self.new(0)
        num = self.new(1)
        one = self.new(1)
        den_c = self.new(0)
        den = self.new(1)
        to_sum = True
        for _ in range(iterations):
            if to_sum:
                temp = self._sum(res, self._div(num, den))
            else:
                temp = self._sub(res, self._div(num, den))
            
            if self._equal(temp, res):
                break

            res = temp

            num = self._mul(num, x)
            num = self._mul(num, x)

            den_c = self._sum(den_c, one)
            den = self._mul(den, den_c)
            den_c = self._sum(den_c, one)
            den = self._mul(den, den_c)

            to_sum = not to_sum
        
        return res

    @_nan_safe
    @_same_fpa
    @_underflow
    def cos(self, x: FPANumber, iterations=100):
        return self._cos(x, iterations)
