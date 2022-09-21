from pyuvdata import UVData
import numpy as np
import sys

#base="guppi_59563_13204_4674987_3c84_0001"
base=sys.argv[1]

uv1 = UVData()
uv1.read("seti-node5/"+base+"_0.uvh5", fix_old_proj=False)
#uv1.downsample_in_time(30)

uv2 = UVData()
uv2.read("seti-node5/"+base+"_1.uvh5", fix_old_proj=False)
#uv2.downsample_in_time(30)

uv3 = UVData()
uv3.read("seti-node6/"+base+"_0.uvh5", fix_old_proj=False)
#uv3.downsample_in_time(30)

uv4 = UVData()
uv4.read("seti-node6/"+base+"_1.uvh5", fix_old_proj=False)
#uv4.downsample_in_time(30)

uv5 = UVData()
uv5.read("seti-node7/"+base+"_0.uvh5", fix_old_proj=False)
#uv5.downsample_in_time(30)

uv6 = UVData()
uv6.read("seti-node7/"+base+"_1.uvh5", fix_old_proj=False)
#uv6.downsample_in_time(30)

uv7 = UVData()
uv7.read("seti-node8/"+base+"_0.uvh5", fix_old_proj=False)
#uv7.downsample_in_time(30)

uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7
try:
    uvd.normalize_by_autos()
    np.nan_to_num(uvd.data_array.real, copy=False, nan=1e-5)
    np.nan_to_num(uvd.data_array.imag, copy=False, nan=0)
    print("Normalizing by autos")
except AttributeError as e:
    pass

print("Writing ms file")
uvd.write_ms(base+"_c.ms")
uvd.write_uvh5(base+"_c.uvh5")
