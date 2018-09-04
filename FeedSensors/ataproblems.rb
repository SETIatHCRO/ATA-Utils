#!/usr/bin/env ruby
#
# Get the last n number of ataproblems for each antenna, create a JSON file and
# scp it to antfeeds.setiquest.info.
# Author: Jon Richards

require 'rubygems'
require 'date'
require 'time'
require 'fileutils'
require 'json'

#ataproblem --history ant5h
##ataproblem --current :ants
#
$LIMIT = 20;

def getAntList() 

  antList = [];
  `/hcro/atasys/ata/run/ataproblem --current ":ants"`.each_line do |line|
    parts = line.strip!.chomp.split(/\s+/);
    antList << parts[0][3..-1];
  end
  return antList;
end

def getProblems(ant)
  #ant5h                        up    RecoveryServer    2018-07-03 15:42:32  [SET_ONLINE]
  problems = [];
  cmd = "/hcro/atasys/ata/run/ataproblem --history \"ant#{ant}\"";
  `#{cmd}`.each_line do |line|
    line.chomp!.strip!;
    parts = line.split(/\s+/);

    status = "";
    (5..parts.length-1).each do |i|
      status += parts[i] + " ";
    end
    status.chop!;

    #puts ant + ": " + parts[1] + "," + parts[3] + "," + parts[4] + "," + status;
    str = "";
    if(parts[1].eql?("up"))
      str = "[" + parts[3] + "] " + parts[1] + "   " + status;
    else
      str = "[" + parts[3] + "] " + parts[1] + " " + status;
    end
    #puts str;
    problems << str;
  end

  return problems.last($LIMIT).reverse();

end

antlist = getAntList();
problems = Hash.new();
antlist.each do |a|
  problems[a] = getProblems(a);
end

data = Hash.new();
data["ants"] = antlist;
data["problems"] = problems;
data["time"] = Time.now.to_i;

s =  "ataproblems(" + data.to_json + ")";

File.open("./ataproblems.jsonp", 'w') { |file| file.write(s) }
#cmd = "scp ./ataproblems.jsonp setiquest@setiquest.info:feeds/ataproblems.jsonp";
cmd = "scp ./ataproblems.jsonp sonata@antfeeds.setiquest.info:www/feeds/ataproblems.jsonp";
puts cmd;
`#{cmd}`;

`rm ./ataproblems.jsonp`

