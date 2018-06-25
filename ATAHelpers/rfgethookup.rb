#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: rfgethookup [<ant> <pol> | all]";
  puts "Get the rf switch port and switch number for a given pol. ";
  puts "If \"all\" specified, all hookups will be reported.";
  exit(0);

end

if(ARGV.length == 1 && (ARGV[0].eql?("all"))) #all

  unique = Hash.new(); 
  results = [];
  cmd = "SELECT switch,port,ant,pol,ts from rfswitch ORDER BY ts DESC";
  result =  `echo \"#{cmd}\" | mysql ants`
  count = 0;
  result.each_line do |line|
    if(count == 0) then count = 1; next; end
    line.chomp!;
    parts = line.split(/\s+/);
    #name = parts[0]+parts[1]+parts[2]+parts[3];
    name = parts[0]+parts[1];
    if(unique[name] == nil)
      unique[name] = parts;
    end
  end

  count = 0;
  unique.each do |key, value|
    results[count] = value;
    count = count + 1;
  end

  puts "switch port antpol time";
  results.sort.each do |r|
    puts r[0] + "      " + r[1] + "    " + r[2] + r[3] + "    " + r[4] + "," + r[5];
  end

  exit(0);

elsif(ARGV.length == 2 || ARGV.length == 1) #ant, pol

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
  end
  exit(0);

else

  printHelp();

end
