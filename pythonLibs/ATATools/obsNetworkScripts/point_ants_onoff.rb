#!/usr/bin/env ruby
on_or_off = ARGV[0]
antlist = ARGV[1]

cmd = "/hcro/atasys/ata/run/atatrackephem \"#{antlist} #{on_or_off}_source.ephem -w\"";
#print cmd
`#{cmd}`
print "{ 'status' : 'OK', 'pointing' : '#{on_or_off}', 'ant_list' : '#{antlist}' }";
