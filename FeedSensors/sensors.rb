#!/usr/bin/env ruby

# sensors.rb
# Jon Richards, SETI Institute
# June 12, 2018
#
# Reads the historical sensor data, crams it into the database
# Data obtained by "ssh atasys@sonata ls -l /home/obs/archive/tempmon/june08/20*"

require 'fileutils'
require 'time'
require 'date'
require 'chronic'
require 'json'

$DATADIR = "/home/obs/archive/tempmon/june08/";
$TABLENAME = "various_sensors";
$DBASE_NAME = "ants";
$uniqueHash = Hash.new();

# pront help if no command lines
if(ARGV.length == 0) 

  puts "";
  puts "sensors.rb";
  puts "  Reads historical sensor data from obs@tumulus /home/obs/archive/tempmon/june08/";
  puts "  and stores it in the MySQL database table \"#{$TABLENAME}\"."
  puts " NOTE: You need to have a MySQL database set up with a #{$TABLENAME} table.";
  puts "       Assumes the database is on the local computer and has all permissions.";
  puts "Syntax:";
  puts "  ./sensors.rb table <date> - prints out the CREATE TABLE syntax.";
  puts "     This is a convenience for when you need to create a new database instance.";
  puts "     The <date> specifies a file to sample for all the field names.";
  puts "     ex: ./sensor.rb table 2014-09-03";
  puts "  ./sensors.rb all - will attempt to process ALL the data in ";
  puts "     /home/obs/archive/tempmon/june08";
  puts "  ./sensors.rb 2018-06-06 - will process just one day's data.";
  puts "  ./sensors.rb -d <minus day number> - will process x number of days ago.";
  puts "  ./sensors.rb -d 1 - will process just yesterday's data.";
  puts "";
  exit(0);
end

# Get a list of all the data files, full path. 
# Return as array.
def getFileList() 

  fileList = [];
  results = `ssh atasys@sonata ls -l  #{$DATADIR}20*`
  results.each_line do |line|
    line.chomp!;
    #puts line;
    fileList << line.split(/\s+/)[-1].chomp;
  end

  return fileList

end

# Get a list, in form or a hashmap, of all the items listed in a file.
# Exclude weather items
# ( 3-Sep-14 10:45:40.003, 0.69 ) ant5g ADC07
def getItems(filename)

  items = Hash.new();
  lines = `ssh atasys@sonata cat #{filename}*`
  lines.each_line do |line|
    if(line.start_with?("(") && !line.include?("weather"))
      parts = line.chomp.split(/\s+/);
      items[parts[6]] = parts[6];
    end
  end
  return items;

end

# Convert the data datetime string into one suitable for MySQL.
def toDatetime(s)
  #3-Sep-14 18:00:42.575
  parts = s.split(/\s+/);
  parts2 = parts[0].split('-');
  parts3 = parts[1].split(':');
  month = parts2[1];
  mon = -1;
  if(month.downcase.eql?("jan")) then mon = 1; end
  if(month.downcase.eql?("feb")) then mon = 2; end
  if(month.downcase.eql?("mar")) then mon = 3; end
  if(month.downcase.eql?("apr")) then mon = 4; end
  if(month.downcase.eql?("may")) then mon = 5; end
  if(month.downcase.eql?("jun")) then mon = 6; end
  if(month.downcase.eql?("jul")) then mon = 7; end
  if(month.downcase.eql?("aug")) then mon = 8; end
  if(month.downcase.eql?("sep")) then mon = 9; end
  if(month.downcase.eql?("oct")) then mon = 10; end
  if(month.downcase.eql?("nov")) then mon = 11; end
  if(month.downcase.eql?("dec")) then mon = 12; end

  str = "20" + ('%02d' % parts2[2].to_i).to_s + "-" + ('%02d' % mon.to_i).to_s + "-" + ('%02d' % parts2[0].to_i).to_s;
  str +=  " " + ('%02d' % parts3[0].to_i).to_s + ":" + ('%02d' % parts3[1].to_i).to_s + ":" + ('%02d' % parts3[2].to_i).to_s;
  return str;
end

