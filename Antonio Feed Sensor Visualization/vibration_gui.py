import tkinter as tk
import tkcalendar as tkc
from fun_gui import vibration,cryopower,cryotemp,cryoplot,temp_distribution,vibrationxyz
from datetime import datetime,date
from tkinter import filedialog

# ['1c','1e','1g','1h','1k','2a','2b','2c','2h','2j','2k','2l','2m','3d','3l','4e','4j','5b']


def time_frame():

    # selects the timeframe selevted in the calendars
    startdate = calstart.get_date()
    try:
        startdate = datetime.strptime(startdate, '%d.%m.%y')
    except:
        startdate = datetime.strptime(startdate, '%m/%d/%y')
    enddate = calend.get_date()
    try:
        enddate = datetime.strptime(enddate, '%d.%m.%y')
    except:
        enddate = datetime.strptime(enddate, '%m/%d/%y')
    
    return startdate,enddate


# methods of the analysis buttons they first get the timeframe in the calender then the slected antennas see if the plots should be saved or shown and then run the method from fun_gui
def run_vibration():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    vibration(time[0],time[1],ants,saveflg,showflg,plotpath)

def run_vibrationxyz():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    vibrationxyz(time[0],time[1],ants,saveflg,showflg,plotpath)

def run_cryopower():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    cryopower(time[0],time[1],ants,saveflg,showflg,plotpath)

def run_cryotemp():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    cryotemp(time[0],time[1],ants,saveflg,showflg,plotpath)

def run_cryoplot():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    cryoplot(time[0],time[1],ants,saveflg,showflg,plotpath)

def run_tempdist():
    time = time_frame()
    ants = update_ants()
    saveflg = saveflag.get()
    showflg = showflag.get()
    temp_distribution(time[0],time[1],ants,saveflg,showflg,plotpath)

def update_ants():

    # selevts the right antennas for the plots
    ants = []

    if var1a.get() == 1:
        ants.append('1a')

    if var1b.get() == 1:
        ants.append('1b')

    if var1c.get() == 1:
        ants.append('1c')

    if var1d.get() == 1:
        ants.append('1d')
        
    if var1e.get() == 1:
        ants.append('1e')

    if var1f.get() == 1:
        ants.append('1f')

    if var1g.get() == 1:
        ants.append('1g')

    if var1h.get() == 1:
        ants.append('1h')

    if var1j.get() == 1:
        ants.append('1j')

    if var1k.get() == 1:
        ants.append('1k')

    if var2a.get() == 1:
        ants.append('2a')

    if var2b.get() == 1:
        ants.append('2b')

    if var2c.get() == 1:
        ants.append('2c')

    if var2d.get() == 1:
        ants.append('2d')

    if var2e.get() == 1:
        ants.append('2e')

    if var2f.get() == 1:
        ants.append('2f')
        
    if var2g.get() == 1:
        ants.append('2g')

    if var2h.get() == 1:
        ants.append('2h')

    if var2j.get() == 1:
        ants.append('2j')

    if var2k.get() == 1:
        ants.append('2k')

    if var2l.get() == 1:
        ants.append('2l')

    if var2m.get() == 1:
        ants.append('2m')

    if var3a.get() == 1:
        ants.append('3a')

    if var3b.get() == 1:
        ants.append('3b')

    if var3c.get() == 1:
        ants.append('3c')

    if var3d.get() == 1:
        ants.append('3d')

    if var3e.get() == 1:
        ants.append('3e')

    if var3f.get() == 1:
        ants.append('3f')

    if var3g.get() == 1:
        ants.append('3g')

    if var3h.get() == 1:
        ants.append('3h')

    if var3j.get() == 1:
        ants.append('3j')
    
    if var3k.get() == 1:
        ants.append('3k')

    if var3l.get() == 1:
        ants.append('3l')

    if var4a.get() == 1:
        ants.append('4a')

    if var4b.get() == 1:
        ants.append('4b')

    if var4c.get() == 1:
        ants.append('4c')

    if var4d.get() == 1:
        ants.append('4d')

    if var4e.get() == 1:
        ants.append('4e')

    if var4f.get() == 1:
        ants.append('4f')

    if var4g.get() == 1:
        ants.append('4g')

    if var4h.get() == 1:
        ants.append('4h')

    if var4j.get() == 1:
        ants.append('4j')

    if var4k.get() == 1:
        ants.append('4k')

    if var4l.get() == 1:
        ants.append('4l')

    if var5a.get() == 1:
        ants.append('5a')

    if var5b.get() == 1:
        ants.append('5b')

    if var5c.get() == 1:
        ants.append('5c')

    if var5d.get() == 1:
        ants.append('5d')

    if var5e.get() == 1:
        ants.append('5e')

    if var5f.get() == 1:
        ants.append('5f')

    if var5g.get() == 1:
        ants.append('5g')

    if var5h.get() == 1:
        ants.append('5h')

    if var5j.get() == 1:
        ants.append('5j')

    if var5k.get() == 1:
        ants.append('5k')

    return ants

