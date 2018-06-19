# Feed sensor utilities

These utilities aid in gathering sensor data from the dishes and new Antonio Feeds.

## sensors.rb

Reads the historical sensor data, crams it into the database
This script is typically run once a day to load the previous day's data.
Data obtained by "ssh atasys@sonata ls -l /home/obs/archive/tempmon/june08/20*"

## feedmon.rb

Queries new Antonio feeds for all their sensor data. 
THis script resides on ataant@antcntl.
The data gets stored IN A MYSQL database on sonata1. 
All new feeds are queried at the same time, each in its own thread. The results are collated into a CVS text file suitable for the MYSQL LOAD function.  Once the file is complete it is copied to the sonata1 computer and ingested with the feed_sensors_load.rb script that resides on sonata1.
This script is kicked off periodically as a cron job.
NOTE: the sonata1 computer is 10.1.49.80


## feed_sensors_load.rb

Called by feedmon.rb to issue the LOAD mysql command to ingest the feed sensor data.

