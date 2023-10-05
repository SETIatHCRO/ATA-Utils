## Joe Bright
## 15/07/2022
## initial scripts for 1gc calibration of ATA data
## using just a flux cal

## modules
import sys
import os
import numpy as np

## users change this

bpcal = '3c286'
pcal = '1733-130'
target = 'SWIFT_J1727'

myrefant = '40'

myvis = 'J1727.ms'

dosteps = ['fluxscale',
           'init_gcal',
           'init_kcal',
           'init_bcal',
           'final_gcal',
           'fluxtable',
           'applycal',
           'flag_split',
           'image_primary',
           'image_secondary',
           'image_target']

## initial flagging
## will want to do a better job here at some stage but make a start using casa tfcrop/rflag
if 'init_flag' in dosteps:
    flagdata(vis=myvis, autocorr=True)

    # flag bpcal
    flagdata(vis=myvis, field=bpcal, mode='tfcrop', datacolumn='DATA')
    flagdata(vis=myvis, field=bpcal, mode='rflag', datacolumn='DATA')

    # flag target
    flagdata(vis=myvis, field=target, mode='tfcrop', datacolumn='DATA')
    flagdata(vis=myvis, field=target, mode='rflag', datacolumn='DATA')

    # flag pcal
    flagdata(vis=myvis, field=pcal, mode='tfcrop', datacolumn='DATA')
    flagdata(vis=myvis, field=pcal, mode='rflag', datacolumn='DATA')

    #flag first and last 100 channels of each spectral window
    flagdata(vis=myvis, mode='manual', spw='0:0~49,0:1294~1343')

if 'fluxscale' in dosteps:
    # fill the model column with a model of the bandpass calibrator scaled to the correct
    # flux level. CASA should recognise the fields of any standards we might use
    setjy(vis=myvis, field=bpcal, standard='Perley-Butler 2017', usescratch=True)


if 'init_gcal' in dosteps:
    # solve for gain variations over time before solving for the bandpass to avoid de-correlation
    gaincal(vis=myvis, caltable=bpcal+'.G0', field=bpcal, refant=myrefant, calmode='p', solint='inf')

if 'init_kcal' in dosteps:
    gaincal(vis=myvis, caltable=bpcal+'.K0', field=bpcal, refant=myrefant, gaintype='K', solint='inf', combine='scan', gaintable=[bpcal+'.G0'])

if 'init_bcal' in dosteps:
    bandpass(vis=myvis, caltable=bpcal+'.B0', field=bpcal, refant=myrefant, combine='scan', solint='inf', bandtype='B', gaintable=[bpcal+'.K0', bpcal+'.G0'])

if 'final_gcal' in dosteps:
    gaincal(vis=myvis, caltable=bpcal+'.G1', field=bpcal, refant=myrefant, solint='inf', calmode='ap', gaintable=[bpcal+'.K0', bpcal+'.B0', bpcal+'.G0'])
    gaincal(vis=myvis, caltable=bpcal+'.G1', field=pcal, refant=myrefant, solint='inf', calmode='ap', gaintable=[bpcal+'.K0', bpcal+'.B0', bpcal+'.G0'], append=True)

if 'fluxtable' in dosteps:
    fluxscale(vis=myvis, caltable=bpcal+'.G1', fluxtable=bpcal+'.fluxscale', reference=bpcal, transfer=[pcal])

if 'applycal' in dosteps:
    applycal(vis=myvis, field=bpcal, gaintable=[bpcal+'.fluxscale', bpcal+'.K0', bpcal+'.B0', bpcal+'.G0'], gainfield=[bpcal,'',''], interp=['nearest','',''], calwt=False)
    applycal(vis=myvis, field=pcal, gaintable=[bpcal+'.fluxscale', bpcal+'.K0', bpcal+'.B0', bpcal+'.G0'], gainfield=[pcal,'',''], interp=['nearest','',''], calwt=False)
    applycal(vis=myvis, field=target, gaintable=[bpcal+'.fluxscale', bpcal+'.K0', bpcal+'.B0', bpcal+'.G0'], gainfield=[pcal,'',''], interp=['linear','',''], calwt=False)

