#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: rfswitchant <ant> <pol>";
  puts "Switch the rfswitch to an antpol. ";
  exit(0);

end

if(ARGV.length == 2 || ARGV.length == 1) #ant, pol

  ant = "";
  pol = "";
  if(ARGV.length == 1) 
    ant = ARGV[0][0..1];
    pol = ARGV[0][2..-1];
  else
    ant = ARGV[0].downcase();
    pol = ARGV[1].downcase();
  end

  cmd = "SELECT ant, pol, switch, port, ts from rfswitch where ant='#{ant}' and pol='#{pol}' ORDER BY ts DESC LIMIT 1";
  puts "switch port antpol time";
  count = 0;
  result = `echo \"#{cmd}\" | mysql ants`;
  result.each_line do | line|
    if(count == 0) then count = 1; next; end
    parts = line.chomp.split(/\s+/);
    puts parts[2] + "      " + parts[3] + "    " + parts[0]+parts[1] + "    " + parts[4] + " " + parts[5];
    cmd = "ssh sonata@10.1.49.174 '/usr/local/bin/rfswitch " + parts[3] + " " + parts[2] + "'";
    puts cmd;
    `#{cmd}`;
    exit(0);
  end

  puts "Not found";

else

  printHelp();

end
