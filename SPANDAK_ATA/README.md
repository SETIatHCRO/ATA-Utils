
# SPANDAK: Searching for Naturally and Artificially Dispersed Transient Signals for the Allen Telescope Array

SPANDAK is a GPU-accelerated, modular pipeline designed to detect **broadband dispersed transient signals** — including **naturally dispersed signals** from FRBs and those with **artificial or negative dispersion** from ETIs. It integrates classic time-domain algorithms with ML-based candidate validation.

This is a modified version of the code with specific changes adapted to work with the Allen Telescope Array, HCRO. 


---

## 🔧 Installation

Clone the repository:

git clone https://github.com/gajjarv/SPANDAK_ATA.git

Install required Python dependencies (TODO: requirements.txt) and ensure HEIMDALL is installed and working. 

The blockdiagram of pipeline is as follows. 
----- 

![SPANDAK](FRBsearching/images/SPANDAK_diag.png)

**To get help:**

SPANDAK -h

![Help](FRBsearching/images/Help.png)

**Examples:**
1. For simple dispersion search across 0 to 1000 DMs. 

SPANDAK --fil file.fil 

2. For artificially dispersed signal search across 0 to 2000 DMs. 

SPANDAK --fil file.fil --negDM --lodm 0 --hidm 2000
	
3. Searching with RFI flagging

SPANDAK --fil file.fil --dorfi
	
4. ML assisted candidate prioritization. 

SPANDAK --fil file.fil --ML saved_model.h5


----
Acknowledgement:

This pipeline is outlined in the following paper: 

Gajjar et al., Searching for broadband pulsed beacons from 1883 stars using neural networks, AJ, 2022

If you use SPANDAK, please cite the paper:

@article{Gajjar2022SPANDAK,
  title = {Searching for broadband pulsed beacons from 1883 stars using neural networks},
  author = {Gajjar, Vishal and et al.},
  journal = {Astronomical Journal},
  year = {2022}
}

-----------------------------------------------------------------------------------------------   
- Vishal Gajjar


For more information write to vishalg@berkeley.edu
------------------------------------------------------------------------------------------------
