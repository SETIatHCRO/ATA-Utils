#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: getCurrentObsId.rb";
  puts "Gets the latest observation table id.";
  exit(0);

end

if(ARGV.length != 0) then printHelp(); end

id = "?";
`echo \"select MAX(id) from observations;\" | mysql ants`.each_line do |line|
  id = line.chomp;
end
puts id;
