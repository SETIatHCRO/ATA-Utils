from pyuvdata import UVData
import sys

#base="guppi_59563_13204_4674987_3c84_0001"
base=sys.argv[1]

uv1 = UVData()
uv1.read("node1/"+base+"_0.uvh5")

uv2 = UVData()
uv2.read("node2/"+base+"_0.uvh5")

uv3 = UVData()
uv3.read("node2/"+base+"_1.uvh5")

uv4 = UVData()
uv4.read("node3/"+base+"_0.uvh5")

uv5 = UVData()
uv5.read("node3/"+base+"_1.uvh5")

uv6 = UVData()
uv6.read("node4/"+base+"_0.uvh5")

uv7 = UVData()
uv7.read("node4/"+base+"_1.uvh5")

uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7

print("Writing ms file")
uvd.write_ms(base+".ms")
uvd.write_uvh5(base+".uvh5")
