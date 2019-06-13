#! /usr/bin/env ruby
#################################################################
###
###  tpoint_fit.rb
###
###  Automates tpoint 
###
###  Author: Jon Richards
###  Original Date: Sep 12, 2016
###
###
##################################################################
#
require 'rubygems'
require 'json'
require 'date'

$rmsThreshold = 50.0;


def printHelp()
  puts "";
  puts "Syntax: tpoint_fit.rb <pointer data file> [-viewscripts]";
  puts " Filename is like FXPointer_ant1b_x_1b.dat";
  puts " The -viewscripts tells the user how to view the before and after gscat diagrams.";
  puts " Example: tpoint.rb FXPointer_ant1b_x_1b.dat";
  puts ""
  exit(0);
end

if(ARGV.length < 1) then printHelp(); end

def removePnt(point, datFilename, outFilename)

  lines = [];

  readingPoints = false;
  index = 0;
  File.readlines(datFilename).each do |line|

    if(index > 0) then index = index + 1; end

    if(line.include?("!  az_com, el_com, az_meas, el_meas"))
      index = 1;
      lines << line;
    elsif(index-1 != point)
      lines << line;
    end
  end

  File.open(outFilename, "w") do |f|
    f.puts(lines)
  end

end

def countPoints(datFilename)
  startCounting = false;
  count = 0;
  File.readlines(datFilename).each do |line|
    if(line.include?("!  az_com, el_com, az_meas, el_meas"))
      startCounting = true;
    elsif(startCounting == true)
      count += 1;
    end
  end
  return count;
end

def oneFit(datFilename)
  `rm -f tpoint.cmds`
  `rm -f tpoint.clog`
  cmd = "rm -f " + File.basename($origFilename, ".*") + ".fit";
  `#{cmd}`;
  open('tpoint.cmds', 'w') do |f|
    f.puts "indat #{datFilename}";
    f.puts "USE IE IA CA AN AW";
    f.puts "FIT";
    f.puts "FAUTO";
    f.puts "slist"
    f.puts "outmod " + File.basename($origFilename, ".*") + ".fit";
  end

  cmd = "source /hcro/opt/tpoint/tpoint.sh; tpoint tpoint.clog init tpoint.cmds";
  result = `#{cmd}`;
  #puts result;
  #Sky RMS = 175.64
  #Popn SD = 204.61
  #
  #Observation #7 is a very weak outlier candidate.
  startLookingForLine = false;
  rms = "0.0";
  worstObsDR = 0.0;
  worstObsIndex = "-1";
  result.each_line do |line|
    line.strip!;
    if(line.include?("Sky RMS"))
      parts = line.split(/\s+/);
      rms = parts[3];
    elsif(line.include?("Observation #"))
      parts = line.split(/\s+/);
      worstObsIndex = parts[1][1..-1];
    elsif(!worstObsIndex.eql?("-1") && worstObsDR == 0.0)
      parts = line.split(/\s+/);
      if(parts[0].eql?(worstObsIndex))
        worstObsDR = parts[-1].to_f;
      end
    end

  end

  if(rms.to_f > $rmsThreshold)
    removePnt(worstObsIndex.to_i, datFilename, "tmp.dat");
  end
  #puts rms.to_s + "," + worstObsIndex.to_s + "," + worstObsDR.to_s + "," + "tmp.dat";
  return[rms.to_s, "tmp.dat"];
end

rms = 9999.0;
$origFilename = ARGV[0];
filename = $origFilename;
result = oneFit(filename);
rms = result[0].to_f;
filename = result[1];
origRMS = rms;
while(rms > $rmsThreshold)
  result = oneFit(filename);
  rms = result[0].to_f;
  filename = result[1];
end

newfitFilename = File.basename($origFilename, ".*") + ".dat_fit";
cmd = "mv #{filename} #{newfitFilename}";
#puts cmd;
`#{cmd}`;

origNumPnts = countPoints($origFilename);
numPoints = countPoints(newfitFilename);

puts "Input DAT file: " + $origFilename;
puts "Original RMS:   " + origRMS.to_s + ", num points: "  + origNumPnts.to_s;
puts "Fitted RMS:     " + rms.to_s + ", num points: "  + numPoints.to_s;
puts "FIT file:       " + File.basename($origFilename, ".*") + ".fit"
puts "New DAT file:   " + newfitFilename;

if(ARGV.length > 1 && ARGV[1].eql?("-viewscripts"))

  puts;
  puts "To view the point scatter diagram before the culling:";
  puts "  source /hcro/opt/tpoint/tpoint.sh";
  puts "  tpoint";
  puts "  indat #{$origFilename}";
  puts "  USE IE IA CA AN AW";
  puts "  FAUTO";
  puts "  gscat a"

  puts;
  puts "To view the point scatter diagram after the culling:";
  puts "  source /hcro/opt/tpoint/tpoint.sh";
  puts "  tpoint";
  puts "  indat #{newfitFilename}";
  puts "  USE IE IA CA AN AW";
  puts "  FAUTO";
  puts "  gscat a"

  puts;

end

`rm -f tpoint.cmds`
`rm -f tpoint.clog`
