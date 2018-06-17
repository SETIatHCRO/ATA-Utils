#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'
load 'ants.rb'
load 'offsetobs.rb'

#
# Perform a system command and print the result to stdout.
#
def doCmd(cmd)
  puts cmd;
  puts `#{cmd}`;
end

#
# Point the beamformer
#
def pointBF(bfNum, freq)
  cmd = "bftrackephem.rb --beamselect " + bfNum.to_s +  " --beamephem x1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_x1.ephem,y1,/home/kilsdonk/ata-svn/ata/src/ata/backend/bf" + bfNum.to_s +  "_y1.ephem --bcclear --bctype beamDefaultPhased --freq " + freq.to_s + " --duration 20000 --sideband off --spk --calbw 0.6 --noatalo --quickload --offsetaz #{$azoffset} --offsetel #{$eloffset}"
  puts cmd;
  doCmd(cmd);
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
  doCmd(cmd);

end

#
# Tell the antennas to track an object
#
def track(calName)
  cmd = "atatrackephem \"" + $antList + " " + calName + ".ephem -w\"";
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


def printHelp
  puts "Syntax: repoint <target1> <target2> <target3> <bf1 freq MHz> <bf2/3 freq MHz> <azoffset> <eloffset>";
  exit(1);
end

if(ARGV.length != 7) then printHelp(); end

#point the antennas, then the beam
createEphem(ARGV[0], 1, true);
createEphem(ARGV[1], 2, true);
createEphem(ARGV[2], 3, true);
#puts "NOT TRACKING! COMMENT BACK IN!!\n\n\n";
track(ARGV[1]);

puts "waiting for rise...";
waitTillRise(ARGV[0] + ".ephem");
puts "#{ARGV[0]} has risen!";
puts "Now starting BF pointing";

$azoffset = ARGV[5];
$eloffset = ARGV[6];


t1 = Thread.new{pointBF(1, ARGV[3])};
t2 = Thread.new{pointBF(2, ARGV[4])};
#t3 = Thread.new{pointBF(3, ARGV[4])};
t1.join;
t2.join;
#t3.join;

