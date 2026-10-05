Beamforming Survey GUI README

This Graphical User Interface is meant to make observations more accessible and user-friendly.
If there are any issues, bugs, or comments for improvement, please reach out to Blayne Griffin at bgriffin@seti.org.

=====================================================================
            GUI OBSERVATION GUIDE (OPERATOR QUICK START)
=====================================================================

Before You Start
- Make sure you're registered as the Observer in Charge and properly calibrated.
- Confirm you're using the correct backend. This survey code is designed for BEAMFORMING mode.
- In the Configuration panel, use Browse to select your project folder.
- IMPORTANT: set your project folder first, or files may get written somewhere unexpected.

Folder Organization
- "rfsoc_obs_scripts/" is the parent folder.
- "survey_gui_code/" contains the GUI, observing script, utilities, and defaults.
- Your project folder (for example "p068" or "ASP") should also live within "rfsoc_obs_scripts/".
- Select that project folder as Project Name in the GUI.
- The scripts will create these folders inside your project automatically:
    - "<project>_working/" for active run files and current terminal output
    - "<project>_archive/" for timestamped archived files from each run
    - "<project>_ephemerides/" for generated solar-system ephemeris files

For CSVs
- Subject to personal preference, you can either have one csv contain all the information (coords + observed flag) or separate.
- Please ensure that you follow the guideline for syntax, otherwise the system may break. If it breaks, reach out to Sofia Sheikh and/or Blayne Griffin

CSV Requirements
Target List CSV format:
ID | Plaintext Name | Horizons Name | Solar System Flag | RA (hours) | DEC | RA (deg)

Observed List CSV format:
ID | Plaintext Name | Solar System Flag | cfreq_1336mhz | cfreq_####mhz...

- For Solsys Flag, "1" means in the solar system and "0" means outside it.
- For observed frequency columns, "0" means unobserved and "1" means observed.
- Keep required columns exactly as shown; add any optional columns to the right.
- The target and observed lists can be the same CSV or separate CSVs.
- The #### of the cfreq column is the center frequency the ATA is set to for a given tuning. Make sure it is exactly accurate.

Example:
ID,Plaintext Name,Horizons Name,Simbad Name,Solar System Flag,RA (hours),DEC,RA (deg),Phylum,Samples,cfreq_1336mhz,cfreq_2008mhz,cfreq_4536mhz,cfreq_8336mhz
1,446 Aeternitas,446 Aeternitas (A899 UB),,1,,,,MinorBody,P,1,1,1,1
72,tau Cet,,tau Cet,0,1.7344722,-15.9375,26.017083,MinorBody+Star,P,1,1,1,1

If you wish to use a custom observation time per target, bouncing between science target and calibrator as an example, that is possible.
To do this, add a column titled "Obs Time" and input the given time in seconds.
Ensure both for this and for anything else that each entry has a unique ID code, even if it's the same target multiple times.

=====================================================================
Running an Observation from the GUI
1) Launch the GUI. (python /home/sonata/rfsoc_obs_scripts/beamforming_gui_code/beamforming_gui.py)
2) Set project folder first.
3) Select target list CSV and observed list CSV. These can be the same or different csv files.
4) Set observation time per target (default: 300 seconds = 5 minutes).
5) Press "Refresh from Notion" to load antenna status.
6) Review antenna checkboxes and uncheck antennas to exclude.
7) Choose options in the Options panel.
8) (Optional) Open Advanced Options to set ODS behavior, scheduled stops, and per-target Obs Time mode.
9) Press "Run".
=====================================================================

Stopping Behavior
- Request Stop: graceful stop at the earliest possible convenience. Will allow a scan to finish before ending.
- Resume: clears a pending stop request and keeps observing.
- Abort: immediate hard stop and GUI shutdown. Use only in emergencies.

Options Guide
- Record Data: enables ATA data recording.
- Mark Target as Observed: updates observed frequency fields after successful scan.
- Sort by Observed List: Whether or not you care about using an observed list csv.
- Dynamic LST Refresh: Rebuilds the working target order during the run to find the Most Vertical target. If False, it uses the given CSV order and doesn't rearrange.
- Testing Mode: Avoids ATA-only control paths and uses test-safe behavior. On every run by default and must be disabled. Done this way to protect the ATA.

Advanced Options Guide
- Scheduled Starts and Stops:
    - Start/Stop After: Values like "8 hours", "1.5 hours", "90m", or raw seconds.
    - Start/Stop At: HH:MM:SS in 24-hour format plus timezone text.
    - Clear Scheduled Start/Stop: Removes any pending schedule.
    - Only one mode of start or stop can exist at a time, as in you can't both start AT and start AFTER XX time.
- Dynamic Observation Time:
    - When enabled, per-target scan time is read from an "Obs Time" column when valid.
    - When disabled (or invalid/missing values), the global OBS_TIME is used.
- ODS Controls:
    - Wait for ODS: waits before first observation so protection can activate (30 minutes).
    - Push ODS: enables/disables ODS reservation pushing entirely.

Notion + Antenna Source Behavior
- "Refresh from Notion" updates antenna state using the Dish Status Notion table.
- If Notion is unavailable and TESTING is enabled, the GUI falls back to default antennas.
- If Notion fails and TESTING is disabled, SNAPobs fallback is used.
- If that fallback fails too, startup is blocked with a warning.