# Determines if a sensor vaue is for the correct day and if it is a duplicate or not.
# This avoind duplicates that appear in the data. A bummer I had to deal with this.
# Return true if this data item is unique and should be used.
def isUnique(ant4hash, dt4hash, name)
  parts = dt4hash.split('/');
  year = parts[-1].split('-')[0];
  month = parts[-1].split('-')[1];
  day = parts[-1].split('-')[2];
  if(year.to_i != $year.to_i || month.to_i != $month.to_i || day.to_i != $day.to_i)
    #puts "Diff day #{name} : #{$year} #{year}, #{$month} #{month}, #{$day} #{day}";
    return false;
  end
  key = ant4hash +  dt4hash + name;
  if($uniqueHash[key] == nil)
    $uniqueHash[key] = 1;
    return true;
  else
    return false;
  end
end

# Initialize the hash values for the database table fields.
def initFieldHash()
    fieldhash = Hash.new();
    fieldhash['ts'] = nil;
    fieldhash['ant'] = nil;
    fieldhash['state'] = 0;
    fieldhash['DriveBoxTemp'] = -99;
    fieldhash['ControlBoxTemp'] = -99;
    fieldhash['PAXBoxTemp'] = -99;
    fieldhash['RimBoxTemp'] = -99;
    fieldhash['ADC01'] = -99;
    fieldhash['ADC02'] = -99;
    fieldhash['ADC03'] = -99;
    fieldhash['ADC04'] = -99;
    fieldhash['ADC07'] = -99;
    fieldhash['ADC08'] = -99;
    fieldhash['ADC09'] = -99;
    fieldhash['ADC10'] = -99;
    fieldhash['ADC11'] = -99;
    fieldhash['CryoRejTemp'] = -99;
    fieldhash['CryoTemp'] = -99;
    fieldhash['CryoPower'] = -99;
    return fieldhash;
end

# Convert a file of data to a CVS format suitable for a MySQL LOAD.
def toCSV(filename)

  puts "toCSV: " + filename;

  csv = "";
  ant = "";
  ant4hash = "";
  dt4hash = "";
  first = true;
  lines = `ssh atasys@sonata cat #{filename}*`
  fields = Hash.new();
  dt = "";
  rejects = 0;
  fieldHash = initFieldHash();
  lines.each_line do |line|
 
    if(line.start_with?("(") && !line.include?("weather"))
      parts = line.chomp.split(/\s+/);
      if(parts.length != 7) then next; end
      tempAnt = parts[5][3..-1];
      if(first) 
        first = false;
        ant = tempAnt;
        dt = toDatetime("#{parts[1]} " + "#{parts[2].chop}\"");
        fieldHash['ts'] = dt;
        ant4hash = ant;
        dt4hash = dt;
        fieldHash['ant'] = ant;
      end
      if(ant != tempAnt)
        if(fields.length > 0) 
          csvTemp = "";
          csvTemp += fieldHash['ts'].to_s + ",";
          csvTemp += fieldHash['ant'].to_s + ",";
          csvTemp += fieldHash['state'].to_s + ",";
          csvTemp += fieldHash['DriveBoxTemp'].to_s + ",";
          csvTemp += fieldHash['ControlBoxTemp'].to_s + ",";
          csvTemp += fieldHash['PAXBoxTemp'].to_s + ",";
          csvTemp += fieldHash['RimBoxTemp'].to_s + ",";
          csvTemp += fieldHash['ADC01'].to_s + ",";
          csvTemp += fieldHash['ADC02'].to_s + ",";
          csvTemp += fieldHash['ADC03'].to_s + ",";
          csvTemp += fieldHash['ADC04'].to_s + ",";
          csvTemp += fieldHash['ADC07'].to_s + ",";
          csvTemp += fieldHash['ADC08'].to_s + ",";
          csvTemp += fieldHash['ADC09'].to_s + ",";
          csvTemp += fieldHash['ADC10'].to_s + ",";
          csvTemp += fieldHash['ADC11'].to_s + ",";
          csvTemp += fieldHash['CryoRejTemp'].to_s + ",";
          csvTemp += fieldHash['CryoTemp'].to_s + ",";
          csvTemp += fieldHash['CryoPower'].to_s;
          csvTemp += "\n";
          csv += csvTemp;
          fieldHash = initFieldHash();
          fields = Hash.new();
        end
        ant = tempAnt;
        dt = toDatetime("#{parts[1]} " + "#{parts[2].chop}\"");
        ant4hash = ant;
        dt4hash = dt;
        fieldHash['ant'] = ant;
        fieldHash['ts'] = dt;
        if(fields[parts[6]] == nil && isUnique(ant4hash, dt4hash, parts[6]))
          fieldHash[parts[6]] = ('%.2f' % parts[3]);
          fields[parts[6]] = parts[6];
        else
          #puts "REJECT: " + ant + "," + dt + "," + parts[6];
          rejects = rejects + 1;
        end
      else
        if(fields[parts[6]] == nil && isUnique(ant4hash, dt4hash, parts[6]))
          fieldHash[parts[6]] = ('%.2f' % parts[3]);
          fields[parts[6]] = parts[6];
        end
      end
      
    end
  end

  puts "Rejects = " + rejects.to_s;
  puts "Total unique fields " + $uniqueHash.length.to_s;
  return csv;

