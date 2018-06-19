#!/usr/bin/env ruby

require 'time'
require 'date'
require 'thread'

$LOCK  = Mutex.new;

$ANTS = ['1c', '1e', '1g', '1h', '1k', '2a', '2b', '2e', '2h', '2j', '2m', '3c', '3d', '3l', '4j', '5b'];

$HOST = "sonata@10.1.49.80";
#$ANTS = ['1e', '1h', '1k', '2a', '2b', '2e', '2h', '2j', '2m', '3c', '3d', '3l', '4j'];
#$ANTS = ['1e', '1c'];

$ITEMS = [
[ "fanpwm", "getfanpwm", "Fan power. ( % on time ) ( pulse width modulation )", 1, 2],
[ "fanspeed", "getfanspeed", "Current fan speed. ( rpm ) ( 3000 rpm max speed )", 1, 1 ],
[ "cryoattemp", "getcryoattemp", "Regulating Display Cooler State, at setpoint temp. ( yes, no ) ( cooler pin 4 )( 5V=yes)", 1, 2 ],
[ "controlboardtemp", "gettemp a0", "Display temperature, on control board. ( °C ) ( near ambient )", 1, 1 ],
[ "outsideairtemp", "gettemp a1", "Display temperature, Outside air. ( °C ) ( lower vent from amb )", 1, 1 ],
[ "paxairtemp", "gettemp a2", "27.8 Display temperature, PAX air. ( °C ) ( PAX case exit air )", 1, 1 ],
[ "exhausttemp", "gettemp a3", "Temperature, Exhaust air. ( °C ) ( to amb ) ( a4 not used )", 1, 1 ],
[ "coolerrejectiontemp", "gettemp a5", "Temperature, Cooler rejection. ( °C ) ( near to fins )", 1, 1 ],
[ "coolerhousingtemp", "gettemp a6", "Temperature, Cooler housing. ( °C ) ( back of housing )( 70 C max )", 1, 1 ],
[ "lnatemp", "gd",  "LNA temperature. ( Kelvin ) ( uses equation to calculate )", 1, 1 ],
[ "lnadiodevoltage", "gd -v", "LNA diode voltage. ( _-v gives )( volts x.xxx )", 1, 1 ],
[ "accel", "getaccel", "Accelerometer data in a 3 x 4 matrix. since last call. ( g ) 3 rows, X, Y, Z, and 4 columns, min, mean, stddev, max.", 1, 1 ],
[ "relaystate", "getrelay", "Relay state", 1, 2 ],
[ "feedstartmode", "getfeedstartmode",  "Manual or auto feed start mode.", 1, 2 ],
[ "cryotempregulating", "getcryoattemp Y", "Regulating cryo temp.", 1, 2 ],
[ "cryotempnoregulating", "getcryoattemp N", "Non regulating cryo temp.", 1, 2 ],
[ "vdc24volt", "get24v",  "24 VDC actual measured.", 1, 1 ],
[ "errormessages", "p303", "error messages, ( also use p360 to p369 for history )", 2, 2 ],
[ "displayexcesstemp", "p304", "Excess Temp Electronics. ( 0 = no, 1 = yes )", 2, 3 ],
[ "excesstempturbo", "p305",  "Excess Temp Turbo. ( 0 = no, 1 = yes )", 2, 3 ],
[ "turbocurrrent", "p310",  "Turbo current consumption. ( amps ) ( 000183 = 1.83 ) ( data T2 )", 2, 3 ],
[ "ophours", "p311", "Station operation ( hours )( 0 to 65535 )", 2 , 3],
[ "turbospeednominal", "p315", "Turbo speed, nominal. ( Hz ) ( 1500 Hz = 90,000 rpm )( x6 )", 2, 3 ],
[ "turbopower", "p316", "Turbo power consumption. ( watts )( 77 max )( 14 good )", 2, 3 ],
[ "electronicsboardtemp", "p326",  "Electronics control board temperature. ( °C xx.x ) ( tenths ? )", 2, 3 ],
[ "turbobottomtemp", "p330", "Turbo bottom temperature. ( °C) ( most sensitive to fan )", 2, 3 ],
[ "turbobearingtemp", "p342", "Turbo bearing temperature. ( °C) ( no tenths from Pfeiffer )", 2, 3 ],
[ "turbomotortemp", "p346", "Turbo motor temperature. ( °C ) ( error 117 ) ( 100 is hot )", 2, 3 ],
[ "turbospeedactual", "p398", "Turbo speed, actual. ( rpm )( 90,000 nom )( 90,600 bad, reset p023 )", 2, 3 ] ];
# Don't ask for the vdc48volt, it is always 0.0
#[ "vdc48volt", "get48v",  "48 VDC actual measured. ( not connected )", 1, 1 ],
#vacuumgaugevoltage does not work
#[ "vacuumgaugevoltage", "getvac", "Vacuum gauge. ( mbar )( equation )( if gauge is present )", 1, 1 ],
# Don't ask for the error (we can figure them out oursleves), and guagepressure does not work.
#[ "guagepressure", "p340",  "Pressure from gauge. ( mbar )( only Pfeiffer DCU ) ( p738 gauge type )", 2, 1 ],
#[ "errorhist1", "P360",  "Error History, position 1", 2, 2 ],
#[ "errorhist2", "P361",  "Error History, position 2", 2, 2 ],
#[ "errorhist3", "P362",  "Error History, position 3", 2, 2 ]];

$results = [];

