# Data Acquisition - HpDaq

The [hpguppi_daq repository](https://github.com/SETIatHCRO/hpguppi_daq) contains the threads that run within the [hashpipe](https://github.com/SETIatHCRO/hashpipe) framework to constitute the data-acquisition pipelines.
## Operation
The hashpipe-threads communicate via IPC shared-buffers. The buffers are internally demarcated into a FITS header and binary data pair.
### Status Buffer

The overall pipeline has a FITS formatted status buffer, from which key-values are parsed to control the internal operations of the pipeline (eg. recording start/stop packet-indices or beam-formation coordinates).

Read/write access to the status buffer is exposed via the `hashpipe_redis_gateway.rb` executable (from the [rb-hashpipe](https://github.com/david-macmahon/rb-hashpipe) gem) which creates a redis hash that mirrors the status buffer and a channel that receives updates to be written to the status buffer.

A convenience executable, [set_hashpipe_keys.py](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/scripts/set_hashpipe_keys.py), is provided by [ATA-Utils/pythonLibs](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs) to write key-values via the redis-gateway to a hashpipe instance.

### Modes

An instance of hashpipe is functionally defined by the threads that constitute the pipeline. The modes (sets of threads) in use at the ATA are defined in the [config_hpguppi.yml](https://github.com/SETIatHCRO/hpguppi_daq/blob/master/src/config_hpguppi.yml#L1-L124) of the repository (stored on-site under `/opt/mnt/share/config_hpguppi.yml`).

The threads are summarised as follows:
- Network package processing
	- hpguppi_ibvpkt_thread
		- manages the IBV-flows that receive network packets into RAM.
	- hpguppi_ata_ibv_payload_order_thread
		- Aligns the packet-payloads to form databuffers with contiguous dimensions.
- Data Processing 
	- hpguppi_ata_xgpu_thread
		- Instantiates xGPU to process the in-databuffer and output correlated data.
	- hpguppi_ata_xintegration_thread
		- Further integrates correlated data CPU-side
	- hpguppi_ata_blade_beamformer_thread
		- Instantiates BLADE, in one of many modes (BLADE is a nested GPU-side pipeline).
- File Output
	- hpguppi_ata_obs_uvh5disk_thread
		- Writes out uvh5 files. (in progress to v1.1)
	- hpguppi_atasnap_obs_rawdisk_thread
		- Writes out GUPPI RAW files.
	- hpguppi_ata_fildisk_thread
		- Writes out filterbank files, either in SIGPROC (.fil) or HDF5 (.fbh5) formats
## Control

The data-acquisition of the hpdaq instances requires knowledge of the incoming data-stream (the port number, number of antenna and channels etc.). This is mediated by the `meta_marshall` service.

### Meta-Marshall

The [meta-marshall](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/scripts/meta_marshall.py) process periodically queries the F-Engines to collect the overall image of the data-streams coming out of them. The list of F-Engines is scraped from the `ATA Snap Tab file` ([code](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/scripts/meta_marshall.py#L25-L26)) :wrench:. This metadata is then pushed via the appropriate keys in the redis-gateway to the hashpipe instances that are the destinations of the F-Engines' packets.

These are the (possibly stale) keys that it populates:
`OBSBW, SCHAN, SUBBAND, NCHAN, OBSNCHAN, OBSFREQ, CHAN_BW, FENCHAN, NANTS, NPOL, PKTNCHAN, TBIN, NBITS, PKTNTIME, SYNCTIME, PKTFMT, SOURCE, RA, DEC, RA_STR, DEC_STR, AZ, EL, ANTNAMES, XPCTGBPS, REFANTNM`

:wrench: **The destination IP-address of the packets is translated to a GPU hostname via python's `socket.gethostbyaddr()` and then processed to determine which instance of hashpipe via the hostname string ([code](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/populate_meta.py#L155-L175)).**  
### record_in

The `snap_hpguppi/record_in` [module](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/record_in.py) of the `ATA-Utils/pythonLibs/SNAPobs` package exposes control of hashpipe recording. It collects the source-name of the telescope, converts the instructed start/stop time to packet-indices and then pushes these key-values to the hashpipe instances via their redis-hash.

### Observational Scripting

Observational scripting can make use of some exposed constant Lo-groupings of hashpipe instances ([code](https://github.com/SETIatHCRO/ATA-Utils/blob/master/pythonLibs/SNAPobs/snap_hpguppi/snap_hpguppi_defaults.py#L43-L68)) :wrench:. 

### Instance orchestration

Controlling the mode of the hashpipe instances is accomplished via ansible-playbooks (stored under /home/sonata/src/ansible_playbooks/hashpipe/, executed with `ansible-playbook` on `obs-node1`).

:wrench: The hashpipe instances that are targeted by the playbooks are under the `setinodes` group specified in `/etc/ansible/hosts`.

## Monitoring

The [pipeline-monitor](https://github.com/MydonSolutions/atapipelinemonitor) exposed at `pipeline-monitor.hcro.org:8081/` (locally the `redishost` machine) exposes summative dashboards for the hashpipe nodes, reflecting their redis-hashes (effectively their status buffers). 

:wrench: The list of hashpipe instances to monitor is hard-coded in the main.html template ([code](https://github.com/MydonSolutions/atapipelinemonitor/blob/master/public/templates/main.html#L340-L358)).
