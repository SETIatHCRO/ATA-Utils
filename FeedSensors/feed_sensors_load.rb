#!/usr/bin/env ruby

# feed_sensors_load.rb
# Jon Richards, SETI Institute
# June 19, 2018
#
# Simple script used to import the feed sensor data into the ants:feed_sensors mysql table.
# This script is called via ssh from anaant@antcntl to periodically load the latest new ant
# feed sensor data.

cmd =  "echo \"LOAD DATA LOCAL INFILE '/home/sonata/sensors/feed_sensors.csv' INTO TABLE ants.feed_sensors FIELDS TERMINATED BY ','\" | mysql ants";
puts cmd;
`#{cmd}`;

