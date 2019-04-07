# BeamformerDataRecord

Hashpipe based modules to read beam data from the beamformer and write to disk.

Note: haskpipe must be installed. Install from https://github.com/david-macmahon/hashpipe

## beam_rw.sh

This shell script starts up beam_read.so to read data from the beamformer socket and
pass the data to beam_write.so to write the data to disk.

example: ./beam_rw.sh 50000 /data/raw.dat
         reads from port 50000, write the data to /data/raw.dat

## beam_split.sh

This shell script starts up beam_read.so to read data from the beamformer socket and
pass the data to beamsplit.so.

beam_split.so takes the data and does 2 things with each packet:

  1) Writes the data to the ip1:port1 UDP socket
  2) Writes the data to ip2:port2 while decimating the data.

The decimating is useful if you want to send the data to a slow application, such as baudline.

Decimantion is defines as sending on every "nth" 4160 byte packet.

## beam_chunks.sh

This shell script starts up beam_read.so to read data from the beamformer socket and
pass the data to beam_chunks.so.

beam_chunks.so writes out the beam data into snmaller file sized onto idks. Also
the data is sent out to another port for display in a program such as baudline.


