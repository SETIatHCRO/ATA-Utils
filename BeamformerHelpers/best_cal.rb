#!/usr/bin/env ruby
require 'open3'
load 'calinfo.rb'

def getCalsList()

  return ["3c123", "3c380", "3c273", "3c84", "3c48", "3c286"];

end

def getBestCal(freq_mhz)

  cals = getCalsList();

  uplist = [];
  notuplist = [];
  cals.each do |cal|
    up = isUp(cal)[0];
    if(up == true)
      uplist << cal;
    else
      notuplist << cal;
    end
  end

  #puts "Ones that are up:";
  best = "none";
  max_flux = -1;
  uplist.each do |cal|
    flux = getCalFlux(cal, freq_mhz.to_s);
    if(flux.to_f > 0.0)
      if(flux.to_f > max_flux) then best = cal; max_flux=flux.to_f end
    end
  end

  return [best, max_flux];

end

if __FILE__==$0

  if(ARGV.length == 0) #print help
      puts "Determines the best calibrator to use at a certain frequency at this moment.";
      puts "syntax: #{$PROGRAM_NAME}: <freq in MHz>";
      exit(1);
  end

  cals = getCalsList();
  puts "search for best cal @ #{ARGV[0].to_f}MHz among the following:";
  cals.each do |c|
    puts "\t" + c;
  end

  best_info = getBestCal(ARGV[0].to_f);

  best = best_info[0];
  max_flux = best_info[1];

  isup = isUp(best);
  if(isup[0] == true) then puts "#{best}, flux #{max_flux.to_s} at #{ARGV[0].to_s} MHz, UP - sets #{isup[1]}"; end
  if(isup[0] == false) then puts "#{best}, flux #{max_flux.to_s} at #{ARGV[0].to_s} MHz, NOT UP - rises #{isup[1]} Pacific"; end

end