# default plotpath is the current python working directory
plotpath = ''

def get_directory():
    # selects a path all the plots get saved to
    global plotpath
    plotpath = filedialog.askdirectory(initialdir='/', title='Select directory for plots')+'/'
    


# creates the tkinter window
root = tk.Tk()
root.title('Data Analysis')
root.geometry('750x500')

mindate = date(2022,3,10) # here the data in the sql database begins
maxdate = date.today() 
# for the calenders to select start and enddate
calstart = tkc.Calendar(root,selectmode = "day",mindate = mindate, maxdate = maxdate)
calend = tkc.Calendar(root,selectmode = "day",mindate = mindate,maxdate = maxdate )

startLabel = tk.Label(root,text = "Start date: ")
startLabel.grid(row = 0, column = 0)
calstart.grid(row = 1, column = 0,rowspan = 8,padx=10, pady=10)
endLabel = tk.Label(root,text = "End date: ")
endLabel.grid(row = 0, column = 1)
calend.grid(row = 1, column = 1,rowspan = 8,padx=10, pady=10)


# Checkbox variables of the antenna buttons 1 if checked 0 if unchecked
var1a = tk.IntVar()
var1b = tk.IntVar()
var1c = tk.IntVar()
var1d = tk.IntVar()
var1e = tk.IntVar()
var1f = tk.IntVar()
var1g = tk.IntVar()
var1h = tk.IntVar()
var1j = tk.IntVar()
var1k = tk.IntVar()

var2a = tk.IntVar()
var2b = tk.IntVar()
var2c = tk.IntVar()
var2d = tk.IntVar()
var2e = tk.IntVar()
var2f = tk.IntVar()
var2g = tk.IntVar()
var2h = tk.IntVar()
var2j = tk.IntVar()
var2k = tk.IntVar()
var2l = tk.IntVar()
var2m = tk.IntVar()

var3a = tk.IntVar()
var3b = tk.IntVar()
var3c = tk.IntVar()
var3d = tk.IntVar()
var3e = tk.IntVar()
var3f = tk.IntVar()
var3g = tk.IntVar()
var3h = tk.IntVar()
var3j = tk.IntVar()
var3k = tk.IntVar()
var3l = tk.IntVar()

var4a = tk.IntVar()
var4b = tk.IntVar()
var4c = tk.IntVar()
var4d = tk.IntVar()
var4e = tk.IntVar()
var4f = tk.IntVar()
var4g = tk.IntVar()
var4h = tk.IntVar()
var4j = tk.IntVar()
var4k = tk.IntVar()
var4l = tk.IntVar()

var5a = tk.IntVar()
var5b = tk.IntVar()
var5c = tk.IntVar()
var5d = tk.IntVar()
var5e = tk.IntVar()
var5f = tk.IntVar()
var5g = tk.IntVar()
var5h = tk.IntVar()
var5j = tk.IntVar()
var5k = tk.IntVar()

# checkbox variables for the save and show checkbox
saveflag = tk.IntVar()
showflag = tk.IntVar()

