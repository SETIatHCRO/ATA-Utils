#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'

$results = Hash.new();

$antlist = "";
$lo = "a";
$GROUPNAME = "bfa";

def doCmd(cmd) 
  puts "cd /home/obs/jrichards; " + cmd;
  `#{cmd}`;
end

#get the feeds in a group
def getAntList(group)
  cmd = "/home/obs/ruby/bin/fxconf.rb sals #{group}";
  return `#{cmd}`.chomp.gsub(" ", ",");
end


if(ARGV.length != 4)
  puts "pointshift <source> <freq MHz> <az offset deg> <el offset deg>";
  puts " NOTE: the antennas used must be in group #{$GROUPNAME}";
  puts "  Example: pointshift w3oh 4000.0 10 20";
  exit(0);
end

$antlist = getAntList($GROUPNAME);
if($antlist.length < 2)
  puts "ERROR: There are no antennas in group #{$GROUPNAME}";
  exit(1);
end

target = ARGV[0]
freq = ARGV[1];
azshift = ARGV[2].to_f;
elshift = ARGV[3].to_f;

cmd = "ataephem \"#{target}\"";
doCmd(cmd);

File.open("temp.ephem", "w+") do |fout|
  File.foreach(target + ".ephem") do |line|
    parts = line.chop.split(/\s+/)
    fout.puts parts[0] + "  " + (parts[1].to_f + azshift).to_s + "  " + (parts[2].to_f + elshift).to_s + "  " + parts[3]
    #puts line;
  end
end

cmd = "/hcro/atasys/ata/run/atalnaon \"#{$antlist}\"";
doCmd(cmd);

cmd = "/hcro/atasys/ata/run/atasetfocus \"#{$antlist} #{freq}\"";
doCmd(cmd);

cmd = "/hcro/atasys/ata/run/atasetskyfreq \"#{$lo} #{freq}\"";
doCmd(cmd);

cmd = "/hcro/atasys/ata/run/atatrackephem \"#{$antlist} temp.ephem -w\"";
doCmd(cmd);
