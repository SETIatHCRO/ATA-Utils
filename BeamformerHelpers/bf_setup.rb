#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'
require 'thread'

load 'userinfo.rb'
load 'report.rb'
load 'best_cal.rb'

$reportSemaphore = Mutex.new;

$phaseDuration = 600;
$phaseIntegrate = 300;
$phaseNum = 2;
#$phaseDuration = 5000;
#$phaseIntegrate = 4800;
#$phaseNum = 3;

$delayFreq = 1420;
$delayTarget = "casa";
$phaseTarget = "3c84";
$obsFreq1 = 8421.2;
$obsFreq2 = 8421.2;
$obsTarget = Array.new(3);
$obsTarget[0] = "rosetta";
$obsTarget[1] = "rosetta";
$obsTarget[2] = "rosetta";

$reportText = "";

def printHelp()
  puts "Syntax:";
  puts "  #{$PROGRAM_NAME} <delay cal target> <phase target name> <BF1 freq MHz> <BF2/3 freq MHz> <beam1 target name> <beam2 target name> <beam3 target name> <logfile name tag>";
  puts " Example:";
  puts "  #{$PROGRAM_NAME} casa 3c48 1680.0 1680.0 moon moon moon testlog1"; 
end

def usebf(num)
  $bfList.each do |b|
    if(b == num) then return true; end
  end
  return false;
end

#
# Perform a system command and print the result to stdout.
#
def doCmd(cmd)
  puts cmd;
  result = `#{cmd}`;
  return result;
end

#
# Get the list of antenas.
#
def getAntennaList(bfNum, withSpaces)
  
    return $antList;

end

#
# Create an ephemeris
#
def createEphem(calName, bfNum, epehmFileExists)

  if(epehmFileExists == false)
    cmd = "ataephem " + calName;
    doCmd(cmd);
  end
  cmd = "atawrapephem \"" + calName + ".ephem\"";
  doCmd(cmd);
  cmd = "cp " + calName + ".ephem /home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_x1.ephem";
  doCmd(cmd);
  cmd = "cp " + calName + ".ephem /home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_y1.ephem";
puts cmd
  doCmd(cmd);

end

#
# Move antennas into another group.
#
def moveAnts(from, to)
    cmd = "fxconf.rb sagive " + from + " " + to + " " + $antList;
    doCmd(cmd);
   
end

#
# Tell the antennas to track an object
#
def track(calName)
  cmd = "atatrackephem \"" + $antList + " " + calName + ".ephem -w\"";
  doCmd(cmd);
end

#
# Turn on the lnas
#
def lna()
  cmd = "atalnaon \"" + $antList + "\"";
  doCmd(cmd);
end

def pams()
  #cmd = "atasetpams \"" + $antList + " xband\"";
  cmd = "atasetpams \"" + $antList + "\"";
  doCmd(cmd);
end

#
# Set the focus
#
def focus(freq)
  cmd = "atasetfocus \"" + $antList + " " + freq.to_s + "\"";
  doCmd(cmd);
end

#
# Set the LO frequency
#
def setLO(lo, freq)
  cmd = "atasetlo \"" + lo + " " +  (freq.to_f + 15529.145600).to_s + "\"";
  doCmd(cmd);
  cmd = "atasetskyfreq \"" + lo + " " + freq.to_s + "\"";
  doCmd(cmd);
end

#
# Perform a bfreset.
#
def bfReset(bfNum)
  doCmd("sleep 10");

  cmd = "bfibob " + bfNum.to_s + " sky && bfibob " + bfNum.to_s  + " walsh && bfibob " + bfNum.to_s + " rearm";
  $stderr.puts cmd;
  doCmd(cmd);
end

#
# Perform a bf autoatten
#
def bfAttn(bfNum)
  #cmd = "atasetazel \"" +  $antList + " 330.0 30.0 -w \"";
  #doCmd(cmd);
  doCmd("sleep 10");
  cmd = "bfibob " + bfNum.to_s + " autoatten | tee -a atten.log";
  $stderr.puts cmd;
  result = doCmd(cmd);
  $reportSemaphore.synchronize {
	$reportText += result + "\n";
  }
  $stderr.puts "DONE: " + cmd;
end

#
# Perform a bfinit
#
def bfInit(bfNum, ipAddrx, xport, ipAddry, yport, pollist)
  
  cmd = "bfinit.rb --beamselect " + bfNum.to_s + " --ip0 " + ipAddrx + ":" + xport.to_s + " --ip1 " + ipAddry + ":" + yport.to_s + " --ants " + pollist + " --spk";
  puts cmd;
  doCmd(cmd);

  cmd = "bfstufftsys.rb -b " + bfNum.to_s + " -f " + $delayFreq.to_s;
  puts cmd;
  doCmd(cmd);

  cmd = "bfspk.rb -b " + bfNum.to_s + " --ip0 " + ipAddrx + ":" + xport.to_s + " --ip1 " + ipAddry + ":" + yport.to_s;
  puts cmd;
  doCmd(cmd);