# checkboxes for the antennas to activate a new antenna just remove the state argument
c1a = tk.Checkbutton(root, text='1a',variable=var1a, state = tk.DISABLED)
c1a.grid(row=0, column=4)
c1b = tk.Checkbutton(root, text='1b',variable=var1b, state = tk.DISABLED)
c1b.grid(row=1, column=4)
c1c = tk.Checkbutton(root, text='1c',variable=var1c)
c1c.grid(row=2, column=4)
c1d = tk.Checkbutton(root, text='1d',variable=var1d, state = tk.DISABLED)
c1d.grid(row=3, column=4)
c1e = tk.Checkbutton(root, text='1e',variable=var1e)
c1e.grid(row=4, column=4)
c1f = tk.Checkbutton(root, text='1f',variable=var1f, state = tk.DISABLED)
c1f.grid(row=5, column=4)
c1g = tk.Checkbutton(root, text='1g',variable=var1g)
c1g.grid(row=6, column=4)
c1h = tk.Checkbutton(root, text='1h',variable=var1h)
c1h.grid(row=7, column=4)
c1j = tk.Checkbutton(root, text='1j',variable=var1j, state = tk.DISABLED)
c1j.grid(row=8, column=4)
c1k = tk.Checkbutton(root, text='1k',variable=var1k)
c1k.grid(row=9, column=4)

c2a = tk.Checkbutton(root, text='2a',variable=var2a)
c2a.grid(row=0, column=5)
c2b = tk.Checkbutton(root, text='2b',variable=var2b)
c2b.grid(row=1, column=5)
c2c = tk.Checkbutton(root, text='2c',variable=var2c)
c2c.grid(row=2, column=5)
c2d = tk.Checkbutton(root, text='2d',variable=var2d, state = tk.DISABLED)
c2d.grid(row=3, column=5)
c2e = tk.Checkbutton(root, text='2e',variable=var2e, state = tk.DISABLED)
c2e.grid(row=4, column=5)
c2f = tk.Checkbutton(root, text='2f',variable=var2f, state = tk.DISABLED)
c2f.grid(row=5, column=5)
c2g = tk.Checkbutton(root, text='2g',variable=var2g, state = tk.DISABLED)
c2g.grid(row=6, column=5)
c2h = tk.Checkbutton(root, text='2h',variable=var2h)
c2h.grid(row=7, column=5)
c2j = tk.Checkbutton(root, text='2j',variable=var2j)
c2j.grid(row=8, column=5)
c2k = tk.Checkbutton(root, text='2k',variable=var2k)
c2k.grid(row=9, column=5)
c2l = tk.Checkbutton(root, text='2l',variable=var2l)
c2l.grid(row=10, column=5)
c2m = tk.Checkbutton(root, text='2m',variable=var2m)
c2m.grid(row=11, column=5)

c3a = tk.Checkbutton(root, text='3a',variable=var3a, state = tk.DISABLED)
c3a.grid(row=0, column=6)
c3b = tk.Checkbutton(root, text='3b',variable=var3b, state = tk.DISABLED)
c3b.grid(row=1, column=6)
c3c = tk.Checkbutton(root, text='3c',variable=var3c, state = tk.DISABLED)
c3c.grid(row=2, column=6)
c3d = tk.Checkbutton(root, text='3d',variable=var3d)
c3d.grid(row=3, column=6)
c3e = tk.Checkbutton(root, text='3e',variable=var3e, state = tk.DISABLED)
c3e.grid(row=4, column=6)
c3f = tk.Checkbutton(root, text='3f',variable=var3f, state = tk.DISABLED)
c3f.grid(row=5, column=6)
c3g = tk.Checkbutton(root, text='3g',variable=var3g, state = tk.DISABLED)
c3g.grid(row=6, column=6)
c3h = tk.Checkbutton(root, text='3h',variable=var3h, state = tk.DISABLED)
c3h.grid(row=7, column=6)
c3j = tk.Checkbutton(root, text='3j',variable=var3j, state = tk.DISABLED)
c3j.grid(row=8, column=6)
c3k = tk.Checkbutton(root, text='3k',variable=var3k, state = tk.DISABLED)
c3k.grid(row=9, column=6)
c3l = tk.Checkbutton(root, text='3l',variable=var3l)
c3l.grid(row=10, column=6)

