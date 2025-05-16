import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

df_lpm = None
df_t = None
df_thp = None
df_thpc = None
df_hps = None

def load():
    global df_lpm
    global df_t
    global df_thp
    global df_thpc
    global df_hps

    df_lpm = pd.read_csv('data_xilinx.csv', index_col='n')
    df_t = pd.read_csv('data_xilinx_tcounter.csv', index_col='n')
    df_thp = pd.read_csv('data_xilinx_tcounter_hp.csv', index_col='n')
    df_thpc = pd.read_csv('data_xilinx_tcounter_hp_composed.csv', index_col='n')
    df_hps = pd.read_csv('data_xilinx_counter_hpslow.csv', index_col='n')
    
    df_lpm = df_lpm.sort_index()
    df_t = df_t.sort_index()
    df_thp = df_thp.sort_index()
    df_thpc = df_thpc.sort_index()
    df_hps = df_hps.sort_index()

label_lpm='AMD Counter IP Core'
label_hps='HP/slow'
label_thp='T-Counter HP'

def showALMFF(filter=['lpm','t', 'thp', 'hps'], saveas=None, maxHPS=True):

    fig = plt.figure(figsize=(4, 3))
    if ('lpm' in filter):
       plt.plot(df_lpm.index, df_lpm['ALM']+df_lpm['FF']+8*df_lpm['dsp'], linestyle='--', label=label_lpm)
    if ('t' in filter):
       plt.plot(df_t.index, df_t['ALM']+df_t['FF'], label='T-Counter')
    if ('thp' in filter):
       plt.plot(df_thp.index, df_thp['ALM']+df_thp['FF'], label=label_thp)
    if ('hps' in filter):
       plt.plot(df_hps.index, df_hps['ALM']+df_hps['FF'], label=label_hps)
    plt.title('CLBs + FFs + 8 \u00D7 CARRY8')
    plt.legend()
    if (maxHPS):
        plt.ylim(0, 1400)
        
    if not(saveas is None):
       plt.savefig(saveas)
    plt.show()

def showALM(filter=['lpm','t', 'thp', 'hps']):
    if ('lpm' in filter):
       plt.plot(df_lpm.index, df_lpm['ALM'], linestyle='--', label='lpm')
    if ('t' in filter):
       plt.plot(df_t.index, df_t['ALM'], label='tcounter')
    if ('thp' in filter):
       plt.plot(df_thp.index, df_thp['ALM'], label=label_thp)
    if ('hps' in filter):
       plt.plot(df_hps.index, df_hps['ALM'], label='HP/slow')
    plt.legend()
    plt.show()


def showFF(filter=['lpm','t', 'thp', 'hps']):
    if ('lpm' in filter):
        plt.plot(df_lpm.index, df_lpm['FF'], linestyle='--', label='lpm')
    if ('t' in filter):
        plt.plot(df_t.index, df_t['FF'], label='tcounter')
    if ('thp' in filter):
        plt.plot(df_thp.index, df_thp['FF'], label=label_thp)
    if ('hps' in filter):
        plt.plot(df_hps.index, df_hps['FF'], label='HP/slow')
    plt.legend()
    plt.show()


def showFmax(filter=['lpm','t', 'thp', 'hps'], saveas=None):
    fig = plt.figure(figsize=(4, 3))
    
    if ('lpm' in filter):
        plt.plot(df_lpm.index, df_lpm['fmax'], linestyle='--', label=label_lpm)
    if ('t' in filter):
        plt.plot(df_t.index, df_t['fmax'], label='tcounter')
    if ('thp' in filter):
        plt.plot(df_thp.index, df_thp['fmax'], label=label_thp)
    if ('hps' in filter):
        plt.plot(df_hps.index, df_hps['fmax'], label=label_hps)
    plt.legend()
    plt.title('$f_{max}$')
    plt.ylim(0, 2000)
    if not(saveas is None):
       plt.savefig(saveas)
    plt.show()
    
