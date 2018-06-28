#!/usr/bin/env ruby

# db2sql.rb
# Converts the various_sensors and feed_sensors table data (the MySQL "ants" database)
# to JSON and copies it to vaious servers.
#
# This script must be run on a computer that has access to the ants database.
#
# Jon Richards
# SETI Institute
# June 28, 2018

require 'time'
require 'date'
require 'thread'

$LOCK  = Mutex.new;

$TABLES = [ "various_sensors", "feed_sensors"];

def runDbCmd(cmd)
  parts = [];
  # mysql queries will have no header and no |, but may have tabs
  `echo \"#{cmd}\" | mysql -sN ants`.each_line do |line|
     parts << line.gsub("\t"," ").strip().split(/\s+/);
  end
  return parts;
end

def getYearsInTable(tableName) 

  result = [];
  cmd = "select distinct YEAR(ts) from #{tableName}";
  runDbCmd(cmd).each do |d|
    result << d[0].to_s;
  end
  return result;

end
  
def getAntsInTable(tableName) 

  result = [];
  cmd = "select distinct ant from #{tableName}";
  runDbCmd(cmd).each do |d|
    result << d[0];
  end
  return result;
  
end

def getTableNumericFieldNames(tableName)

  result = [];
  cmd = "describe #{tableName}";
  runDbCmd(cmd).each do |d|
    if(d[1].downcase().eql?("float") || d[1].downcase().eql?("int"))
      result << d[0];
    end
  end
  return result;
  
end

def getTableValues(tableName, years, ants, fieldNames)

  results = Hash.new();

  ants.each do |a|

    antResults = Hash.new();

    years.each do |y|

      avg = Hash.new();
      min = Hash.new();
      max = Hash.new();
    
      #cmd = "SELECT ant, WEEK(ts), ";
      cmd = "SELECT "
#i = 0;
      fieldNames.each do |f|
       cmd += "AVG (#{f}), MIN(#{f}), MAX(#{f}),";
       avg[f] = [];
       min[f] = [];
       max[f] = [];
      end
      cmd.chop!;
      cmd += " FROM #{tableName} where YEAR(ts)=#{y} AND ant='#{a}'  GROUP BY ant, WEEK(ts), YEAR(ts)";
      #puts cmd;
      dbRows = runDbCmd(cmd);
      dbRows.each_with_index do |row|
        index = 0;
        fieldNames.each do |fieldname|
          avg[fieldname] << row[index*3].to_f.round(2);
          min[fieldname] << row[index*3+1].to_f.round(2);
          max[fieldname] << row[index*3+2].to_f.round(2);
          index = index + 1;
        end
      end

      v = Hash.new();
      fieldNames.each do |f|
        v[f] = { "avg" => avg[f], "min" => min[f], "max" => max[f]};
      end
      antResults[y.to_i] = v;

    end

    results[a] =  antResults;

  end

  #puts results.to_s;
  return results;
end

results = Hash.new();

results["tables"] = $TABLES;

$TABLES.each do |tableName|

  years = getYearsInTable(tableName);
  ants = getAntsInTable(tableName);
  fieldNames = getTableNumericFieldNames(tableName);
  values = getTableValues(tableName, years, ants, fieldNames);

  data = Hash.new();
  data["years"] = years;
  data["ants"] = ants;
  data["fields"] = fieldNames;
  data["values"] = values;

  results[tableName] = data;

end

s =  "sensor_data(" + results.to_s + ")";

File.write('./ant_sensors.jsonp', s);

cmd = "scp ./ant_sensors.jsonp setiquest@setiquest.info:feeds/ant_sensors.jsonp";
puts cmd;
`#{cmd}`;

