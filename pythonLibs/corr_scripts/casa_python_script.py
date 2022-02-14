import sys
import os
import shutil


base = sys.argv[1]
filen = sys.argv[2]

#flagdata(vis=base+'_b.ms', spw="0:225~250;260~285;850~900;1170~1180")

applycal(base+"_b.ms", gaintable='/home/sonata/corr_data/uvh5_multi_new/uvh5_59618_51600_32857299_3c273_0001/cal.b.BP', calwt=False)

split(base+"_b.ms", outputvis=base+"_bbp.ms", datacolumn='corrected')

#gain K for refant 1c
gaincal(base+"_bbp.ms", caltable=filen+"/cal_1c.b.K", refant="3", gaintype="K")

#gain K for refant 2a
gaincal(base+"_bbp.ms", caltable=filen+"/cal_2a.b.K", refant="11", gaintype="K")

plotms(vis=base+'_bbp.ms', xaxis='frequency', yaxis='phase', antenna='!*&&&', correlation='xx,yy', 
        avgtime='1200', iteraxis='baseline', gridrows=5, gridcols=4, coloraxis='corr', titlefont=12, 
        xaxisfont=11, yaxisfont=11, plotfile=str(base)+'.png', highres=True, width=1500, height=1200, showgui=False)

shutil.rmtree(base+"_bbp.ms")


#applycal(base+"_b.ms", gaintable=filen+'/cal.b.K', calwt=False)
#split(base+"_b.ms", outputvis=base+"_k.ms", datacolumn='corrected')
