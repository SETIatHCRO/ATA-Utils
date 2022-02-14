from pyuvdata import UVData
import sys

#base="guppi_59563_13204_4674987_3c84_0001"
base=sys.argv[1]

uv1 = UVData()
uv1.read("node1/"+base+"_0.uvh5", fix_old_proj=False)
ra = uv1.phase_center_ra
dec = uv1.phase_center_dec
uvw = uv1.uvw_array
app_ra = uv1.phase_center_app_ra
app_dec = uv1.phase_center_app_dec
f_pa = uv1.phase_center_frame_pa

uv2 = UVData()
uv2.read("node2/"+base+"_0.uvh5", fix_old_proj=False)
uv2.phase_center_ra = ra
uv2.phase_center_dec = dec
uv2.uvw_array = uvw
uv2.phase_center_app_ra = app_ra
uv2.phase_center_app_dec = app_dec
uv2.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uv3 = UVData()
uv3.read("node2/"+base+"_1.uvh5", fix_old_proj=False)
uv3.phase_center_ra = ra
uv3.phase_center_dec = dec
uv3.uvw_array = uvw
uv3.phase_center_app_ra = app_ra
uv3.phase_center_app_dec = app_dec
uv3.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uv4 = UVData()
uv4.read("node3/"+base+"_0.uvh5", fix_old_proj=False)
uv4.phase_center_ra = ra
uv4.phase_center_dec = dec
uv4.uvw_array = uvw
uv4.phase_center_app_ra = app_ra
uv4.phase_center_app_dec = app_dec
uv4.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uv5 = UVData()
uv5.read("node3/"+base+"_1.uvh5", fix_old_proj=False)
uv5.phase_center_ra = ra
uv5.phase_center_dec = dec
uv5.uvw_array = uvw
uv5.phase_center_app_ra = app_ra
uv5.phase_center_app_dec = app_dec
uv5.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uv6 = UVData()
uv6.read("node4/"+base+"_0.uvh5", fix_old_proj=False)
uv6.phase_center_ra = ra
uv6.phase_center_dec = dec
uv6.uvw_array = uvw
uv6.phase_center_app_ra = app_ra
uv6.phase_center_app_dec = app_dec
uv6.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uv7 = UVData()
uv7.read("node4/"+base+"_1.uvh5", fix_old_proj=False)
uv7.phase_center_ra = ra
uv7.phase_center_dec = dec
uv7.uvw_array = uvw
uv7.phase_center_app_ra = app_ra
uv7.phase_center_app_dec = app_dec
uv7.phase_center_frame_pa = f_pa
print(uv2.phase_center_app_ra)

uvd =  uv1 + uv2 + uv3 + uv4 + uv5 + uv6 + uv7

print("Writing ms file")
uvd.write_ms(base+"_b.ms")
uvd.write_uvh5(base+"_b.uvh5")
