#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys, os.path, logging
from optparse import OptionParser

from twisted.internet import reactor, defer

pname=os.path.basename(sys.argv[0])

act='get'
if pname.startswith('arinfo'):
    act='info'
elif pname.startswith('argrep'):
    act='grep'
elif pname.startswith('arget'):
    act='get'
elif pname.startswith('arh5export'):
    act='h5export'

par=OptionParser(
    usage='%prog [options] channel <channels ...>',
    description='Query the channel archiver'
    )

par.add_option('', '--helptime', action="store_true", default=False,
               help="Show help on date/time format")
par.add_option('-I','--info', action="store_true", default=False,
               help='Show archive server information')
par.add_option('-S','--search', action="store_true", default=False,
               help='Search for channels matching the given pattern(s)')
par.add_option('-G','--get', action="store_true", default=False,
               help='Retrieve data for given channels')
par.add_option('-E','--export', metavar='TYPE', default=None,
               help="Retrieve data and write to file in the given format (eg. hdf5)")

par.add_option('-u','--url', metavar='NAME or URL',
               help='Either a config key, host name, or full url for the server')
par.add_option('-s','--start', metavar='TIME',
               help='Start of query window (required)')
par.add_option('-e','--end', metavar='TIME', default=None,
               help='End of query window (defaults to current system time)')
par.add_option('-c','--count', metavar='NUM', default=10, type="int",
               help='Maximum number of samples to read. (10 = default, 0 = inf.)')
par.add_option('-a','--archive', metavar='NAME', action='append', default=[],
               help='Archive name.  Wildcards allowed.  Can be given more than once')
par.add_option('-H','--how', metavar='NAME', default='raw',
               help="Query method (eg. raw)")

par.add_option('-M','--merge', metavar='NAME', default='simple',
               help='How to attempt to combine data for one channel received in '
               'different responces.  Options: none, simple')

par.add_option('-v','--verbose', action='count', default=0,
               help='Print more')
par.add_option('-d','--debug', action='store_true', default=False,
               help='Show archiver queries')

opt, args = par.parse_args()

if opt.helptime:
    from carchive import date
    print date.__doc__
    sys.exit(0)

if opt.merge not in ['none','simple']:
    par.error('Invalid merge method %s'%opt.merge)


LVL={0:logging.WARN, 1:logging.INFO, 2:logging.DEBUG}

logging.basicConfig(format='%(message)s',level=LVL.get(opt.verbose, LVL[2]))

from carchive import getArchive
from carchive._conf import _conf as conf

if opt.url:
    conf.set('DEFAULT', 'url', opt.url)

if len(opt.archive)==0:
    if conf.has_option('DEFAULT', 'defaultarchs'):
        opt.archive = [conf.get('DEFAULT', 'defaultarchs')]
    else:
        opt.archive = ['*']

if opt.info:
    act='info'
elif opt.search:
    act='grep'
elif opt.get:
    act='get'
elif opt.export=='hdf5':
    act='h5export'

@defer.inlineCallbacks
def haveArchive(act, opt, args, conf):

    if opt.verbose>0:
        print 'Command:',act

    mod = __import__('carchive.cmd', fromlist=[act])
    mod = getattr(mod, act)

    serv = yield getArchive(conf=conf)    
    
    done = mod.cmd(action=act, archive=serv,
                   opt=opt, args=args,
                   conf=conf)

    try:
        yield done
    finally:
        reactor.stop()

reactor.callWhenRunning(haveArchive, act, opt, args, conf)

reactor.run()

sys.exit(0)

#elif act=='get':
#    if len(args)==0:
#        par.error('No channel to query')
#    elif opt.how not in serv.how:
#        par.error("How %s is invalid.  Use one of %s"%(opt.how, ', '.join(serv.how)))
#    elif not opt.start:
#        par.error("Start time is required")
#
#    Q=serv.Q().set(names=args, patterns=True, archs=archs)
#    Q.how=opt.how
#    Q.count=opt.count
#    Q.start=opt.start
#    if opt.end:
#        Q.end=opt.end
#
#    for ch, ranges in Q.execute().iteritems():
#        print ch
#        if opt.merge=='simple':
#            ranges=data.simpleMerge(ranges, Q.start, Q.end)
#        for d in ranges:
#            print '==='
#            d.pPrint()
#
#else:
#    par.error('Unkown action: %s'%act)
