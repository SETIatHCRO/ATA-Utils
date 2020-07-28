#!/usr/bin/env ruby
#
source_ra_s = ARGV[0];
source_dec_s = ARGV[1];
azshift = ARGV[2].to_f;
elshift = ARGV[3].to_f;

source = "#{source_ra_s},#{source_dec_s}"
source_name = "#{source_ra_s}-#{source_dec_s}"

cmd = "ataephem --radec \"#{source}\"";
`#{cmd}`

`mv #{source_name}.ephem #{source_name}_on.ephem`

File.open("#{source_name}_off.ephem", "w+") do |fout|
  File.foreach("#{source_name}_on.ephem") do |line|
    parts = line.chop.split(/\s+/)
    fout.puts parts[0] + "  " + (parts[1].to_f + azshift).to_s + "  " + (parts[2].to_f + elshift).to_s + "  " + parts[3]
    #puts line;
  end
end


print "{ 'status' : 'OK', 'az_off' : #{azshift}, 'el_offset' : #{elshift} }";