c4a = tk.Checkbutton(root, text='4a',variable=var4a, state = tk.DISABLED)
c4a.grid(row=0, column=7)
c4b = tk.Checkbutton(root, text='4b',variable=var4b, state = tk.DISABLED)
c4b.grid(row=1, column=7)
c4c = tk.Checkbutton(root, text='4c',variable=var4c, state = tk.DISABLED)
c4c.grid(row=2, column=7)
c4d = tk.Checkbutton(root, text='4d',variable=var4d, state = tk.DISABLED)
c4d.grid(row=3, column=7)
c4e = tk.Checkbutton(root, text='4e',variable=var4e)
c4e.grid(row=4, column=7)
c4f = tk.Checkbutton(root, text='4f',variable=var4f, state = tk.DISABLED)
c4f.grid(row=5, column=7)
c4g = tk.Checkbutton(root, text='4g',variable=var4g, state = tk.DISABLED)
c4g.grid(row=6, column=7)
c4h = tk.Checkbutton(root, text='4h',variable=var4h, state = tk.DISABLED)
c4h.grid(row=7, column=7)
c4j = tk.Checkbutton(root, text='4j',variable=var4j)
c4j.grid(row=8, column=7)
c4k = tk.Checkbutton(root, text='4k',variable=var4k, state = tk.DISABLED)
c4k.grid(row=9, column=7)
c4l = tk.Checkbutton(root, text='4l',variable=var4l, state = tk.DISABLED)
c4l.grid(row=10, column=7)

c5a = tk.Checkbutton(root, text='5a',variable=var5a, state = tk.DISABLED)
c5a.grid(row=0, column=8)
c5b = tk.Checkbutton(root, text='5b',variable=var5b)
c5b.grid(row=1, column=8)
c5c = tk.Checkbutton(root, text='5c',variable=var5c, state = tk.DISABLED)
c5c.grid(row=2, column=8)
c5d = tk.Checkbutton(root, text='5d',variable=var5d, state = tk.DISABLED)
c5d.grid(row=3, column=8)
c5e = tk.Checkbutton(root, text='5e',variable=var5e, state = tk.DISABLED)
c5e.grid(row=4, column=8)
c5f = tk.Checkbutton(root, text='5f',variable=var5f, state = tk.DISABLED)
c5f.grid(row=5, column=8)
c5g = tk.Checkbutton(root, text='5g',variable=var5g, state = tk.DISABLED)
c5g.grid(row=6, column=8)
c5h = tk.Checkbutton(root, text='5h',variable=var5h, state = tk.DISABLED)
c5h.grid(row=7, column=8)
c5j = tk.Checkbutton(root, text='5j',variable=var5j, state = tk.DISABLED)
c5j.grid(row=8, column=8)
c5k = tk.Checkbutton(root, text='5k',variable=var5k, state = tk.DISABLED)
c5k.grid(row=9, column=8)



# buttons for the functions of the program

button1 = tk.Button(root,text = 'Vibration/Cryopower',command = run_vibration)
button1.grid(row = 9, column = 0)

button2 = tk.Button(root, text = 'Cryopower distribution',command = run_cryopower)
button2.grid(row = 11, column = 0)

button3 = tk.Button(root, text = 'Cryopower/Temperature', command = run_cryotemp)
button3.grid(row = 12, column = 0)

button4 = tk.Button(root, text = 'Cryopower and Vibration', command = run_cryoplot)
button4.grid(row = 13, column = 0)

button5 = tk.Button(root,text = 'Temperature distribution', command = run_tempdist)
button5.grid(row = 14, column = 0)

button6 = tk.Button(root,text = 'Select directory for plots',command = get_directory)
button6.grid(row = 9, column = 1)

button7 = tk.Button(root,text = 'Vibration_x_y_z/Cryopower',command = run_vibrationxyz)
button7.grid(row = 10, column = 0)

savecheck = tk.Checkbutton(root, text = 'Save plots',variable = saveflag)
savecheck.grid(row = 10, column = 1)

showcheck = tk.Checkbutton(root, text = 'Show plots', variable = showflag)
showcheck.grid(row = 11, column = 1)
showcheck.select()

root.mainloop()

