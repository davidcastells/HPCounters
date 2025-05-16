import os
import shutil
import py4hw
import pandas as pd
import subprocess
from edalize.vivado_reporting import VivadoReporting

dir = '/tmp/testAlveoU50'
projectName = 'testAlveoU50'

class AlveoU50(py4hw.HWSystem):
    def __init__(self):
        super().__init__(name = 'AlveoU50')
        clk = self.wire('clk')
        clockDriver = py4hw.ClockDriver('clk', 50E6, 0, wire=clk)                
        self.clockDriver = clockDriver
        
class c_counter_binary_0_wrapper(py4hw.Logic):
    def __init__(self, parent, name, q):
        super().__init__(parent, name)
        
        self.q = self.addOut('q', q)
        
    def clock(self):
        self.q.prepare(self.g.get())
        
    def verilogBody(self):
        clkname = 'clk'
        return 'c_counter_binary_0 i0(.CLK('+clkname+'), .Q(q));\n'


def testDesign(n, req_freq=None):

    if (os.path.exists(dir)):
        print('removing existing project')
        shutil.rmtree(dir)
    
    os.makedirs(dir)
        
    sys = AlveoU50()

    q = sys.wire('q', n)
    sys.addOut('q', q)

    c_counter_binary_0_wrapper(sys, 'cwrap', q)

    rtl = py4hw.VerilogGenerator(sys)
    rtl_code = rtl.getVerilogForHierarchy(noInstanceNumberInTopEntity=True)

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
    tcl_cmd += 'create_ip -name c_counter_binary -vendor xilinx.com -library ip -version 12.0 -module_name c_counter_binary_0\n'
    tcl_cmd += 'set_property CONFIG.Output_Width {{{}}} [get_ips c_counter_binary_0]\n'.format(n)
    tcl_cmd += 'generate_target {instantiation_template} [get_files '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'
    tcl_cmd += 'generate_target all [get_files  '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'
    tcl_cmd += 'catch { config_ip_cache -export [get_ips -all c_counter_binary_0] }\n'
    tcl_cmd += 'export_ip_user_files -of_objects [get_files '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci] -no_script -sync -force -quiet\n'
    tcl_cmd += 'create_ip_run [get_files -of_objects [get_fileset sources_1] '+dir+'/'+projectName+'.srcs/sources_1/ip/c_counter_binary_0/c_counter_binary_0.xci]\n'

    tcl_cmd += 'set_property strategy Performance_Explore [get_runs impl_1]\n'

    tcl_cmd += 'launch_runs impl_1 -jobs 4\n'
    tcl_cmd += 'wait_on_run impl_1\n'
        
    with open(dir + '/create_project.tcl', 'w') as file:
        file.write(tcl_cmd)
        
    cmd = 'vivado -mode batch -source create_project.tcl'
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
    # dsp = summary['dsp']
    df = rpt['resources']['Primitives']
    dsp = df[df['Ref Name'] == 'CARRY8']['Used'].values[0]
    pins = n+1
    
    return CLB, FF, pins, Fmax, dsp
    
def findFmaxDesign(n):
    # Take care, fmax is reported in MHz, but freq is specified in Hz
    
    print('FIND FMAX START n=',n)
    
    # we start with 50MHz to get an estimate
    ALM, FF, pins, fmax, dsp = testDesign(n)
    
    FL = fmax 
    FH = 2000 # 1 GHz is above the maximum possible frequency for our available FPGAs
    freq = FH
    
    last_fmax = [fmax]

    #while ((FL+1) < FH):
    for i in range(1):

        ALM, FF, pins, fmax, dsp = testDesign(n, freq * 1E6)

        print('FIND FMAX => FL:',FL, 'FH:', FH, 'freq:', freq, '-> fmax:', fmax)
    
        last_fmax.append(fmax)
        
        #if ((len(last_fmax) > 3) and (last_fmax[-1] == last_fmax[-3])):
        #    # If the last 3 results are equal, stop
        #    break 
    
        if (fmax > freq):
            FH = fmax * 1.5
            FL = fmax
            freq = FH
        elif (fmax < freq):
            if (fmax > FL): 
                FL = fmax
            else:
                FH = (max(fmax, FL) + FH) / 2
                freq = FH
        
    fmax = max(last_fmax)
    
    print('FIND FMAX STOP => FL:',FL, 'FH:', FH, 'freq:', freq, 'fmax:', fmax)
    
    return ALM, FF, pins, fmax, dsp   


csv_file = 'data_xilinx.csv'

if os.path.exists(csv_file):
    df = pd.read_csv(csv_file, index_col='n')
else:
    data = {'n':[], 'ALM' : [], 'FF': [], 'pins':[], 'fmax':[], 'dsp':[] }
    df = pd.DataFrame(data)
    df.set_index('n', inplace=True)

def testAll():
    obj_set = set(range(2, 258, 8))
    done_set = set(df.index)
    todo_set = list(obj_set - done_set)
    todo_set.sort()

    print('Obj set:', obj_set)
    print('TODO:', todo_set)

    for n in todo_set:
       print('Testing', n)
       ALM, FF, pins, fmax, dsp = findFmaxDesign(n)
       #data['n'].append(n)
       #data['ALM'].append(ALM)
       #data['FF'].append(FF)
       #data['pins'].append(pins)
       #data['fmax'].append(fmax)
       
       df.loc[n] = {'ALM': ALM, 'FF': FF, 'pins': pins, 'fmax': fmax, 'dsp': dsp}
       df.to_csv(csv_file)


if __name__ == "__main__":
    testAll()
