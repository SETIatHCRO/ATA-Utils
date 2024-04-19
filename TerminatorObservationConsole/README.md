# Terminator HCRO Observation Console

Uses the "terminator" terminal multiplexer to group all the terminals needed for the ATA observations in a single organized window.

## Installation instructions:
### 1: install terminator
Install terminator with `apt` on Debian-based Linux systems:

```
sudo apt update
sudo apt install terminator
```

### 2: Copy the repository directory "TerminatorObservationConsole" in the user's home directory


### 3: Create an encrypted file to store the sonata password
Replace SONATA_PASSWORD with the sonata password below, keep the double quotes
```
export GPG_TTY=$(tty) ; eval $(gpg-agent --daemon)
echo "SONATA_PASSWORD" | gpg -c > ~/TerminatorObservationConsole/.sonata.password.gpg
```
A window will open and ask you to enter the password for the file encryption.

Note: This will allow terminator to decrypt the file on startup and use the sonata password to start all the terminals automatically. With this method, the user only needs to enter the sonata password once.


### 4: Create a custor command to start the terminator window
add the following line at the end of the user's "~/.bashrc" file:
```
alias HCRO_observation='~/TerminatorObservationConsole/HCRO_OBS_launch.sh'
```

## Usage:
To open the terminator window on obs-node1, simply write the following in a terminal:
```
HCRO_term
```


### Test:
Before deployment on obs-node1, this software can be tested on a local machine that is connected to the HCRO network. Follow the install steps locally and use:
```
HCRO_term --remote
```
*Warning:* This feature is only for testing purposes. Never observe from a local machine and always connect to the VNC session.



## Files description:
*`terminator_HCRO_launch.sh`: Bash script launching automatically terminator window
*`terminator_config_HCRO` contains the terminator config that can be run on obs-node1
*`terminator_config_HCRO_remote` contains the terminator config that can be run on any laptop (also ssh the right terminals to obs-node1)
*`.sonata.password.gpg` contains the gpg-encrypted sonata password
*`scripts` folder contains the scripts that terminator uses to automatically ssh to the right places.