if 'flag_split' in dosteps:
    flagdata(vis=myvis, mode='tfcrop', datacolumn='corrected')
    flagdata(vis=myvis, mode='rflag', datacolumn='corrected')
    mstransform(vis=myvis, outputvis=bpcal+'_noauto_1GC.ms', antenna='!*&&&', field=bpcal, datacolumn='corrected')
    mstransform(vis=myvis, outputvis=pcal+'_noauto_1GC.ms', antenna='!*&&&', field=pcal, datacolumn='corrected')
    mstransform(vis=myvis, outputvis=target+'_noauto_1GC.ms', antenna='!*&&&', field=target, datacolumn='corrected')

if 'image_primary' in dosteps:
    image_vis = bpcal + '_noauto_1GC.ms'
    os.makedirs('./IMAGES/' + bpcal + '/')

    tb.open(image_vis)
    B_max = np.max(np.sqrt(tb.getcol('UVW')[0]**2 + tb.getcol('UVW')[1]**2 + tb.getcol('UVW')[2]**2))
    tb.close()
    tb.open(image_vis + '/SPECTRAL_WINDOW/')
    nu_max = np.max(tb.getcol('REF_FREQUENCY'))
    tb.close()

    mycell = ((3.e8 / nu_max) / B_max) * (180. / np.pi) * 3600. / 8.
    myimagenamebase = 'IMAGES/' + bpcal + '/' + bpcal + 'briggs0_' + str(round(mycell, 2)) + 'arcsec'

    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase + '_dirty', cell=str(mycell) + 'arcsec', imsize=[2048,2048], pblimit=-1, deconvolver='mtmfs')
    dirty_rms = imstat(myimagenamebase + '_dirty.image.tt0')['rms'][0]
    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase + '_clean_iter1', cell=str(mycell) + 'arcsec', imsize=[2048,2048], niter=1000, threshold = str(dirty_rms*5.) + 'Jy', pblimit=-1, deconvolver='mtmfs')
    clean_rms = imstat(myimagenamebase + '_clean_iter1.residual.tt0')['rms'][0]
    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase+'_clean_iter2', cell=str(mycell) + 'arcsec', imsize=[2048,2048], niter=1000, threshold = str(clean_rms*5.) + 'Jy', pblimit=-1,deconvolver='mtmfs')

    ia.open(myimagenamebase+'_clean_iter2.image.tt0')
    maj = ia.restoringbeam()['major']['value']
    min = ia.restoringbeam()['minor']['value']
    pos = ia.restoringbeam()['positionangle']['value']
    ia.close()

    fname = './IMAGES/' + bpcal + '/' + 'fitting_region.crtf'
    f = open(fname, 'w')
    f.write('#CRTF\n')
    f.write('circle[[1024pix, 1024pix],' + str(mycell * 8. * 5.) + 'arcsec]')
    f.close()

    fname2 = './IMAGES/' + bpcal + '/' + 'estimates.txt'
    f = open(fname2, 'w')
    f.write('1,1024,1024,' + str(maj) + 'arcsec,' + str(min) + 'arcsec,' + str(pos) + 'deg,abp')
    f.close()

    fit_results = imfit(imagename=myimagenamebase+'_clean_iter2.image.tt0', region=fname, estimates=fname2)
    flux_density = fit_results['deconvolved']['component0']['flux']['value'][0]
    error = fit_results['deconvolved']['component0']['flux']['error'][0]

    fname = './IMAGES/' + bpcal + '/' + 'fitting_results.txt'
    f = open(fname, 'w')
    f.write(str(flux_density) + ',' + str(error))
    f.close()

