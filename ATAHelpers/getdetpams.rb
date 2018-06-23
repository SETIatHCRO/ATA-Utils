#!/usr/bin/env ruby

require 'rubygems'
require 'date'
require 'fileutils'

def doCmd(cmd) 
  #puts "cd /home/obs/jrichards; " + cmd;
  return `#{cmd}`;
end

if(ARGV.length != 1)
  puts "Get an antenna pam settings and det values";
  puts "Syntax: getdetpams <ant>";
  puts "  Example: getdetpams 4j";
  puts "  returns: <ant>,<front pamx db>,<back pamx db>,<front pamy db>,<back pamy db>,<det x>,<det y>";
  exit(0);
end

ant = ARGV[0]

cmd = "ssh ataant@antcntl 'ssh ant#{ant} \"echo getdet x | netcat pax 23\"'";
detx = doCmd(cmd).split(/\s+/)[-1];
cmd = "ssh ataant@antcntl 'ssh ant#{ant} \"echo getdet y | netcat pax 23\"'";
dety = doCmd(cmd).split(/\s+/)[-1];
#puts detx + "," + dety;

#atagetpams 4j
#ant4j  on 23.0  on 18.0
#
cmd = "/hcro/atasys/ata/run/atagetpams \"#{ant} --xfb --yfb\"";
#atagetpams 4j --xfb --yfb
#ant4j  on 00.0/23.0  on 00.0/18.0
pams = doCmd(cmd).split(/\s+/);;
pamx = pams[2].split("/");
pamy = pams[4].split("/");
puts ant + "," + pamx[0] + "," + pamx[1] + "," + pamy[0] + "," + pamy[1] + "," + detx + "," + dety;

