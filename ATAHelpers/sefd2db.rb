#!/usr/bin/env ruby

require 'rubygems'
require 'time'
require 'date'
require 'fileutils'

def printHelp() 

  puts "Syntax: sefd2db.rb <ant> <sefd> <obsid>";
  puts " OR: obs2db.rb list - will simply list the most 100 recent sefd rows.";
  puts "Stores SEFD records in the \"sefd\" database table.";
  puts "The obsid is the id of this observation as stored in the observations table";
  puts "The time and freq, target, etc. can be derived using the obsid to query";
  puts "  observations table.";
  puts " Example: ./sefd2db.rb 1a 1654.7 3";
  exit(0);

end

if(ARGV.length == 1 && ARGV[0].eql?("list"))
  puts `echo \"select * from sefd LIMIT 100; \" | mysql ants`;
  exit(0);
end

if(ARGV.length != 3) then printHelp(); end

ant = ARGV[0];
sefd = ARGV[1];
obsid = ARGV[2];

#mysql> describe sefd
#    -> ;
#+-------+------------+------+-----+---------+----------------+
#| Field | Type       | Null | Key | Default | Extra          |
#+-------+------------+------+-----+---------+----------------+
#| id    | int(11)    | NO   | PRI | NULL    | auto_increment |
#| obsid | int(11)    | NO   | MUL | NULL    |                |
#| ant   | varchar(3) | NO   |     | NULL    |                |
#| sefd  | float      | NO   |     | NULL    |                |
#+-------+------------+------+-----+---------+----------------+

sql = "INSERT INTO sefd set obsid=#{obsid.to_i}, ant='#{ant}', sefd=#{sefd.to_f};";

`echo \"#{sql}\" | mysql ants`
`echo \"#{sql}\" | mysql -h 35.233.233.72 -u jrseti ants`

