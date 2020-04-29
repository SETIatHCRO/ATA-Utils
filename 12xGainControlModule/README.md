# 12xGainControlModule

Contains software to control the attenuators in the 12 channel gain control module for use at the Allen Telescope Array.

## attenuatorMain.py

Python program to perform specific attenuations on selected attenuator(s).

## Technologies
* Python - version 3.6

## Setup
You can clone the repository and install the program from there directly. At the command line, run:  
`git clone https://github.com/SETIatHCRO/ATA-Utils`   
Then find the file where you've cloned this repository in, go into the file by typing  
`cd ATA-Utils
cd 12xGainControlModule`  
Install the program by typing:  
`python setup.py install`  

If you don't want the program installed, you can download the attenuatorMain.py file, and run the program directly on terminal by typing:  
`python attenuatorMain.py -[commands]`

## Usage
The program takes in arguments from the terminal directly. To get the most up-to-date functions available, run:  
`attenuatorMain -h`  
This will return a list of arguments that the program takes and specific instructions about input requirements

## Debug
The program provides logging for tracking usage and debugging. A log file called Attenuator.log will be automatically generated when the program is run. Access the log file directly for information.

## To-do list:
* Storing previously programmed values
* -initialize to initialize all attenuators from last programmed values
* arguments through TCP connection

## Acknowledgment
Alexander Pollak for credits of design and mentorship through the whole project
