# Terminator HCRO Observation Console

Uses the "terminator" terminal multiplexer to group all the terminals needed for the ATA observations in a single organized window.

## Installation instructions:
### 1: install terminator
If not already on the system, install terminator and the expect interpreter with `apt` on Debian-based Linux systems:
```
sudo apt-get update
sudo apt-get install terminator
sudo apt-get install expect
```


### 2: Copy the repository directory "TerminatorObservationConsole" in the user's home directory
cp -r <PATH DOWNLOADED REPO>/TerminatorObservationConsole/ ~/


### 3: Create an encrypted file to store the sonata password
Replace SONATA_PASSWORD with the sonata password below, keep the double quotes
```
export GPG_TTY=$(tty) ; eval $(gpg-agent --daemon)
echo "SONATA_PASSWORD" | gpg -c > ~/TerminatorObservationConsole/.sonata.password.gpg
```
A window will open and ask you to enter the password for the file encryption.

Note: This will allow terminator to decrypt the file on startup and use the sonata password to start all the remote terminals automatically. With this method, the user only needs to enter the sonata password once.


### 4: Create a custor command to start the terminator window
add the following line in the user's "~/.bashrc" file:
```
alias HCRO_observation='~/TerminatorObservationConsole/HCRO_OBS_launch.sh'
```


### 5: Edit file permission:
Run the following to have the permission
```
chmod +x ~/TerminatorObservationConsole/HCRO_OBS_launch.sh
chmod +x ~/TerminatorObservationConsole/scripts/LOb.exp
chmod +x ~/TerminatorObservationConsole/scripts/LOc.exp
```


## Usage:
To open the terminator window on obs-node1, simply write the following in a terminal:
```
HCRO_observation
```

## Files description:
*`terminator_HCRO_launch.sh`: Bash script launching automatically terminator window \\
*`terminator_config_HCRO` contains the terminator config that can be run on obs-node1 \\
*`.sonata.password.gpg` contains the gpg-encrypted sonata password *Note:* Not on Github for security reasons, has to be generated at installation step 3. \\
*`scripts` folder contains the scripts that terminator uses to automatically ssh to the right places. \\

