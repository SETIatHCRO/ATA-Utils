#!/bin/bash

Help()
{
   # Display Help
   echo "Apply solutions unto the delay engine"
}

while getopts ":h" option; do
   case $option in
      h) # display Help
         Help
         exit;;
   esac
done

sudo cp ./delays_b.txt.new /opt/mnt/share/delays_b.txt
sudo cp ./delays_c.txt.new /opt/mnt/share/delays_c.txt

sudo cp ./phases_b.txt.new /opt/mnt/share/phases_b.txt
sudo cp ./phases_c.txt.new /opt/mnt/share/phases_c.txt

sudo cp ./weights_b.bin.new /opt/mnt/share/weights_b.bin
sudo cp ./weights_c.bin.new /opt/mnt/share/weights_c.bin

sudo cp ./weights_b.txt /opt/mnt/share/weights_b.txt
sudo cp ./weights_c.txt /opt/mnt/share/weights_c.txt



curl -F file=@./observation.png -F channels=C01HKMMQVUZ -H "Authorization: Bearer ${ATATOKEN}" https://slack.com/api/files.upload
curl -F file=@./calibration.png -F channels=C01HKMMQVUZ -H "Authorization: Bearer ${ATATOKEN}" https://slack.com/api/files.upload
echo ""
#rm observation.png
#rm calibration.png