if(ARGV.length == 1 && ARGV[0].eql?("list"))
  if(ARGV.length == 1 && ARGV[0].eql?("list"))

    puts "Feed Control Board items: ";
    $ITEMS.each do |item|
      if(item[3] == 1)
        puts "#{item[1]} \t #{item[2]}";
      end
    end
    puts "Vacuum Controller items: ";
    $ITEMS.each do |item|
      if(item[3] == 2)
        puts "#{item[1]} \t #{item[2]}";
      end
    end
  end
  exit(0);
end

if(ARGV.length == 1 && (ARGV[0].start_with?("table")))
  sql = "CREATE TABLE feed_sensors\n";
  sql += "(\n";
  #sql += "  id INT UNSIGNED AUTO_INCREMENT,\n";
  sql += "  ts DATETIME NOT NULL,\n";
  sql += "  ant VARCHAR(3) NOT NULL,\n";
  sql += "  state TINYINT NOT NULL DEFAULT '0',\n";
  $ITEMS.each do |i|
    if(i[0].eql?("accel"))
      sql += "  accelminx FLOAT DEFAULT -99.0,\n";
      sql += "  accelmeanx FLOAT DEFAULT -99.0,\n";
      sql += "  accelstdx FLOAT DEFAULT -99.0,\n";
      sql += "  accelmaxx FLOAT DEFAULT -99.0,\n";
      sql += "  accelminy FLOAT DEFAULT -99.0,\n";
      sql += "  accelmeany FLOAT DEFAULT -99.0,\n";
      sql += "  accelstdy FLOAT DEFAULT -99.0,\n";
      sql += "  accelmaxy FLOAT DEFAULT -99.0,\n";
      sql += "  accelminz FLOAT DEFAULT -99.0,\n";
      sql += "  accelmeanz FLOAT DEFAULT -99.0,\n";
      sql += "  accelstdz FLOAT DEFAULT -99.0,\n";
      sql += "  accelmaxz FLOAT DEFAULT -99.0,\n";
    elsif(i[4] == 2)
      sql += "  #{i[0]} VARCHAR(8) DEFAULT NULL,\n";
    elsif(i[4] == 3)
      sql += "  #{i[0]} int DEFAULT -99,\n";
    else
      sql += "  #{i[0]} FLOAT DEFAULT -99.0,\n";
    end
    #puts i;
  end
  sql += "  CONSTRAINT ANT_DATE PRIMARY KEY (ant,ts)\n";
  sql += ");";
  puts sql;
  puts "CREATE INDEX idx on feed_sensors(ant,ts);";
  exit(0);
end

# If we get this far, then query the ants
items = [];
$ITEMS.each do |item|
  items << item[1];
  #puts "#{item[1]}";
end

#ssh 1e netcat -v -i 2 rimbox 1518 < test.txt  | sed -e "s/\r/\r\n/g" 
File.open("test.txt", "w") do |f|
  f.puts(items)
end

def doFeed(ant, timestamp)
  cmd = 'ssh ' +  ant  + ' netcat -v -i 2 rimbox 1518 < test.txt | sed -e "s/\r/\r\n/g"';
puts cmd;
  result = `#{cmd}`;

  if(result.include?("Connection timed out"))
    #return "'" + timestamp + "','" + ant + "',0"; # Specify state = not good
    return "" + timestamp + "," + ant + ",0"; # Specify state = not good
  end

  i = 0;
  #csv = "'" + timestamp + "','" + ant + "',1";
  csv = "" + timestamp + "," + ant + ",1";
  result.each_line do |val|
    puts "[" + ant + "]" + $ITEMS[i][0] + " = " + val;
    if($ITEMS[i][0].eql?("accel"))
      #-0.410  -0.117   0.052   0.136| 0.750   1.022   0.082   1.360|-0.786  -0.001   0.413   0.846
      parts = val.chomp.gsub("|", " ").split(/\s+/);
      parts.each do |a|
        if(val.chomp.eql?("timeout"))
          csv += ",-99,-99,-99,-99,-99,-99,-99,-99,-99,-99,-99,-99";
        else
          csv += "," + a;
        end
      end
    elsif($ITEMS[i][4] == 2) #String
        if(val.chomp.eql?("timeout"))
          #csv += ",\'\'";
          csv += ",";
        else
          #csv += ",\'" + val.chomp + "\'";
          csv += "," + val.chomp + "";
        end
    else
      if(val.chomp.eql?("timeout"))
        csv += ",-99";
      else
        csv += "," + val.chomp;
      end
    end
    i = i + 1;
    #puts i.to_s;
  end

  #puts csv;

  $LOCK.synchronize {
    $results << csv;
  }

end

def count_commas(s) 
 num = s.count(",");
 return num.to_s;
end

numInGroup = $ANTS.length;
timestamp = Time.now.strftime('%Y-%m-%d %H:%M:%S');
(0...$ANTS.length).step(numInGroup) do |i|

  t = [];
puts "";
  (i...(i+numInGroup)).each  do |j|
    puts j.to_s;
    t << Thread.new{doFeed($ANTS[j], timestamp)};
  end

  t.each do |th|
    th.join();
  end

  File.open("feed_sensors.csv", "w") do |f|
    #f.puts(items)
    $results.each do |r|
      f.puts r;
    end
  end

end
#it1 = Thread.new{pointBF(1, $obsFreq1)};

#send the file
cmd = "scp ./feed_sensors.csv sonata@10.1.49.80:/home/sonata/ATA-Utils/FeedSensors";
puts cmd;
`#{cmd}`;

cmd = 'ssh sonata@10.1.49.80 "cd /home/sonata/ATA-Utils/FeedSensors; /home/sonata/ATA-Utils/FeedSensors/feed_sensors_load.rb"';
puts cmd;
`#{cmd}`;

puts "Finished";