end

# -d <num days ago> process x number of days ago
if(ARGV.length == 2 && ARGV[0].eql?("-d"))
  minusDays = ARGV[1].to_i;
  dt = DateTime.now() - minusDays;
  dateString = dt.strftime("%Y-%m-%d");
  #puts dateString;

  f = $DATADIR + dateString;
  parts = f.split('/');
  $year = parts[-1].split('-')[0];
  $month = parts[-1].split('-')[1];
  $day = parts[-1].split('-')[2];
  #puts f;
  $uniqueHash = Hash.new();
  csv = toCSV(f);
  filename = "/home/sonata/sensors/" + $year.to_s + "_" + $month.to_s + "_" + $day + "_" + "sensors.csv";
  File.open(filename, 'w') { |file| file.write(csv) };
  cmd =  "echo \"LOAD DATA LOCAL INFILE '#{filename}' INTO TABLE ants.#{$TABLENAME} FIELDS TERMINATED BY ',';\" | mysql ants";
puts cmd;
  `#{cmd}`;
  exit(0);

end

# table <name> specified, print out the create table command
if(ARGV.length == 2 && (ARGV[0].start_with?("table")))
  items = getItems($DATADIR + ARGV[1]);
  sql = "CREATE TABLE #{$TABLENAME}\n";
  sql += "(\n";
  sql += "  id INT UNSIGNED AUTO_INCREMENT,\n";
  sql += "  ts DATETIME NOT NULL,\n";
  sql += "  ant VARCHAR(3) NOT NULL,\n";
  sql += "  state TINYINT NOT NULL DEFAULT '0',\n";
  items.each_key do |i|
    sql += "  #{i} FLOAT DEFAULT -99.0,\n";
    puts i;
  end
  sql += "  CONSTRAINT ANT_DATE PRIMARY KEY (ant,ts)";
  sql += "  INDEX ANT_DATE PRIMARY KEY (ant,ts)";
  sql += ");";
  puts sql;
  exit(0);
end

# all is specified, will do all dates
if(ARGV.length == 1 && (ARGV[0].start_with?("all")))
  filenames = getFileList();
  filenames.each do |f|
    if(f.include?("test")) then next; end
    parts = f.split('/');
    $year = parts[-1].split('-')[0];
    $month = parts[-1].split('-')[1];
    $day = parts[-1].split('-')[2];
    puts f;
    $uniqueHash = Hash.new();
    csv = toCSV(f);
    filename = "/home/sonata/sensors/" + $year.to_s + "_" + "sensors.csv";
    File.open(filename, 'w') { |file| file.write(csv) };
    cmd =  "echo \"LOAD DATA LOCAL INFILE '#{filename}' INTO TABLE ants.#{$TABLENAME} FIELDS TERMINATED BY ',';\" | mysql ants";
    `#{cmd}`;
  end
  exit(0);
end

# The date is specified
if(ARGV.length == 1) 
  f = $DATADIR + ARGV[0];
  #sql = toCSV($DATADIR + ARGV[0]);
  parts = f.split('/');
  $year = parts[-1].split('-')[0];
  $month = parts[-1].split('-')[1];
  $day = parts[-1].split('-')[2];
  #puts f;
  $uniqueHash = Hash.new();
  csv = toCSV(f);
  filename = "/home/sonata/sensors/" + $year.to_s + "_" + $month.to_s + "_" + $day + "_" + "sensors.csv";
  File.open(filename, 'w') { |file| file.write(csv) };
  cmd =  "echo \"LOAD DATA LOCAL INFILE '#{filename}' INTO TABLE ants.#{$TABLENAME} FIELDS TERMINATED BY ',';\" | mysql ants";
   puts cmd;
  `#{cmd}`;
#  `rm #{filename}`;
  exit(0);
end
