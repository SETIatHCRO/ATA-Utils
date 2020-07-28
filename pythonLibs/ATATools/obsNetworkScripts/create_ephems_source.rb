#!/usr/bin/env ruby
#
source = ARGV[0]
azshift = ARGV[1].to_f;
elshift = ARGV[2].to_f;

cmd = "ataephem \"#{source}\"";
`#{cmd}`

`mv #{source}.ephem #{source}_on.ephem`

File.open("#{source}_off.ephem", "w+") do |fout|
  File.foreach("#{source}_on.ephem") do |line|
    parts = line.chop.split(/\s+/)
    fout.puts parts[0] + "  " + (parts[1].to_f + azshift).to_s + "  " + (parts[2].to_f + elshift).to_s + "  " + parts[3]
    #puts line;
  end
end


print "{ 'status' : 'OK', 'az_off' : #{azshift}, 'el_offset' : #{elshift} }";
