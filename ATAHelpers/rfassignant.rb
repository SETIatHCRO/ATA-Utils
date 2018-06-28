#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: rfassignant <ant> <pol> <switch (0..n)> <port (1..n{8 or 16})>";
  puts "Define and store in the databse the antpol to RF switch port.";
  exit(0);

end

if(ARGV.length != 4) then printHelp(); end

ant = ARGV[0].downcase();
pol = ARGV[1].downcase();
switch = ARGV[2].downcase();
port = ARGV[3].downcase();
timestamp = Time.now.strftime('%Y-%m-%d %H:%M:%S');

cmd = "INSERT INTO rfswitch set ts='#{timestamp}', ant='#{ant}', pol='#{pol}', switch=#{switch}, port=#{port}";
puts cmd;
`echo \"#{cmd}\" | mysql ants`


