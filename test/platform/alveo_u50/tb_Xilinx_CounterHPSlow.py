import os
import shutil
import py4hw
import pandas as pd
import subprocess
import synth_automation as sa
from edalize.vivado_reporting import VivadoReporting

dir = '/tmp/testAlveoU50'
projectName = 'testAlveoU50'


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
            
                
class SlowPart(py4hw.Logic):
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
        pre_co = self.wires('pre_co', w, 1)
        #pre_s = self.wires('pre_s', w, 1)
        s = self.wires('s', w, 1)
        d = self.wires('d', w, 1)
        
        py4hw.ConcatenateLSBF(self, 'q', r, q)
        
        for i in range(w):
            py4hw.Xor2(self, 'pre_s{}'.format(i), ci[i], r[i], s[i])
            py4hw.And2(self, 'pre_co{}'.format(i), ci[i], r[i], pre_co[i])

            #py4hw.Reg(self, 's{}'.format(i), pre_s[i], s[i])
            py4hw.Reg(self, 'co{}'.format(i), pre_co[i], co[i])
            
            py4hw.Reg(self, 'q{}'.format(i), s[i], r[i], reset=reset, enable=inc)
            
            if (i == 0):
                py4hw.Constant(self, 'ci0', 1, ci[i])
            else:
                py4hw.Buf(self, 'ci{}'.format(i), co[i-1], ci[i])
                
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
        SlowPart(self, 'slow', reset, carry, qS)
        
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


class AlveoU50(py4hw.HWSystem):
    def __init__(self):
        super().__init__(name = 'AlveoU50')
        clk = self.wire('clk')
        clockDriver = py4hw.ClockDriver('clk', 50E6, 0, wire=clk)                
        self.clockDriver = clockDriver
        


def testDesign(n, req_freq=None):

    if (os.path.exists(dir)):
        print('removing existing project')
        shutil.rmtree(dir)
    
    os.makedirs(dir)
        
    sys = AlveoU50()

    q = sys.wire('q', n)
    sys.addOut('q', q)

    reset = None # sys.wire('reset')

    inc = sys.wire('inc')
 
    py4hw.Constant(sys, 'inc', 1, inc)

    CounterHPSlow(sys, 'counter', reset, inc, q)

    rtl = py4hw.VerilogGenerator(sys)
    rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=True)

    print('finished generating Verilog')
    with open(dir + '/AlveoU50.v', 'w') as file:
        file.write(rtl_code)

    clk_freq_txt = 'create_clock -period 1 [get_ports clk]\n'

    with open(dir + '/clk_freq.xdc', 'w') as file:
        file.write(clk_freq_txt)


    tcl_cmd = 'create_project '+projectName+' . -part xcu50-fsvh2104-2-e \n'
    tcl_cmd += 'set_property board_part xilinx.com:au50:part0:1.3 [current_project]\n'
    tcl_cmd += 'add_files -norecurse '+dir+'/AlveoU50.v\n'
    tcl_cmd += 'add_files -fileset constrs_1 '+dir+'/clk_freq.xdc\n'
    #tcl_cmd += 'add_files -fileset constrs_1 [get_property DIRECTORY [current_project]]/clk_freq.xdc\n'

    tcl_cmd += 'update_compile_order -fileset sources_1\n'
    # tcl_cmd += 'create_ip -name c_counter_binary -vendor xilinx.com -library ip -version 12.0 -module_name c_counter_binary_0\n'
    # tcl_cmd += 'set_property CONFIG.Output_Width {{{}}} [get_ips c_counter_binary_0]\n'.format(n)
    # tcl_cmd += 'generate_target {instantiation_template} [get_files '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'
    #tcl_cmd += 'generate_target all [get_files  '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'
    #tcl_cmd += 'catch { config_ip_cache -export [get_ips -all c_counter_binary_0] }\n'
    #tcl_cmd += 'export_ip_user_files -of_objects [get_files '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci] -no_script -sync -force -quiet\n'
    #tcl_cmd += 'create_ip_run [get_files -of_objects [get_fileset sources_1] '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'

    tcl_cmd += 'set_property strategy Performance_Explore [get_runs impl_1]\n'

    tcl_cmd += 'launch_runs impl_1 -jobs 4\n'
    tcl_cmd += 'wait_on_run impl_1\n'
        
    with open(dir + '/create_project.tcl', 'w') as file:
        file.write(tcl_cmd)
        
    cmd = 'vivado -stack 2000 -mode batch -source create_project.tcl'
    try:
        result = subprocess.run(cmd, cwd=dir, shell=True, check=True)
        print("Command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")

    rpt = VivadoReporting.report(dir+ '/'+projectName+'.runs/impl_1/')

    summary = VivadoReporting.report_summary(rpt['resources'], rpt['timing'])

    CLB = summary['lut']
    FF = summary['reg']
    Fmax = summary['fmax']['clk']
    pins = n+1
    
    return CLB, FF, pins, Fmax
    


csv_file = 'data_xilinx_counter_hpslow.csv'


if __name__ == "__main__":
    sa.testAll(csv_file, board='AlveoU50', testDesign=testDesign)
