import redis
from string import Template
from SNAPobs import snap_defaults
from SNAPobs.snap_hpguppi import auxillary as hpguppi_aux

NBITS              = 4
REDISHOST          = 'redishost'
MAX_CHANS_PER_PKT  = 128

def fengine_meta_key_values(n_bits=8):
	FEnChan = 4096 if n_bits == 4 else 2048 if n_bits == 8 else 0
	BW			= snap_defaults.bw * 1e6 # in Hz
	return {
		'NBITS'	   : n_bits,
		'FENCHAN'  : FEnChan,
		'NPOL'     : 2,
		'TBIN'     : 1/(BW/FEnChan),
		'N_TIMES_PER_PKT' : 16,
		'FOFF'		 : BW / (FEnChan * 1e6) # in Mhz
	}


# BINDHOST           = 'ens6d1'# static once the instance starts
# DATADIR            = '/mnt/buf0' # best left to the configuration (numactl grouping of NVMe mounts)
PROJID             = 'dmpauto'
BACKEND            = 'GUPPI'
BANK               = '.'
PKTFMT             = 'ATASNAPV'
OBSSTART           = 0
OBSSTOP            = 0

REDISGETGW = Template('hashpipe://${host}/${inst}/status')
REDISGETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/status'
REDISSETGW = Template('hashpipe://${host}/${inst}/set')
REDISSETGW_re = r'hashpipe://(?P<host>[^/]+)/(?P<inst>[^/]+)/set'
REDISSET = 'hashpipe:///set'
REDISPOSTPROCHASH = Template('postprocpype://${host}/${inst}/status')
REDISPOSTPROCHASH_re = r'postprocpype://(?P<host>[^/]+)/(?P<inst>[^/]+)/status'
REDISPOSTPROCSET = 'postprocpype:///set'

redis_obj = redis.Redis(host=REDISHOST)

seti_node_hostnames = [
	f"seti-node{i}"
	for i in range(1, 10)
]

seti_node_instances = [
	i
	for i in range(0, 2)
]

hashpipe_targets_LoA = {
	'seti-node1': [0],
	'seti-node2': [0,1],
	'seti-node3': [0,1],
	'seti-node9': [0,1],
}

hashpipe_targets_LoB = {
	'seti-node5': [0,1],
	'seti-node6': [0,1],
	'seti-node7': [0,1],
	'seti-node8': [0],
}

hashpipe_targets_LoC = {}
hashpipe_targets_LoD = {}

def resolve_hashpipe_targets():
	global hashpipe_targets_LoA, hashpipe_targets_LoB, hashpipe_targets_LoC, hashpipe_targets_LoD

	instances = [0, 1]

	hashpipe_targets_LoA = {}
	hashpipe_targets_LoB = {}
	hashpipe_targets_LoC = {}
	hashpipe_targets_LoD = {}
	for seti_node in seti_node_hostnames:
		for instance in instances:
			redis_get_chan = REDISGETGW.substitute(
				host=seti_node, inst=instance
			)

			antenna_list = hpguppi_aux.get_antennae_of_redis_chan(
				redis_obj,
				redis_get_chan
			)
			if len(antenna_list) == 0:
				continue

			# print(f"{seti_node}.{instance}: {antenna_list}")
			lo = antenna_list[0][-1]
			if lo == "A":
				hashpipe_targets_LoA[seti_node] = hashpipe_targets_LoA.get(seti_node, [])
				hashpipe_targets_LoA[seti_node].append(instance)
			elif lo == "B":
				hashpipe_targets_LoB[seti_node] = hashpipe_targets_LoB.get(seti_node, [])
				hashpipe_targets_LoB[seti_node].append(instance)
			elif lo == "C":
				hashpipe_targets_LoC[seti_node] = hashpipe_targets_LoC.get(seti_node, [])
				hashpipe_targets_LoC[seti_node].append(instance)
			elif lo == "D":
				hashpipe_targets_LoD[seti_node] = hashpipe_targets_LoD.get(seti_node, [])
				hashpipe_targets_LoD[seti_node].append(instance)

resolve_hashpipe_targets()