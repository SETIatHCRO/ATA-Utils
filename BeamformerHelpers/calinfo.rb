#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'open3'

def calinfo(calname, freq_mhz)

  puts `ssh obs@tumulus /home/obs/mmm/karto/cals/calinfo target=#{calname} freq=#{(freq_mhz.to_f/1000.0).to_s}`;

end

def getCalFlux(calname, freq_mhz)

  flux = nil;
  cmd = "ssh obs@tumulus /home/obs/mmm/karto/cals/calinfo target=" + calname + " freq=" + (freq_mhz.to_f/1000.0).to_s + " 2>/dev/null";
  #puts cmd;
  calinfo = `#{cmd}`
  calinfo.each do |line|
    if(line.index("Estimated flux:") != nil)
      line.strip!;
      #puts line;
      #parts = line.split(/[^\w-]+/);
      parts = line.split(/\s+/);
      return parts[2];
    end
  end

  return "0.0";

end

def isUp(calName)

  isup = false;
  cmd = "/bin/bash /hcro/atasys/ata/run/atacheck " + calName;
  #puts cmd;
  calinfo = `#{cmd}`
  calinfo.each do |line|
    if(line.index("is up") != nil)
      isup = true;
    end
    if(isup == true && line.index("Sets") != nil)
      parts = line.split(/\s+/);
      return [true, parts[8]];
    end
    if(isup == false && line.index("Rises") != nil)
      parts = line.split(/\s+/);
      return [false, parts[8]];
    end
  end

  return [false, "Undetermined"];

end


if __FILE__==$0

  if(ARGV.length == 0) #print help
    puts "syntax: #{$PROGRAM_NAME} <calibrator name> <freq in MHz>";
    exit(1);
  end

  calname = ARGV[0]
  freq_mhz = ARGV[1];

  flux = getCalFlux(calname, freq_mhz);
  isup = isUp(calname);
  if(isup[0] == true) then puts "#{calname}, flux #{flux} at #{freq_mhz} MHz, UP - sets #{isup[1]}"; end
  if(isup[0] == false) then puts "#{calname}, flux #{flux} at #{freq_mhz} MHz, NOT UP - rises #{isup[1]} Pacific"; end


end
