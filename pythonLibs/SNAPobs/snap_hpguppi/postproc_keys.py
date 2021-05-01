import redis
from string import Template
from . import snap_hpguppi_defaults as hpguppi_defaults

def set_keys(redis_set_channels, dry_run=False,
                POSTPROC='rawspec turboseti candidate_filter log rm',
                PPRWSINP='hpguppi',
                PPRWSENV='CUDA_VISIBLE_DEVICES:$inst$',
                PPRWSARG='-f 116480 -t 2 -I 1.0 -d /mnt/buf$inst$/rawspec/$stem$/',
                PPTBSINP='rawspec',
                PPTBSENV='CUDA_VISIBLE_DEVICES:$inst$',
                PPTBSARG='-M 20 -g n -p 12 -n 1440 -o /mnt/buf$inst$/turboseti/$stem$/',
                PPCNDINP='turboseti ^turboseti',
                PPCNDARG='-r 1 -s 10 -o auto -n bla',
                PPRMINP='hpguppi &*.raw,^turboseti &*.fil,turboseti &*.h5',
                PPLOGINP='*candidate_filter',
                PPLOGARG='-H $hnme$ -i $inst$ -s $stem$ -b $beg$ -e $end$',
                cmd_prefix=''
                ):

    r = redis.Redis(host=hpguppi_defaults.REDISHOST)
    for channel in redis_set_channels:
        cmd = cmd_prefix
        # Specify the 'postproc_*' names of the modules to be run in the post-processing, in order
        cmd += 'POSTPROC=' + POSTPROC + '\n'

        # Specify that the input of rawspec (RWS) is the output of hpguppi
        cmd += 'PPRWSINP=' + PPRWSINP + '\n'
        # Specify the environment variables of the rawspec command
        cmd += 'PPRWSENV=' + PPRWSENV + '\n'
        # Specify the static arguments of rawspec
        cmd += 'PPRWSARG=' + PPRWSARG + '\n'

        # Specify that the input of turboSETI (TBS) is the output of rawspec
        cmd += 'PPTBSINP=' + PPTBSINP + '\n'
        # Specify the environment variables of the turboSETI command
        cmd += 'PPTBSENV=' + PPTBSENV + '\n'
        # Specify the static arguments of turboSETI
        cmd += 'PPTBSARG=' + PPTBSARG + '\n'

        # Specify that the input of candidate_filter (CND) is the output of turboseti and the input of turboseti
        cmd += 'PPCNDINP=' + PPCNDINP + '\n'
        cmd += 'PPCNDARG=' + PPCNDARG + '\n'

        # Specify that the input of rm (RM) is the output of hpguppi
        cmd += 'PPRMINP=' + PPRMINP + '\n'

        cmd += 'PPLOGINP=' + PPLOGINP + '\n'
        cmd += 'PPLOGARG=' + PPLOGARG + '\n'

        print(channel, '\n\t', cmd.replace('\n', '\n\t').replace('=', '\t=\t'))

        if not dry_run:
            r.publish(channel, cmd)
        else:
            print('***Dry Run***')