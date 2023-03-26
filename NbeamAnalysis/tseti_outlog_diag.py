
    # imports
import argparse
import pandas as pd
import numpy as np
import os
import glob
import time

    # functions
# input argument parse function
# using this is optional, depending on how you want the timing output. Seconds works in most cases.
def parse_args():
    parser = argparse.ArgumentParser(description='turboSETI processing diagnostics.')
    parser.add_argument('-t', dest='timescale', metavar='secs/mins/hrs', type=str, default='secs',
                        help='print in secs/mins/hrs? Default is seconds.')
    args = parser.parse_args()
    odict = vars(args)
    return odict

#elapsed time function
def get_elapsed_time(start=0,end=0):
    if not end:
        end = time.time() - start
    time_label = 'seconds'   
    if end > 86400:
        end = end/86400
        time_label = 'days' 
    elif end > 3600:
        end = end/3600
        time_label = 'hours'
    elif end > 60:
        end = end/60
        time_label = 'minutes'
    return end, time_label

    # the program starts here
start=time.time()

# data directory hard-coded. sub-directory tree hard-coded as well
data_dir = '/mnt/datac-netStorage-40G/projects/p004/'
observations = sorted(glob.glob(f'{data_dir}20*/'))
# initializing counter variables
num_ints=0
num_nodes=0
num_fils=0
total_nodecount=0
total_intcount=0
total_obscount=0
tot_obs_nodes=[]
tot_obs_ints=[]
nodenames=[]
# this loop counts all the files, nodes, and integrations of each observation
for o,obs in enumerate(observations):    
    ints = sorted(glob.glob(f'{obs}*trappist*/'))
    num_ints+=len(ints)
    total_obscount+=1
    tot_obs_nodes.append(0)
    tot_obs_ints.append(0)
    for n,i in enumerate(ints):
        nodes = sorted(glob.glob(f'{i}seti-node*/'))
        num_nodes+=len(nodes)
        total_intcount+=1
        tot_obs_ints[o]+=1
        for node in nodes:
            fils = sorted(glob.glob(f'{node}fil*.fil'))
            num_fils+=len(fils)
            nodenames.append(node)
            total_nodecount+=1
            tot_obs_nodes[o]+=1

# output logs hardcoded based on the bash script output
outlogs = sorted(glob.glob("obs_*_out.txt"))

# initializing counter comparison variables
node_secs=np.zeros(len(nodenames))
int_secs=np.zeros(len(nodenames))
obs_secs=np.zeros(len(nodenames))
node=0
nodecount=0
intcount=0
obs_nodes=[]
obs_nodes_secs=[]
obs_ints=[]
obs_ints_secs=[]

# this loop iterates through the output log to see how long processing took
for o,outlog in enumerate(outlogs):
    obs_ints.append(0)
    obs_ints_secs.append(0)
    obs_nodes.append(0)
    obs_nodes_secs.append(0)
    searchfile = open(outlog,'r').readlines()
    for ell,line in enumerate(searchfile):
        if " seconds to complete this node..." in line:
            node_sec=int(line.split(' seconds')[0].split('It took ')[-1])
            node_secs[node]=node_sec
            nodecount+=1
            obs_nodes[o]+=1
            obs_nodes_secs[o]+=node_sec
            node+=1
        if " seconds to complete this integration block..." in line:
            int_sec=int(line.split(' seconds')[0].split('It took ')[-1])
            int_secs[node-1]=int_sec
            nodecount=0
            obs_ints[o]+=1
            obs_ints_secs[o]+=int_sec
        if " seconds to complete this night of observations..." in line:
            obs_sec=int(line.split(' seconds')[0].split('It took ')[-1])
            obs_secs[node-1]=obs_sec

# The rest of this collates the processing times into a dataframe and outputs statistics
data = [np.array(nodenames)]
data.append(np.array(node_secs))
data.append(np.array(int_secs))
data.append(np.array(obs_secs))

col_secs=['nodenames', 'node_secs', 'int_secs', 'obs_secs']
col_mins=['nodenames', 'node_mins', 'int_mins', 'obs_mins']
col_hrs=['nodenames', 'node_hrs', 'int_hrs', 'obs_hrs']

df1 = pd.DataFrame(np.array(data, dtype="O").T,columns=col_secs[:len(data)])
df2 = pd.DataFrame(np.array(data, dtype="O").T,columns=col_mins[:len(data)])
df3 = pd.DataFrame(np.array(data, dtype="O").T,columns=col_hrs[:len(data)])

df = df1
coeff=1
cmd_args = parse_args()
arg = cmd_args["timescale"]
if arg == 'mins':
    coeff=60
    df = df2
elif arg == 'hrs':
    coeff=3600
    df = df3

df = df.replace(0, np.NaN)
df.iloc[:,1:]/=coeff
print(df.describe(),"\n")

for o,outlog in enumerate(outlogs):
    ETA,ETA_label=get_elapsed_time(end=obs_nodes_secs[o]*(tot_obs_nodes[o]/obs_nodes[o]-1))
    ETA=f"ETA: {ETA:.2f}"
    if tot_obs_nodes[o]==obs_nodes[o]:
        ETA,ETA_label=get_elapsed_time(end=obs_nodes_secs[o])
        ETA=f"{obs_nodes[o]} nodes completed in {ETA:.2f}"
    print(f'{outlog}\tnodes: {obs_nodes[o]/tot_obs_nodes[o]*100:.2f}%\t ints: {obs_ints[o]/tot_obs_ints[o]*100:.2f}%\t{ETA} {ETA_label}')

print(f'\n{df.iloc[:,1].count()} nodes out of {total_nodecount} total nodes processed.') 
print(f'{df.iloc[:,2].count()} integrations out of {total_intcount} total integrations processed.')
print(f'{df.iloc[:,3].count()} observations out of {total_obscount} total observations processed.')
print(f'Data processing is {df.iloc[:,1].count()/total_nodecount*100:.2f}% complete.\n')

end, time_label = get_elapsed_time(start)
print(f"\nRunning these diagnostics took %.2f {time_label}.\n" %end)