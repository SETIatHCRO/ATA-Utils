from pyuvdata import UVData
import sys

uv = UVData()
print(sys.argv[1:])
uv.read(sys.argv[1], fix_old_proj=False)

uvd = uv

for uvname in sys.argv[2:]:
    print(uvname)
    uv = UVData()
    uv.read(uvname, fix_old_proj=False)
    uvd.fast_concat(uv, axis='blt', inplace=True)

print("Writing ms file")
uvd.write_ms("time_concated.ms")
uvd.write_uvh5("time_concated.uvh5")
