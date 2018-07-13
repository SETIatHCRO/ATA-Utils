#!/usr/bin/env ruby
#  
require 'time'
require 'date'
require 'thread'
require 'json'

h = Hash.new();
ants = Hash.new();
sources = Hash.new();

filename = ARGV[0];
File.open(filename).each do |line|
	#taua,5c,y,4000.00,0.000000,0.000000
	parts = line.split(",");
	source = parts[0];
	ant = parts[1];
	pol = parts[2];
	freq = parts[3];
	sefd = parts[4];
	ratio = parts[5].chomp;

	ants[ant] = 1;
	sources[source] = 1;

	if(h[source] == nil)
		h[source] = Hash.new();
	end
	if(h[source][ant] == nil)
		h[source][ant] = Hash.new();
	end
	if(h[source][ant][pol] == nil)
		h[source][ant][pol] = [];
	end
	h[source][ant][pol] << [freq, sefd];
end

antlist = [];
ants.each do |key, value|
	antlist << key;
end

sourcelist = [];
sources.each do |key, value|
	sourcelist << key;
end

h["ants"] = antlist;
h["sources"] = sourcelist;

j = h.to_json;
puts "sefd(" + j + ")";


