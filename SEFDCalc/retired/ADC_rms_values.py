

import pickle
import glob
import numpy as np


def giveme_rms_value(filename):
    '''
    '''

#    test1 = pickle.load(open('1529651156_rf2000.00_n180_3C295_on_ant_3d_2000.00.pkl','r'))
#     test1['auto0_of_count']
#     test1['adc0_stats']
#     test1['adc0_stats']
#     {'dev': 7.708337778983681, 'mean': 0.509130859375}
#     test1['adc0_stats']['dev']
#     7.708337778983681

    blah1 = pickle.load(open(filename,'r'))

    return blah1['adc0_stats']['dev']




#---------------------------------------------------------
#---------------------------------------------------------



band = 3000



#Finding filesimp
filelist_on= glob.glob('*on*'+str(band)+'*.00.pkl')
filelist_off= glob.glob('*off*'+str(band)+'*.00.pkl')

filelist= glob.glob('*'+str(band)+'*.00.pkl')



good_RMS = []
bad_RMS = []


verbose =1
#
for filename in filelist:

    ADC_rms = giveme_rms_value(filename)

    if ADC_rms > 5. and ADC_rms < 20.:
        good_RMS.append(filename)
        if verbose:
            print '%s RMS value is %s' % (filename,ADC_rms)
    else:
        bad_RMS.append(filename)
        if verbose:
            print 'The RMS value is %s' % ADC_rms



def for_notes():
    test_ON= pickle.load(open('1529662696_rf3000.00_n180_3C295_on_ant_4j_3000.00.pkl','r'))
    test_OFF= pickle.load(open('1529668026_rf3000.00_n180_3C295_off_ant_4j_3000.00.pkl','r'))
    #

    # type(test_ON['auto0'][0])
    # test_ON['auto0'][0].shape
    # data_ON = np.array(test_ON['auto0'])
    # data_ON.shape
    # data_ON
    # data_ON[0]
    # data_ON = np.array(test_OFF['auto0'])
    data_ON = np.array(test_ON['auto0'])
    data_OFF = np.array(test_OFF['auto0'])
    # spectra_ON = np.sum(data_ON,axis=1)
    # spectra_ON.shape
    spectra_ON = np.sum(data_ON,axis=0)
    spectra_OFF = np.sum(data_OFF,axis=0)
    # plt.clf()
    # plt.plot(test_ON['frange'],spectra_ON)
    # plt.plot(test_OFF['frange'],spectra_OFF)
    ratio1 = (spectra_ON-spectra_OFF)/spectra_OFF
    plt.figure()
    plt.plot(test_ON['frange'],ratio1)


