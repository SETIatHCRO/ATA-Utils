#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'
require 'json'
require 'thread'
require 'time'

$DEBUG = true;
$MINDB = 0;
$MAXDB = 60;
$values = Hash.new();
$ants = "";

$mutex = Mutex.new();
$cryo = Hash.new();

$timenow = Time.now.to_i;
puts "Time now is " + $timenow.to_s;

def doCmd(cmd) 
  puts "cd /home/obs/jrichards; " + cmd;
  return `#{cmd}`;
end

#get the feeds in a group
def getAntList(group)
   cmd = "/home/obs/ruby/bin/fxconf.rb sals #{group}";
   return `#{cmd}`.chomp.gsub(" ", ",");
end

def getPAMDETS(ant, pamxydb)
  cmd = "/hcro/atasys/ata/run/atasetpams \"#{ant} #{pamxydb.to_s} #{pamxydb.to_s}\"";
  doCmd(cmd);
  `sleep 1`;
  cmd = "/hcro/atasys/ata/run/atagetpams \"#{ant} --xfb --yfb\"";
  pams = doCmd(cmd).split(/\s+/);;
  pamx = pams[2].split("/");
  pamy = pams[4].split("/");
  cmd = "ssh ataant@antcntl 'ssh ant#{ant} \"echo getdet x | netcat pax 23\"'";
  detx = doCmd(cmd).split(/\s+/)[-1];
  cmd = "ssh ataant@antcntl 'ssh ant#{ant} \"echo getdet y | netcat pax 23\"'";
  dety = doCmd(cmd).split(/\s+/)[-1];
  return [pamx[0].to_f, pamx[1].to_f, detx.to_f, pamy[0].to_f, pamy[1].to_f, dety.to_f];
end

def getCryo()

  antlist = "";
  $ants.each do |a|
    antlist += "," + a;
  end

  cmd = "/hcro/atasys/ata/run/atagetcryotemp \"#{antlist}\"";
  `#{cmd}`.each_line do |line|
    parts = line.chomp.split(/\s+/);
    puts parts[0][3..-1] + "," + parts[1];
    $cryo[parts[0][3..-1]] = parts[1].to_f;
  end

end

def getValues(ant)

  pamx_front = [];
  pamx_back = [];
  detx = [];

  pamy_front = [];
  pamy_back = [];
  dety = [];

  dbs = [];

  ($MINDB..$MAXDB).each do |db|
    vals = getPAMDETS(ant, db);
    dbs << db;
    pamx_front << vals[0];
    pamx_back << vals[1];
    detx << vals[2];
    pamy_front << vals[3];
    pamy_back << vals[4];
    dety << vals[5];
  end

  $mutex.synchronize do
    $values[ant] = { "cryo" => $cryo[ant], "db" => dbs, "pamx_front" => pamx_front, "pamx_back" => pamx_back, "detx" => detx, "pamy_front" => pamy_front, "pamy_back" => pamy_back, "dety" => dety };
  end

end

if(ARGV.length != 1)
  puts "Sweeps the range of PAM settings and records the det values.";
  puts "Syntax: sweepdetpams <ant list comma separated>";
  puts "If ant list is \"none\" or \"bfa\" then get the list from fxconf.rb";
  puts "  Example: sweepdetpams 1a,4j";
  puts "  returns: ";
  exit(0);
end

if(ARGV[0].eql?("none") || ARGV[0].eql?("bfa"))
  $ants = getAntList(ARGV[0]).gsub(" ",",").split(",");
  #puts "ant list is " + $ants;
else
  if(!ARGV[0].include?(","))
    $ants = [ARGV[0]];
  else
    $ants = ARGV[0].split(",");
  end
end

if($ants.length < 2)
  puts "ERROR: no dishes specified\n";
  exit(0);
end

getCryo();

threads = [];

$ants.each do |ant|
  threads << Thread.new{ getValues(ant) };
end

threads.each do |t|
  t.join();
end

j = { "t" => $timenow, "values" => $values }.to_json;
puts j;

File.open("db_pams_dets.json", 'w') { |file| file.write("db_pams_dets(" + j + ")") }
`scp ./db_pams_dets.json setiquest@setiquest.info:feeds/db_pams_dets.json`;


