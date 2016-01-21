python arget -s "2006-11-10 21:30:00" -e "2014-11-10 21:35:00" --appliance-name appliance1 -E pbraw --export-granularity 1year --export-out-dir /home/deployer/pbraw
python arget -s "2006-11-10 21:30:00" -e "2014-11-10 22:35:00" --appliance-name appliance1 --export-granularity 1year --export-out-dir /home/deployer/pbraw
rsync -avm --include='*2011.pb' -f 'hide,! */' . /srv/epicsdata/conversion/dest/overlap_trash/2009
rsync -avm --include='*2012.pb' -f 'hide,! */' . /srv/epicsdata/conversion/dest/t2012
find . -name '*:2008.pb' -type f -delete
find . -type f -exec chmod a-x {} \;
