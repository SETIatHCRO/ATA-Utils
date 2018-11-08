#!/usr/bin/env ruby

# feed_sensors_load.rb
# Jon Richards, SETI Institute
# June 19, 2018
#
# Simple script used to import the feed sensor data into the ants:feed_sensors mysql table.
# This script is called via ssh from anaant@antcntl to periodically load the latest new ant
# feed sensor data.
#
# Modified Nov 08, 2018 to load feed_sensors_short.csv into the ants.feed_sensors_short table.
#

if(File.file?("feed_sensors.csv"))
    cmd =  "echo \"LOAD DATA LOCAL INFILE '/home/sonata/ATA-Utils/FeedSensors/feed_sensors.csv' INTO TABLE ants.feed_sensors FIELDS TERMINATED BY ','\" | mysql ants";
    puts cmd;
    `#{cmd}`;
    cmd =  "echo \"LOAD DATA LOCAL INFILE '/home/sonata/ATA-Utils/FeedSensors/feed_sensors.csv' INTO TABLE ants.feed_sensors FIELDS TERMINATED BY ','\" | mysql -h googledb -u jrseti ants";
    puts cmd;
    `#{cmd}`;
    cmd = "rm feed_sensors.csv";
    `#{cmd}`;
end

if(File.file?("feed_sensors_short.csv"))
    cmd =  "echo \"LOAD DATA LOCAL INFILE '/home/sonata/ATA-Utils/FeedSensors/feed_sensors_short.csv' INTO TABLE ants.feed_sensors_short FIELDS TERMINATED BY ','\" | mysql ants";
    puts cmd;
    `#{cmd}`;
    cmd =  "echo \"LOAD DATA LOCAL INFILE '/home/sonata/ATA-Utils/FeedSensors/feed_sensors_short.csv' INTO TABLE ants.feed_sensors_short FIELDS TERMINATED BY ','\" | mysql -h googledb -u jrseti ants";
    puts cmd;
    `#{cmd}`;
    cmd = "rm feed_sensors_short.csv";
    `#{cmd}`;
end
