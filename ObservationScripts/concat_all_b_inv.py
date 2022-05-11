from pyuvdata import UVData
import sys
import numpy as np

#base="guppi_59563_13204_4674987_3c84_0001"
base=sys.argv[1]

uv1 = UVData()
uv1.read("node1/"+base+"_0.uvh5", fix_old_proj=False)
uv1.data_array = np.conj(uv1.data_array)

uv2 = UVData()
uv2.read("node2/"+base+"_0.uvh5", fix_old_proj=False)
uv2.data_array = np.conj(uv1.data_array)

uv3 = UVData()
uv3.read("node2/"+base+"_1.uvh5", fix_old_proj=False)
uv3.data_array = np.conj(uv1.data_array)

uv4 = UVData()
uv4.read("node3/"+base+"_0.uvh5", fix_old_proj=False)
uv4.data_array = np.conj(uv1.data_array)

uv5 = UVData()
uv5.read("node3/"+base+"_1.uvh5", fix_old_proj=False)
uv5.data_array = np.conj(uv1.data_array)

uv6 = UVData()
uv6.read("node4/"+base+"_0.uvh5", fix_old_proj=False)
uv6.data_array = np.conj(uv1.data_array)

uv7 = UVData()
uv7.read("node4/"+base+"_1.uvh5", fix_old_proj=False)
uv7.data_array = np.conj(uv1.data_array)



uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7

print("Writing ms file")
uvd.write_ms(base+"_uvw.ms")
uvd.write_uvh5(base+"_uvw.uvh5")
