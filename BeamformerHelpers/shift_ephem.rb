#!/usr/bin/env ruby

/**
 * Shifts an ephemeris by an amount in az and el.
 * Creates a new ephemeris file. The original is untouched.
 */
require 'rubygems'
require 'date'
require 'fileutils'

def shift_ephem(infilename, outfilename, azshift, elshift) 

  of = File.open(outfilename, "w");

  File.foreach(infilename) do |line|
    parts = line.chop.split(/\s+/)
    #puts parts[0] + "  " + (parts[1].to_f + azshift).to_s + "  " + (parts[2].to_f + elshift).to_s + "  " + parts[3]
    of.write(parts[0] + "  " + (parts[1].to_f + azshift).to_s + "  " + (parts[2].to_f + elshift).to_s + "  " + parts[3] + "\n");
  end

  of.close();

end

if __FILE__==$0

  if(ARGV.length == 0) #print help
    puts "syntax: shift_ephem <input file> <output file> <shift az deg> <shift el deg>";
    exit(1);
  end

  infile = ARGV[0]
  outfile = ARGV[1];
  azshift = ARGV[2].to_f;
  elshift = ARGV[3].to_f;

  shift_ephem(infile, outfile, azshift, elshift);

  
end
