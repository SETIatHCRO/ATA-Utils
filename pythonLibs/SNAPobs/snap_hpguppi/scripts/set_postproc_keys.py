#!/home/sonata/miniconda3/bin/python
import argparse
import socket
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary
from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults

if __name__ == "__main__":
        parser = argparse.ArgumentParser(description='Set the post-processing key-values for a Hashpipe instance.')
        parser.add_argument('-d', action='store_true',
                help='dry run (don\'t publish)')
        parser.add_argument('-i', type=str, default='-1',
                help='hashpipe instance id to target [-1: for broadcast]')
        parser.add_argument('-I', type=str, default=None,
                help='hashpipe instance hostname to target [$hostname]')

        parser.add_argument('--POSTPROC', type=str, default='rawspec turboseti candidate_filter log cp rm',
                help='Set the value for the POSTPROC key [\'rawspec turboseti candidate_filter log cp rm\']')
        parser.add_argument('--PPRWSINP', type=str, default='hpguppi',
                help='Set the value for the PPRWSINP key [\'hpguppi\']')
        parser.add_argument('--PPRWSENV', type=str, default='CUDA_VISIBLE_DEVICES:$inst$',
                help='Set the value for the PPRWSENV key [\'CUDA_VISIBLE_DEVICES:$inst$\']')
        parser.add_argument('--PPRWSARG', type=str, default='-f 116480 -t 2 -I 1.0 -d /mnt/buf$inst$/rawspec/$stem$/',
                help='Set the value for the PPRWSARG key [\'-f 116480 -t 2 -I 1.0 -d /mnt/buf$inst$/rawspec/$stem$/\']')
        parser.add_argument('--PPTBSINP', type=str, default='rawspec',
                help='Set the value for the PPTBSINP key [\'rawspec\']')
        parser.add_argument('--PPTBSENV', type=str, default='CUDA_VISIBLE_DEVICES:$inst$',
                help='Set the value for the PPTBSENV key [\'CUDA_VISIBLE_DEVICES:$inst$\']')
        parser.add_argument('--PPTBSARG', type=str, default='-M 10 -g y -p 12 -n 1440 -o /mnt/buf$inst$/turboseti/$stem$/',
                help='Set the value for the PPTBSARG key [\'-M 10 -g y -p 12 -n 1440 -o /mnt/buf$inst$/turboseti/$stem$/\']')
        parser.add_argument('--PPCNDINP', type=str, default='turboseti ^turboseti',
                help='Set the value for the PPCNDINP key [\'turboseti ^turboseti\']')
        parser.add_argument('--PPCNDARG', type=str, default='-r 1 -s 10 -o auto -n bla',
                help='Set the value for the PPCNDARG key [\'-r 1 -s 10 -o auto -n bla\']')
        parser.add_argument('--PPLOGINP', type=str, default='*candidate_filter',
                help='Set the value for the PPLOGINP key [\'*candidate_filter\']')
        parser.add_argument('--PPLOGARG', type=str, default='-H $hnme$ -i $inst$ -s $stem$ -b $beg$ -e $end$',
                help='Set the value for the PPLOGARG key [\'-H $hnme$ -i $inst$ -s $stem$ -b $beg$ -e $end$\']')
        parser.add_argument('--PPRMINP', type=str, default='hpguppi &*.raw,^turboseti &*.fil,turboseti &*.h5',
                help='Set the value for the PPRMINP key [\'hpguppi &*.raw,^turboseti &*.fil,turboseti &*.h5\']')
        parser.add_argument('--PPCPINP', type=str, default='rawspec',
                help='Set the value for the PPCPINP key [\'rawspec\']')
        parser.add_argument('--PPCPARG', type=str, default='/mnt/datax-netStorage-40G/dmpauto-$hnme$.$inst$/$stem$/',
                help='Set the value for the PPCPARG key [\'/mnt/datax-netStorage-40G/dmpauto-$hnme$.$inst$/$stem$/\']')
        parser.add_argument('--prefix', type=str, nargs='?', default=[],
                help='Specify additional key=value strings')
        args = parser.parse_args()


        instances = args.i.split(',')
        hostnames = args.I.split(',') if args.I is not None else [socket.gethostname()]

        channels =[]
        for hostname in hostnames:
                for instance in instances:

                        try:
                                instance = int(instance)
                        except:
                                print('Instance {} is not an integer.'.format(instance))
                                exit(1)


                        if instance > -1:
                                print('Setting key-values on instance', instance)

                                channels.append(hpguppi_defaults.REDISSETGW.substitute(host=hostname, inst=instance))
                        else:
                                print('Broadcasting the key-values')
                                channels.append(hpguppi_defaults.REDISSET)

        keyval_dict = {
                'POSTPROC':args.POSTPROC,
                'PPRWSINP':args.PPRWSINP,
                'PPRWSENV':args.PPRWSENV,
                'PPRWSARG':args.PPRWSARG,
                'PPTBSINP':args.PPTBSINP,
                'PPTBSENV':args.PPTBSENV,
                'PPTBSARG':args.PPTBSARG,
                'PPCNDINP':args.PPCNDINP,
                'PPCNDARG':args.PPCNDARG,
                'PPLOGINP':args.PPLOGINP,
                'PPLOGARG':args.PPLOGARG,
                'PPCPINP':args.PPCPINP,
                'PPCPARG':args.PPCPARG,
                'PPRMINP':args.PPRMINP,
        }
        for key_value_str in args.prefix:
                key_value = key_value_str.split('=')
                keyval_dict[key_value[0]] = key_value[1]

        redis_publish_command = hpguppi_auxillary.redis_publish_command_from_dict(keyval_dict)
        print(redis_publish_command)
        if args.d:
                print('*** Dry Run ***')
        else:
                print('Publishing to:')
                for channel in channels:
                        print('\t', channel)
                        hpguppi_defaults.redis_obj.publish(channel, redis_publish_command)