if 'image_secondary' in dosteps:
    image_vis = pcal + '_noauto_1GC.ms'
    os.makedirs('./IMAGES/' + pcal + '/')

    tb.open(image_vis)
    B_max = np.max(np.sqrt(tb.getcol('UVW')[0]**2 + tb.getcol('UVW')[1]**2 + tb.getcol('UVW')[2]**2))
    tb.close()
    tb.open(image_vis + '/SPECTRAL_WINDOW/')
    nu_max = np.max(tb.getcol('REF_FREQUENCY'))
    tb.close()

    mycell = ((3.e8 / nu_max) / B_max) * (180. / np.pi) * 3600. / 8.
    myimagenamebase = 'IMAGES/' + pcal + '/' + pcal + '_briggs0_' + str(round(mycell, 2)) + 'arcsec'

    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase + '_dirty', cell=str(mycell) + 'arcsec', imsize=[2048,2048], pblimit=-1, deconvolver='mtmfs')
    dirty_rms = imstat(myimagenamebase + '_dirty.image.tt0')['rms'][0]
    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase + '_clean_iter1', cell=str(mycell) + 'arcsec', imsize=[2048,2048], niter=1000, threshold = str(dirty_rms*5.) + 'Jy', pblimit=-1, deconvolver='mtmfs')
    clean_rms = imstat(myimagenamebase + '_clean_iter1.residual.tt0')['rms'][0]
    tclean(vis=image_vis, weighting='briggs', robust=0, imagename=myimagenamebase+'_clean_iter2', cell=str(mycell) + 'arcsec', imsize=[2048,2048], niter=1000, threshold = str(clean_rms*5.) + 'Jy', pblimit=-1, deconvolver='mtmfs')

    ia.open(myimagenamebase+'_clean_iter2.image.tt0')
    maj = ia.restoringbeam()['major']['value']
    min = ia.restoringbeam()['minor']['value']
    pos = ia.restoringbeam()['positionangle']['value']
    ia.close()

    fname = './IMAGES/' + pcal + '/' + 'fitting_region.crtf'
    f = open(fname, 'w')
    f.write('#CRTF\n')
    f.write('circle[[1024pix, 1024pix],' + str(mycell * 8. * 5.) + 'arcsec]')
    f.close()

    fname2 = './IMAGES/' + pcal + '/' + 'estimates.txt'
    f = open(fname2, 'w')
    f.write('1,1024,1024,' + str(maj) + 'arcsec,' + str(min) + 'arcsec,' + str(pos) + 'deg,abp')
    f.close()

    fit_results = imfit(imagename=myimagenamebase+'_clean_iter2.image.tt0', region=fname, estimates=fname2)
    flux_density = fit_results['deconvolved']['component0']['flux']['value'][0]
    error = fit_results['deconvolved']['component0']['flux']['error'][0]

    fname = './IMAGES/' + pcal + '/' + 'fitting_results.txt'
    f = open(fname, 'w')
    f.write(str(flux_density) + ',' + str(error))
    f.close()

if 'image_target' in dosteps:
    image_vis = target + '_noauto_1GC.ms'
    os.makedirs('./IMAGES/' + target + '/')

    tb.open(image_vis)
    B_max = np.max(np.sqrt(tb.getcol('UVW')[0]**2 + tb.getcol('UVW')[1]**2 + tb.getcol('UVW')[2]**2))
    tb.close()
    tb.open(image_vis + '/SPECTRAL_WINDOW/')
    nu_max = np.max(tb.getcol('REF_FREQUENCY'))
    tb.close()

    mycell = ((3.e8 / nu_max) / B_max) * (180. / np.pi) * 3600. / 8.
    myimagenamebase = 'IMAGES/' + target + '/' + target + '_briggs0_' + str(round(mycell, 2)) + 'arcsec'

    tclean(vis=image_vis, weighting='briggs', robust=0.5, imagename=myimagenamebase + '_dirty', cell=str(mycell) + 'arcsec', imsize=[2048,2048], pblimit=-1, deconvolver='mtmfs')

    ia.open(myimagenamebase+'_dirty.image.tt0')
    maj = ia.restoringbeam()['major']['value']
    min = ia.restoringbeam()['minor']['value']
    pos = ia.restoringbeam()['positionangle']['value']
    ia.close()

    fname2 = './IMAGES/' + target + '/' + 'estimates.txt'
    f = open(fname2, 'w')
    f.write('1,1024,1024,' + str(maj) + 'arcsec,' + str(min) + 'arcsec,' + str(pos) + 'deg,abp')
    f.close()
