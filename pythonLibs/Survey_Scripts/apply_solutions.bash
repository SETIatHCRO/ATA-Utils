#!/bin/bash

sudo cp ./delays_b.txt.new /opt/mnt/share/delays_b.txt
sudo cp ./delays_c.txt.new /opt/mnt/share/delays_c.txt

sudo cp ./phases_b.txt.new /opt/mnt/share/phases_b.txt
sudo cp ./phases_c.txt.new /opt/mnt/share/phases_c.txt


#for png_name in `ls *.png`
#do
#    curl -F file=@./${png_name} -F channels=C01HKMMQVUZ -H "Authorization: Bearer ${ATATOKEN}" https://slack.com/api/files.upload
#    echo ${png_name}
#done

montage -geometry +30+30 -tile 2x2 *.png observation.png
curl -F file=@./observation.png -F channels=C01HKMMQVUZ -H "Authorization: Bearer ${ATATOKEN}" https://slack.com/api/files.upload
rm observation.png
