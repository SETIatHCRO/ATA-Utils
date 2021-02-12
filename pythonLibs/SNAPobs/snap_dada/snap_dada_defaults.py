create_buf_script = "create_buf.sh"
destroy_buf_script = "destroy_buf.sh"
udpdb_script = "udpdb.sh"
dbsumdb_script = "ata_dbsumdb"
dbsigproc_script = "dbsigproc.sh"
dbnull_script = "dbnull.sh"
#NIC_cores = [8,9,10,11,12,13,14,15,24,25,26,27,28,29,30,31]
NIC_cores = [8,9,10,11,12,13,14,15]
#proc_cores = [4,5,6,7,16,17,18,19,20,21,22,23]
proc_cores = [4,5,6,7]
#bufsze = 16777216 # for spectrometer data, nbit=32 npol=4 nchan=4096
#bufsze = 134217728 # for spectrometer data, nbit=32 npol=4 nchan=4096, nsamp=2048
bufsze = 67108864 # for spectrometer data, nbit=32 npol=4 nchan=4096, nsamp=1024

acclen = 160
