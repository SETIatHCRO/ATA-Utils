#!/usr/bin/env python
import casperfpga
from multiprocessing import Pool
from SNAPobs import snap_config
import sys,os

if "-h" in sys.argv or "--help" in sys.argv:
    print("")
    print("%s [rfsoc1, rfsoc2, ...]" %os.path.basename(sys.argv[0]))
    print("if no hostnames are passed, assume all 1-22 rfsocs")
    sys.exit(-1)

if len(sys.argv) > 1:
    hosts = sys.argv[1:]
else:
    hosts = [
            f"rfsoc{i}"
            for i in range(1,22)
    ]
#hosts = ['rfsoc9']
#hosts = ['rfsoc6-ctrl-1', 'rfsoc7-ctrl-1']
#hosts = ['rfsoc10-ctrl-1']
#fpgfile = '/opt/mnt/share/test_onehundredgbe_jumbo_2021-11-01_1154.fpg'
fpgfile = snap_config.ATA_CFG['DEPROGFPG']

def reprog(host):
	cfpga = casperfpga.CasperFpga(host, transport=casperfpga.KatcpTransport)
	return cfpga.upload_to_ram_and_program(fpgfile)


with Pool(len(hosts)) as pool:
	async_results = {}

	for host in hosts:
		print("Programming %s with %s" % (host, fpgfile))
		async_results[host] = pool.apply_async(
			reprog,
			(
				host,
			)
		)

	async_failures = {}
	for host, async_result in async_results.items():
		try:
			print(f"Joining async reprogramming of {host}...")
			res = async_result.get()
		except BaseException as err:
			async_failures[host] = err
	
	if len(async_failures) > 0:
		print(f"Failures occurred in asynchronous reprogramming:\n{async_failures}")
		exit(1)
