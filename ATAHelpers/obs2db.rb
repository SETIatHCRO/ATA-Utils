#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: obs2db.rb <comma sep ant list> <freq MHz> <target name> <az offset, deg> <el offset, deg>";
  puts " OR: obs2db.rb list - will simply list the most 100 recent observations rows.";
  puts "Stores observation records on the \"observations\" database table.";
  puts " Example: ./obs2db.rb 1a,1b 1421.4 casa 0 10";
  puts " Output: The observation id to use for reference to this row.";
  exit(0);

end

if(ARGV.length == 1 && ARGV[0].eql?("list"))
  puts `echo \"select * from observations LIMIT 100; \" | mysql ants`;
  exit(0);
end

if(ARGV.length != 5) then printHelp(); end

antlist = ARGV[0];
freq = ARGV[1];
target = ARGV[2];
az_offset = ARGV[3];
el_offset = ARGV[4];

#mysql> describe observations;
#+-----------+--------------+------+-----+---------+----------------+
#| Field     | Type         | Null | Key | Default | Extra          |
#+-----------+--------------+------+-----+---------+----------------+
#| id        | int(11)      | NO   | PRI | NULL    | auto_increment |
#| ts_start  | datetime     | NO   |     | NULL    |                |
#| ts_stop   | datetime     | YES  |     | NULL    |                |
#| ants      | varchar(255) | NO   |     | NULL    |                |
#| az_offset | float        | YES  |     | 0       |                |
#| el_offset | float        | YES  |     | 0       |                |
#| freq      | float        | NO   |     | NULL    |                |
#| target    | varchar(32)  | NO   |     | NULL    |                |
#+-----------+--------------+------+-----+---------+----------------+

timestamp = Time.now.strftime('%Y-%m-%d %H:%M:%S');

sql = "INSERT INTO observations set ts_start='#{timestamp}', ants='#{antlist}', freq=#{freq.to_f}, target='#{target}', az_offset=#{az_offset.to_f}, el_offset=#{el_offset.to_f};";

#puts sql;

`echo \"#{sql}\" | mysql ants`
`echo \"#{sql}\" | mysql -h 35.233.233.72 -u jrseti ants`

id = "?";
`echo \"select MAX(id) from observations;\" | mysql ants`.each_line do |line|
  id = line.chomp;
end
puts id;
