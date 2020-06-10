import numpy

azSpeedMax = 2.5 #deg/s
elSpeedMax = 1 #deg/s
pointperdeg = 10


def makeEphem(filename, azlist, ellist, azSpeed = azSpeedMax, elSpeed = elSpeedMax):
    """
    ephem file should be called with atatractephem --now
    """
    if (azSpeed > azSpeedMax):
        raise RuntimeError('az speed greater that max az speed')
    if (elSpeed > elSpeedMax):
        raise RuntimeError('el speed greater that max az speed')
    if(len(azlist) != len(ellist)):
        raise RuntimeError('lenght mismatch')

    nbatches = len(azlist)-1
    if(nbatches < 1):
        raise RuntimeError('not enough points')

    lastTime = 0;

    degAmountAzList = numpy.absolute(numpy.diff(azlist))
    degAmountElList = numpy.absolute(numpy.diff(ellist))

    timeSweepAz = degAmountAzList/azSpeed
    timeSweepEl = degAmountElList/elSpeed

    noPointsAz = degAmountAzList * pointperdeg
    noPointsEl = degAmountElList * pointperdeg

    nOfPointsList = numpy.max([noPointsAz,noPointsEl],axis=0)
    timeSweepList = numpy.max([timeSweepAz,timeSweepEl],axis=0)

    with open(filename,'w') as fd:
        for ii in range(nbatches):
            nOfPoints = nOfPointsList[ii]
            timeSweep = timeSweepList[ii]
            sweepAz = numpy.linspace(azlist[ii],azlist[ii+1],num=nOfPoints+1)
            sweepEl = numpy.linspace(ellist[ii],ellist[ii+1],num=nOfPoints+1)
            sweepTime = numpy.round(numpy.linspace(lastTime,lastTime + timeSweep,num=nOfPoints+1)*1e9)
            lastTime += timeSweep

            for zz in range(nOfPoints):
                fd.write("{0:d} {1:03.5f} {2:02.5f} {3:f}\n".format(int(sweepTime[zz]),sweepAz[zz],sweepEl[zz],0))


