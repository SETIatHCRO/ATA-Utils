from casatools import table
import numpy as np
import sys

base = sys.argv[1]

#1c
calK = table()
calK.open(base+"/cal_1c.b.K")
delays   = np.squeeze(calK.getcol("FPARAM"))
antnames = calK.getcol("ANTENNA1")

tb = np.column_stack((antnames, *delays))

np.savetxt(base+"/delays_residuals_1c.txt", tb, fmt="%i %.6f %.6f", header="antnum X Y")

#2a
calK = table()
calK.open(base+"/cal_2a.b.K")
delays   = np.squeeze(calK.getcol("FPARAM"))
antnames = calK.getcol("ANTENNA1")

tb = np.column_stack((antnames, *delays))

np.savetxt(base+"/delays_residuals_2a.txt", tb, fmt="%i %.6f %.6f", header="antnum X Y")






