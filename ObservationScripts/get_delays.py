from casatools import table
import numpy as np

calK = table()
#calK.open("cal.b.K")
calK.open("test_cal")
delays   = np.squeeze(calK.getcol("FPARAM"))
antnames = calK.getcol("ANTENNA1")

tb = np.column_stack((antnames, *delays))

np.savetxt("./delays_residuals.txt", tb, fmt="%i %.6f %.6f", header="antnum X Y")
