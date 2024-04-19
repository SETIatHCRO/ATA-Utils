#!/bin/bash -x

export GPG_TTY=$(tty)
gpg -d ~/TerminatorObservationConsole/.sonata.password.gpg >/dev/null || exit 1
ssh-add -t 300 || exit 2
nohup terminator --config ~/hcro/terminator/terminator_config_HCRO --layout HCROOBS --profile=HCRO
