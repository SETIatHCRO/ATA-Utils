import control

h = control.control()

h.open()

h.reset_device()

print h.send_query('*IDN?')