def showTclk(filter=['lpm','t', 'thp', 'hps'], saveas=None):
    fig = plt.figure(figsize=(4, 3))

    if ('lpm' in filter):
        plt.plot(df_lpm.index, 1E3/df_lpm['fmax'], linestyle='--', label=label_lpm)
    if ('t' in filter):
        plt.plot(df_t.index, 1E3/df_t['fmax'], label='tcounter')
    if ('thp' in filter):
        plt.plot(df_thp.index, 1E3/df_thp['fmax'], label=label_thp)
    if ('hps' in filter):
        plt.plot(df_hps.index, 1E3/df_hps['fmax'], label=label_hps)
    plt.legend()
    plt.ylabel('(ns)')
    plt.xlabel('n')
    plt.title('$t_{clk}$')
    #plt.ylim(0, 700)
    if not(saveas is None):
       plt.savefig(saveas)
    plt.show()


# Function to check if row i dominates row j
def dominates(df, i, j):
    res_i = df.iloc[i]['FF']+df.iloc[i]['ALM']
    res_j = df.iloc[j]['FF']+df.iloc[j]['ALM']
    return ((res_i <= res_j) and (df.iloc[i]['fmax'] >= df.iloc[j]['fmax']))

def getParetoFront(df):
    pareto_front_indices = []
    for i in range(len(df)):
        if not any(dominates(df, j, i) for j in range(len(df)) if i != j):
            pareto_front_indices.append(i)

    pareto_front_df = df.iloc[pareto_front_indices]
    return pareto_front_df

def showComposed(saveas=None):
    fig = plt.figure(figsize=(4, 3))
    x_values = np.array(df_thpc['FF'])+np.array(df_thpc['ALM'])
    y_values = np.array(df_thpc['fmax'])
    bs_values = np.array(df_thpc.index)
    
    plt.title('Tradeoff performance/resources for\ndifferent block sizes ($bs$)')

    plt.scatter(x_values, y_values, color='gray')

    df = getParetoFront(df_thpc)

    x_values = np.array(df['FF'])+np.array(df['ALM'])
    y_values = np.array(df['fmax'])
    bs_values = np.array(df.index)

    plt.plot(x_values, y_values, color='red')

    for i in range(len(x_values)):
        if not(bs_values[i] in [20,52]):
            continue
            
        arrowprops = dict(facecolor='blue', arrowstyle='->')
        plt.annotate('{}'.format(bs_values[i]), (x_values[i], y_values[i]), textcoords="offset points", xytext=(-5,10), ha='center', fontsize=12)

    plt.ylabel('$f_{max}$')
    plt.xlabel('FF+CLB')
    plt.ylim(0, 1000)
    plt.tight_layout()
    if not(saveas is None):
       plt.savefig(saveas)
    plt.show()


def saveFigures():
    #showALMFF(filter=['lpm', 'thp'], saveas='XilinxLPMvsTHP_ALMFF.pdf')
    #showFmax(filter=['lpm', 'thp'], saveas='XilinxLPMvsTHP_Fmax.pdf')
    showALMFF(filter=['lpm', 'thp', 'hps'], saveas='Xilinx_ALMFF.pdf')
    showFmax(filter=['lpm', 'thp', 'hps'], saveas='Xilinx_Fmax.pdf')
    showTclk(filter=['lpm', 'thp', 'hps'], saveas='Xilinx_Tclk.pdf')
    showComposed(saveas='Xilinx_Composed.pdf')


def xilinxReport():
    global summary
    global rpt
    from edalize.vivado_reporting import VivadoReporting

    dir = '/tmp/testAlveoU50'
    projectName = 'testAlveoU50'

    rpt = VivadoReporting.report(dir+ '/'+projectName+'.runs/impl_1/')
    summary = VivadoReporting.report_summary(rpt['resources'], rpt['timing'])
