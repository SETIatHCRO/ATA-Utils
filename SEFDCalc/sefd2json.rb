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
	#taua,5c,y,4000.00,0.000000,0.000000,fname
	if(line.include?("skip")) then next; end
	parts = line.split(",");
	source = parts[0];
	ant = parts[1];
	pol = parts[2];
	freq = parts[3];
	sefd = parts[4];
	ratio = parts[5];
	fname = parts[6].chomp;

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
	h[source][ant][pol] << [freq, sefd, fname];
end

=begin
filename = ARGV[1];
File.open(filename).each do |line|
	#casa,4g,y,9000.00,39008.822899,67.708553,4gy_9000.00_casa_292.png
	line.chomp!;
	if(line.start_with?("skip")) then next; end
	parts = line.split(",");
	if(parts.length != 7) then next; end
	source = parts[0];
	ant = parts[1];
	pol = parts[2];
	freq = parts[3];
	sefdx = parts[4];
	sefdy = parts[5];
	png = parts[6];

	if(h[source] == nil || h[source][ant] == nil) then next; end


	if(h[source][ant][pol] != nil)
		h[source][ant][pol].each do |fs|
			if(fs[0].to_f == freq.to_f)
				fs << png;
			end
		end
	end
end
=end



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


