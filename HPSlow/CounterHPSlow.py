import py4hw
from TCounterHP import TCounterHP
from SlowCounter import SlowCounter
 
class CounterHPSlow(py4hw.Logic):
    def __init__(self, parent, name, reset, inc, q):
        super().__init__(parent, name)

        if not(reset is None):
            self.addIn('reset', reset)

        self.addIn('inc', inc)
        self.addOut('q', q)

        wF, wS = CounterHPSlow.split_fast_slow(q.getWidth())

        qF = self.wire('qF', wF)
        qS = self.wire('qS', wS)

        carry = self.wire('carry') # carry from the fast part

        TCounterHP(self, 'fast', reset, inc, qF, carry)
        SlowCounter(self, 'slow', reset, carry, qS)

        py4hw.ConcatenateLSBF(self, 'q', [qF, qS], q)

    def split_fast_slow(n):
        # We find the smallest value of F that satisfies
        #  2^F >= S

        for F in range(n):
            fp = 2**F
            S = n-F

            if (fp >= S):
                return F,S

        return None, None