end


#
# Perform a del cal with optional --statusonly command line flag.
#
def delayCal(bfNum, statusOnly)
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_y1.ephem --freq #{$delayFreq} --duration 600 --sideband off --caldelay --integrate 30 --num 2 --agcdb 0.0 --bcclear --spk --calbw 0.6 --noatalo";
  if(statusOnly == true)
    cmd = cmd + " --statusonly";
  end
  cmd = cmd + "  | tee -a delaycal.log";
  puts cmd;
  result = doCmd(cmd);
  
  $reportSemaphore.synchronize {
	$reportText += "#{result}\n";
  }
end

#
# perform a phase cal
# 
def phaseCal(bfNum, freq)
  #cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --freq " + freq.to_s + " --duration 600 --sideband off --calphase --integrate 300 --num 2 --gainadjustdb 6 --bcclear --spk --calbw 0.6 --noatalo | tee -a phasecal.log";
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --freq " + freq.to_s + " --duration #{$phaseDuration.to_s} --sideband off --calphase --integrate #{$phaseIntegrate.to_s} --num #{$phaseNum.to_s} --gainadjustdb 6 --bcclear --spk --calbw 0.6 --noatalo | tee -a phasecal.log";
  puts cmd;
  result = doCmd(cmd);
  $reportSemaphore.synchronize {
	$reportText += "#{result}\n";
  }
end

#
# perform a freq cal
# 
def freqCal(bfNum, freq)
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --freq " + freq.to_s + " --duration 400 --sideband off --calfreq --integrate 300 --num 1 --bcclear --spk --calbw 0.6 --noatalo";
  puts cmd;
  doCmd(cmd);
end

#
# Point the beamformer
#
def pointBF(bfNum, freq)
  #cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --bcclear --bctype beamDefaultPhased --freq " + freq.to_s + " --duration 300 --sideband off --timer 5 --spk --calbw 0.6 --noatalo --quickload";
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --bcclear --bctype beamDefaultPhased --freq " + freq.to_s + " --duration 20000 --sideband off --spk --calbw 0.6 --noatalo --quickload --write out --memtimer"
  puts cmd;
  doCmd(cmd);
end

#
# Do a delay cal is an optional --clearalarms command line flag.
#
def delayCalClear(bfNum, statusOnly)
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s + "_y1.ephem --freq #{$delayFreq} --duration 600 --sideband off --caldelay --integrate 30 --num 2 --agcdb 0.0 --bcclear --spk --calbw 0.6 --noatalo ";
  if(statusOnly == true)
    cmd = cmd + " --clearalarms";
  end
  puts cmd;
  doCmd(cmd);
end

def waitTillRise(ephemFileName)

        ephemStart = File.readlines(ephemFileName).first.split(/\s+/)[0][0...10].to_i;
        timeNow = Time.now().to_i;

        puts ephemStart.to_i;
        puts timeNow.to_s;

        ephemStart = ephemStart + 10;

        while (timeNow < (ephemStart)) do

        diff = (ephemStart - timeNow);
                puts diff.to_s + " seconds till rise...";
                sleep(1);
                timeNow = Time.now().to_i;

        end

end

def allFreqCal(centerFreq, offset)
  focus(centerFreq.to_f + offset);
  setLO("b", centerFreq.to_f + offset);
  setLO("c", centerFreq.to_f + offset);
  setLO("d", centerFreq.to_f + offset);
  if(usebf(1)) then t1 = Thread.new{freqCal(1, centerFreq.to_f + offset)}; end
  if(usebf(2)) then t2 = Thread.new{freqCal(2, centerFreq.to_f + offset)}; end
  if(usebf(3)) then t3 = Thread.new{freqCal(3, centerFreq.to_f + offset)}; end
  if(usebf(1)) then t1.join; end
  if(usebf(2)) then t2.join; end
  if(usebf(3)) then t3.join; end
  puts "Finished freqcal at " + (centerFreq.to_f + offset).to_s;
end
  
#
# Park the antennas
#
def park()
  cmd = "atasetazel \"" + $antList + " 180 18\"";
  doCmd(cmd);
end


if(ARGV.length != 8)
  printHelp();
  exit;
end

$delayTarget = ARGV[0];
$phaseTarget = ARGV[1];
$obsFreq1 = ARGV[2].to_f;
$obsFreq2 = ARGV[3].to_f;
$obsTarget = Array.new(3);
$obsTarget[0] = ARGV[4];
$obsTarget[1] = ARGV[5];
$obsTarget[2] = ARGV[6];
$bflogfile = "bf_" + ARGV[7] + ".log";

