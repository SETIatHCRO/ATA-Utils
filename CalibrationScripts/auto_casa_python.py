import sys
import os
import shutil


base = sys.argv[1]
#filen = sys.argv[2]
lo = sys.argv[2]

#LOB
print("Starting LO"+str(lo))

plotms(vis=base+'_'+str(lo)+'.ms', xaxis='frequency', yaxis='phase', antenna='!*&&&', correlation='xx,yy', 
        avgtime='1200', iteraxis='baseline', gridrows=5, gridcols=4, coloraxis='corr', titlefont=12, 
        xaxisfont=11, yaxisfont=11, plotfile=base+'_'+str(lo)+'.png', highres=True, width=1500, height=1200, plotrange=[0, 0, -180, 180], showgui=False)


#gain K for refant 1c
gaincal(base+'_'+str(lo)+'.ms', caltable="cal."+str(lo)+".K", refant="3", gaintype="K")
applycal(base+'_'+str(lo)+'.ms', gaintable="cal."+str(lo)+".K", calwt=False)
split(base+'_'+str(lo)+'.ms', outputvis=base+'_'+str(lo)+'k.ms', datacolumn='corrected')

#gain G for refant 1c
gaincal(base+'_'+str(lo)+'k.ms', caltable="cal."+str(lo)+".G", refant="3", gaintype="G")
applycal(base+'_'+str(lo)+'k.ms', gaintable="cal."+str(lo)+".G", calwt=False)
split(base+'_'+str(lo)+'k.ms', outputvis=base+'_'+str(lo)+'kg.ms', datacolumn='corrected')

#gain BP for refant 1c
bandpass(base+'_'+str(lo)+'kg.ms', caltable="cal."+str(lo)+".BP", refant="3", bandtype="B", minblperant=6)
applycal(base+'_'+str(lo)+'kg.ms', gaintable="cal."+str(lo)+".BP", calwt=False)
split(base+'_'+str(lo)+'kg.ms', outputvis=base+'_'+str(lo)+'kgbp.ms', datacolumn='corrected')

plotms(vis=base+'_'+str(lo)+'kgbp.ms', xaxis='frequency', yaxis='phase', antenna='!*&&&', correlation='xx,yy', 
        avgtime='1200', iteraxis='baseline', gridrows=5, gridcols=4, coloraxis='corr', titlefont=12, 
        xaxisfont=11, yaxisfont=11, plotfile=base+'_'+str(lo)+'kgbp.png', highres=True, width=1500, height=1200, plotrange=[0, 0, -180, 180], showgui=False)


#shutil.rmtree(base+'_'+str(lo)+'k.ms')
#shutil.rmtree(base+'_'+str(lo)+'kg.ms')
#shutil.rmtree(base+'_'+str(lo)+'kgbp.ms')



print("CASA work complete")
