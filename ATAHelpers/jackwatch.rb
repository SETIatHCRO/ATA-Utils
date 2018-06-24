#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'

def getBFAAnts(group)
  cmd = "/home/obs/ruby/bin/fxconf.rb sals #{group}";
  return `#{cmd}`.chomp.gsub(" ", ",");
end

def getAzEl(ant)
  cmd = "/hcro/atasys/ata/run/atagetazel \"#{ant}\"";
  result = `#{cmd}`.chomp;
  parts = result.split(/\s+/);
  return [parts[1], parts[2]];

end

def getFreq()
  cmd = "/hcro/atasys/ata/run/atagetskyfreq \"a\"";
  return `#{cmd}`.chomp;
end


loop do

  antlist = getBFAAnts("bfa");
  t = Time.now.strftime("[%Y/%m/%d %H:%M:%S]");
  if(antlist.length > 1)
    azel = getAzEl(antlist.split(",")[0]);
    freq = getFreq();
    $stderr.puts "#{t} Ants: #{antlist} Freq: #{freq}, Az: #{azel[0]}, El: #{azel[1]}";
  else
    $stderr.puts "#{t} No antennas assigned to BFA group";
  end

  `sleep 5`;

end


