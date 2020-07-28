#!/usr/bin/env ruby
on_or_off = ARGV[0]
antlist = ARGV[1]
source = ARGV[2]

cmd = "/hcro/atasys/ata/run/atatrackephem \"#{antlist} #{source}_#{on_or_off}.ephem -w\"";
#print cmd
`#{cmd}`
print "{ 'status' : 'OK', 'pointing' : '#{on_or_off}', 'ant_list' : '#{antlist}' }";
