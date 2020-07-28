#!/usr/bin/env ruby
on_or_off = ARGV[0]
antlist = ARGV[1]
source_ra_s = ARGV[2]
source_dec_s = ARGV[3]

source = "#{source_ra_s}-#{source_dec_s}"

cmd = "/hcro/atasys/ata/run/atatrackephem \"#{antlist} #{source}_#{on_or_off}.ephem -w\"";
#print cmd
`#{cmd}`
print "{ 'status' : 'OK', 'pointing' : '#{on_or_off}', 'ant_list' : '#{antlist}' }";