#$delayFreq = $obsFreq1.to_f;

phaseFlux = 0.0;

# Check to see if the delay calibrator is up
isup = isUp($delayTarget);
if(isup[0] == false)
  puts "Error: the delay cal target #{$delayTarget} is not up, rises " + isup[1] + " local time";
  exit(1);
end


if($phaseTarget.eql?("best"))
  print "Please wait, figuring out best phase cal";
  $stdout.flush
  bestCalInfo = getBestCal($obsFreq1);
  $phaseTarget = bestCalInfo[0];
  phaseFlux = bestCalInfo[1];
  print "\r                                         \r";
else
  phaseFlux = getCalFlux($phaseTarget, $obsFreq1)
end

puts "Check your settings:";

puts " Delay target:   " + $delayTarget + " @ " + $delayFreq.to_s + ", sets " + isup[1] + " local time";
isup = isUp($phaseTarget);
puts " Phase target:   " + $phaseTarget + ", flux=" + phaseFlux.to_s + " Jy, sets " + isup[1] + " local time";
puts " BF1 Obs freq:   " + $obsFreq1.to_s;
puts " BF2/3 Obs freq: " + $obsFreq2.to_s;
puts " BF1 target:     " + $obsTarget[0];
puts " BF2 target:     " + $obsTarget[1];
puts " BF3 target:     " + $obsTarget[2];
puts " Antennas used:  " + $antList;
puts " Beam destinations: ";
puts Address.getDesc($addressList);
puts " Logfile name:   " + $bflogfile;

puts "\nAre these correct? (y or n)";

answer = STDIN.getc();
if(answer.to_s != "121")
  puts "Goodbye! Try again...\n";
  exit;
end


#=begin

########################
# Main program section #
########################

#Create the logfile
# Do not continue if it exists
if(setLogfileName($bflogfile))
	puts "The log file " + $bflogfile + " exists. Choose another tag.\n";
	exit(1);
end
puts "file did not exist";

# Output the date to the logfile
createReport("", REPORT_TYPE_DATETIME);

#=begin

# Output the antenna list to the log file
createReport("", REPORT_TYPE_ANTS);

#Move the ants to the proper group
moveAnts("none", "bfa");

# Init the system
lna();
pams();


# Set the freq for the delaycal
focus($delayFreq.to_f);
setLO("b", $delayFreq.to_f);
setLO("c", $delayFreq.to_f);
setLO("d", $delayFreq.to_f);

# BFreset
if(usebf(1)) then t1 = Thread.new{bfReset(1)}; end
if(usebf(2)) then t2 = Thread.new{bfReset(2)}; end
if(usebf(3)) then t3 = Thread.new{bfReset(3)}; end
if(usebf(1)) then t1.join(); end
if(usebf(2)) then t2.join(); end
if(usebf(3)) then t3.join(); end

# Autoatten
cmd = "atasetazel \"" +  $antList + " 330.0 30.0 -w \"";
doCmd(cmd);
if(usebf(1)) then t1 = Thread.new{bfAttn(1)}; end
if(usebf(2)) then t2 = Thread.new{bfAttn(2)}; end
if(usebf(3)) then t3 = Thread.new{bfAttn(3)}; end
if(usebf(1)) then t1.join(); end
if(usebf(2)) then t2.join(); end
if(usebf(3)) then t3.join(); end
createReport($reportText, REPORT_TYPE_ATTN);
puts "BF autoatten finished";

# BFINIT

if(usebf(1)) 
  ax = Address.get($addressList, 1, "x");
  ay = Address.get($addressList, 1, "y");
  t1 = Thread.new{bfInit(1, ax.ipaddress, ax.port.to_i, ay.ipaddress, ay.port.to_i, $antPolList[a.bfnum.to_i])};
end
if(usebf(2)) 
  ax = Address.get($addressList, 2, "x");
  ay = Address.get($addressList, 2, "y");
  t1 = Thread.new{bfInit(1, ax.ipaddress, ax.port.to_i, ay.ipaddress, ay.port.to_i, $antPolList[a.bfnum.to_i])};
end
if(usebf(3)) 
  ax = Address.get($addressList, 3, "x");
  ay = Address.get($addressList, 3, "y");
  t1 = Thread.new{bfInit(1, ax.ipaddress, ax.port.to_i, ay.ipaddress, ay.port.to_i, $antPolList[a.bfnum.to_i])};
end
if(usebf(1)) then t1.join(); end
if(usebf(2)) then t2.join(); end
if(usebf(3)) then t3.join(); end
puts "BFINIT finished.";

