import py4hw

class TCounterForward(py4hw.Logic):
    def __init__(self, parent, name, reset, inc, q):
        super().__init__(parent, name)

        if not(reset is None):
           self.addIn('reset', reset)
        self.addIn('inc', inc)
        self.addOut('q', q)

        w = q.getWidth()
        r = self.wires('r', w, 1)
        one = self.wire('one')
        ci = self.wires('ci', w, 1)
        co = self.wires('co', w, 1)

        s = self.wires('s', w, 1)
        d = self.wires('d', w, 1)

        py4hw.ConcatenateLSBF(self, 'q', r, q)

        for i in range(w):
            py4hw.And2(self, 'pre_co{}'.format(i), ci[i], r[i], co[i])


            py4hw.TReg(self, 'q{}'.format(i), ci[i], r[i], reset=reset, enable=inc)

            if (i == 0):
                py4hw.Constant(self, 'ci0', 1, ci[i])
            else:
                py4hw.Buf(self, 'ci{}'.format(i), co[i-1], ci[i])

