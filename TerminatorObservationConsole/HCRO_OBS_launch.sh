#!/bin/bash -x

export GPG_TTY=$(tty)
gpg -d ~/TerminatorObservationConsole/.sonata.password.gpg >/dev/null || exit 1
ssh-add -t 300
nohup terminator --config ~/TerminatorObservationConsole/terminator_config_HCRO --layout HCROOBS --profile=HCRO </dev/null &>/dev/null &

# Open atastatus page
nohup ssh obs@control.hcro.org 'atastatus' &

# Automatically open webpages relevant to HCRO observation
xhost +local:
nohup ~/TerminatorObservationConsole/scripts/webpages.sh