#=begin

#=end

focus($delayFreq.to_f);
setLO("b", $delayFreq.to_f);
setLO("c", $delayFreq.to_f);
setLO("d", $delayFreq.to_f);


# Create the ephem for the delay target, track it and do the delay cal
$reportText ="";
if(usebf(1)) then createEphem($delayTarget, 1, false); end
if(usebf(2)) then createEphem($delayTarget, 2, false); end
if(usebf(3)) then createEphem($delayTarget, 3, false); end
track($delayTarget);

for i in 0..1
if(i == 1) then $reportText =""; end
if(usebf(1)) then t1 = Thread.new{delayCal(1, false)}; end
if(usebf(2)) then t2 = Thread.new{delayCal(2, false)}; end
if(usebf(3)) then t3 = Thread.new{delayCal(3, false)}; end
if(usebf(1)) then t1.join; end
if(usebf(2)) then t2.join; end
if(usebf(3)) then t3.join; end
end
createReport($reportText, REPORT_TYPE_DELAYCAL);
puts "Delay Cal finished";

#=end

#=begin

# Set the freq for the phase cal
focus(4000.0);
# FXA uses LOB, set us just because
setLO("b", $obsFreq1.to_f);
# FXC/BF1 use LOC
setLO("c", $obsFreq1.to_f);
# BF2/3 use LOD
setLO("d", $obsFreq2.to_f);

#puts "Skipping phase cal\n\n";
#=begin

# Create the ephem for the phase cal target, track it and do the phase cal
if(usebf(1)) then createEphem($phaseTarget, 1, false); end
if(usebf(2)) then createEphem($phaseTarget, 2, false); end
if(usebf(3)) then createEphem($phaseTarget, 3, false); end
track($phaseTarget);

$reportText = "";
if(usebf(1)) then t1 = Thread.new{phaseCal(1, $obsFreq1)}; end
if(usebf(2)) then t2 = Thread.new{phaseCal(2, $obsFreq2)}; end
if(usebf(3)) then t3 = Thread.new{phaseCal(3, $obsFreq2)}; end
if(usebf(1)) then t1.join; end
if(usebf(2)) then t2.join; end
if(usebf(3)) then t3.join; end
createReport($reportText, REPORT_TYPE_PHASECAL);
puts "Phase Cal finished";

#=end

puts "\nALERT:!\n";
puts "  If you are doing a correlator obs, now is the time to observe";
puts "    " + $phaseTarget + " at " + $obsFreq1.to_s + "MHz for 3 minutes";
puts "  Press <return> when you are finished with that..."
#STDIN.getc();
#puts "again...";
#STDIN.getc();

=begin
startFreq = 2900.0;
allFreqCal(startFreq, 0);
allFreqCal(startFreq, 1);
allFreqCal(startFreq, 2);
allFreqCal(startFreq, 7);
allFreqCal(startFreq, 17);
allFreqCal(startFreq, 67);
allFreqCal(startFreq, 100);
allFreqCal(startFreq, 150);
allFreqCal(startFreq, 200);
allFreqCal(startFreq, 250);
allFreqCal(startFreq, 300);
allFreqCal(startFreq, 350);
=end

focus($obsFreq1.to_f);
setLO("b", $obsFreq1.to_f);
setLO("c", $obsFreq1.to_f);
setLO("d", $obsFreq2.to_f);

#point the antennas, then the beam
if(usebf(1)) then createEphem($obsTarget[0], 1, true); end
if(usebf(2)) then createEphem($obsTarget[1], 2, true); end
if(usebf(3)) then createEphem($obsTarget[2], 3, true); end
track($obsTarget[0]);

puts "\nALERT:!\n";
puts " FREQ CAL FINISHED\n";
puts "    your center target at " + $obsFreq1.to_s + " and " + $obsFreq2.to_s + " MHz.";

# Focus and tune
focus($obsFreq1.to_f);
setLO("b", $obsFreq1.to_f);
setLO("c", $obsFreq1.to_f);

#waitTillRise($obsTarget[0] + ".ephem");

if(usebf(1)) then t1 = Thread.new{pointBF(1, $obsFreq1)}; end
if(usebf(2)) then t2 = Thread.new{pointBF(2, $obsFreq2)}; end
if(usebf(3)) then t3 = Thread.new{pointBF(3, $obsFreq2)}; end
if(usebf(1)) then t1.join; end
if(usebf(2)) then t2.join; end
if(usebf(3)) then t3.join; end

puts "\nFinished, beams should be pointed at " + $obsTarget[0] + " @ " + $obsFreq1.to_s + " and " + $obsFreq2.to_s + " MHz";
puts "\n";

#moveAnts("bfa", "none");
#park();
