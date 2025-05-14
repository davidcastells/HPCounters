class TCounterHP(py4hw.Logic):
    def __init__(self, parent, name, reset, inc, q, carry):
        super().__init__(parent, name)

        self.addOut('q', q)
        self.addIn('inc', inc)

        if not(reset is None):
            self.addIn('reset', reset)

        if not(carry is None):
            self.addOut('carry', carry)

        w = q.getWidth()
        r = self.wires('r', w, 1)
        t = self.wires('t', w+1, 1)

        py4hw.ConcatenateLSBF(self, 'q', r, q)

        for i in range(w):
            py4hw.TReg(self, 't{}'.format(i), t[i], r[i], reset=reset)

            if (i == 0):
                py4hw.Buf(self, 'one', inc, t[i])
                py4hw.And2(self, 'nt{}'.format(i), r[i], inc, t[i+1])
            else:
                #py4hw.And(self, 'and{}'.format(i), r[0:i], t[i])
                last = r[i]

                for j in range(i):
                    nr = self.wire('d{}_{}'.format(i,j), last.getWidth())

                    py4hw.Reg(self, 'd{}_{}'.format(i,j), last, nr, reset=reset)
                    if (j == i-1):
                        py4hw.And(self, 'nt{}'.format(i), [inc,nr, r[0]], t[i+1])
                    else:
                        nnr = self.wire('nt{}_{}'.format(i,j), last.getWidth())
                        py4hw.And(self, 'nt{}_{}'.format(i,j), [inc, nr, r[i-j-1]], nnr)
                        last = nnr

        if not(carry is None):
            py4hw.Buf(self, 'carry', t[w], carry)

