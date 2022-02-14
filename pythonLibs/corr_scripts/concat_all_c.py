from pyuvdata import UVData
import sys

#base="guppi_59563_13204_4674987_3c84_0001"
base=sys.argv[1]

uv1 = UVData()
uv1.read("node5/"+base+"_0.uvh5", fix_old_proj=False)
uvw = uv1.uvw_array

uv2 = UVData()
uv2.read("node5/"+base+"_1.uvh5", fix_old_proj=False)
uv2.uvw_array = uvw

uv3 = UVData()
uv3.read("node6/"+base+"_0.uvh5", fix_old_proj=False)
uv3.uvw_array = uvw

uv4 = UVData()
uv4.read("node6/"+base+"_1.uvh5", fix_old_proj=False)
uv4.uvw_array = uvw

uv5 = UVData()
uv5.read("node7/"+base+"_0.uvh5", fix_old_proj=False)
uv5.uvw_array = uvw

uv6 = UVData()
uv6.read("node7/"+base+"_1.uvh5", fix_old_proj=False)
uv6.uvw_array = uvw

uv7 = UVData()
uv7.read("node8/"+base+"_0.uvh5", fix_old_proj=False)
uv7.uvw_array = uvw

uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7

print("Writing ms file")
uvd.write_ms(base+"_c.ms")
uvd.write_uvh5(base+"_c.uvh5")
