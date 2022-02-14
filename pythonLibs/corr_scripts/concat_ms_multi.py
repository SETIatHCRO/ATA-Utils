from pyuvdata import UVData
import sys

#base="guppi_59563_13204_4674987_3c84_0001"
base="uvh5_filename"

uv1 = UVData()
uv1.read(".uvh5")

uv2 = UVData()
uv2.read("node2.uvh5")

uv3 = UVData()
uv3.read("node.uvh5")

uv4 = UVData()
uv4.read("nod_0.uvh5")

uv5 = UVData()
uv5.read("node1.uvh5")

uv6 = UVData()
uv6.read("node.uvh5")

uv7 = UVData()
uv7.read("nod_1.uvh5")

uv8 = UVData()
uv8.read("nod_1.uvh5")

uv9 = UVData()
uv9.read("nod_1.uvh5")

uv10 = UVData()
uv10.read("nod_1.uvh5")

uv11 = UVData()
uv11.read("nod_1.uvh5")

uv12 = UVData()
uv12.read("nod_1.uvh5")

uv13 = UVData()
uv13.read("nod_1.uvh5")

uv14 = UVData()
uv14.read("nod_1.uvh5")

uv15 = UVData()
uv15.read("nod_1.uvh5")

uv16 = UVData()
uv16.read("nod_1.uvh5")

uv17 = UVData()
uv17.read("nod_1.uvh5")

uv18 = UVData()
uv18.read("nod_1.uvh5")



uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7 + uv8 + uv9 + uv10 + uv11 + uv12 + uv13 + uv14 + uv15 + uv16 + uv17 + uv18

print("Writing ms file")
uvd.write_ms("uvh5_3c84_freqs.ms")
uvd.write_uvh5("uvh5_3c84_freqs.uvh5")
