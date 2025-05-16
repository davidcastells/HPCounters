import py4hw

class TCounter(py4hw.Logic):
    def __init__(self, parent, name, reset, q):
        super().__init__(parent, name)

        self.addOut('q', q)

        w = q.getWidth()
        r = self.wires('r', w, 1)
        t = self.wires('t', w, 1)

        py4hw.ConcatenateLSBF(self, 'q', r, q)

        for i in range(w):
            py4hw.TReg(self, 't{}'.format(i), t[i], r[i])

            if (i == 0):
                py4hw.Constant(self, 'one', 1, t[i])
            else:
                py4hw.And(self, 'and{}'.format(i), r[0:i], t[i])

