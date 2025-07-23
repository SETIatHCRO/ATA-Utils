import os,sys
from parse import parse
from abc import ABC, abstractmethod
import time
import json
import redis
import datetime
import tkinter as tk

from ATATools import ata_control, logger_defaults, ata_if

from hashpipe_keyvalues import HashpipeKeyValues

from SNAPobs.snap_hpguppi import snap_hpguppi_defaults as hpguppi_defaults
from SNAPobs.snap_hpguppi import record_in as hpguppi_record_in
from SNAPobs.snap_hpguppi import auxillary as hpguppi_auxillary

WAIT_DTFMT = "%Y-%m-%dT%Hh%Mm%Ss%z"
DAQPULSE_DTFMT = "%a %b %d %H:%M:%S %Y"

PROJECTID_FNAME = "./projects.json"
BACKENDS_FNAME = "./backends.json"
POSTPROCESSORS_FNAME = "./postprocessors.json"



def most_common(lst):
    return max(set(lst), key=lst.count)


def load_mapping(fname):
    with open(fname, 'r') as json_file:
        mapping = json.load(json_file)
    return mapping

def get_daqpulse(hp_targets):
    redis_obj = redis.Redis(host='redishost', decode_responses=True)
    daqpulses1 = []
    daqpulses2 = []

    for node,instances in hp_targets.items():
        for instance in instances:
            kv = HashpipeKeyValues(node, instance, redis_obj)
            dt_str = kv.get("DAQPULSE")
            if not dt_str:
                raise RuntimeError(f"Could not get a DAQPULSE from {node}.{instance}")

            try:
                dt = datetime.datetime.strptime(dt_str, DAQPULSE_DTFMT)
            except Exception as e:
                original_exception = e.args[0]
                raise RuntimeError(f"Could not convert to datetime from {node}.{instance}\nOriginal exception: {original_exception}")

            daqpulses1.append(dt)

    #sleep to get one second in
    time.sleep(1.5)

    for node,instances in hp_targets.items():
        for instance in instances:
            kv = HashpipeKeyValues(node, instance, redis_obj)
            dt_str = kv.get("DAQPULSE")
            if not dt_str:
                raise RuntimeError(f"Could not get a DAQPULSE from {node}.{instance}")

            try:
                dt = datetime.datetime.strptime(dt_str, DAQPULSE_DTFMT)
            except Exception as e:
                original_exception = e.args[0]
                raise RuntimeError(f"Could not convert to datetime from {node}.{instance}\nOriginal exception: {original_exception}")

            daqpulses2.append(dt)

    i = 0
    for node,instances in hp_targets.items():
        for instance in instances:
            daqpulse1 = daqpulses1[i]
            daqpulse2 = daqpulses2[i]
            diff = (daqpulse2 - daqpulse1).seconds
            if diff < 1:
                raise RuntimeError(f"No heartbeat from {node}.{instance}")
            i += 1



def get_current_backend(hp_targets):
    redis_obj = redis.Redis(host='redishost', decode_responses=True)
    kvs = []

    for node, instances in hp_targets.items():
        for instance in instances:
            kvs.append(HashpipeKeyValues(node, instance, redis_obj))

    backend = list(set(kv.get("HPCONFIG") for kv in kvs))
    assert len(backend) == 1, f"More than 1 backend detected for targets: {backend}"

    return backend[0]


class Executable(ABC):
    def __init__(self, config, write_status):
        # configuration dictionary for each executor
        self.config = config

        # propagating status
        self.write_status = write_status

        # in case schedule need to be aborted
        # The executor can use this flag to interrupt if needed
        self.interrupt = False


    @abstractmethod
    def execute(self):
        pass

    def check_consistency(self, needed_keys):
        for key in needed_keys:
            if key not in self.config.keys():
                raise RuntimeError("Key: %s not in config keys" %key)

    def interrupt_requested(self):
        return self.interrupt


class ReserveAntennas(Executable):
    """
    Executer class that reserves antennas and checks whether their LNAs are on
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        needed_keys = ["ant_list"]
        self.check_consistency(needed_keys)

    def execute(self):
        ant_list = self.config['ant_list']
        self.write_status(f"Reserving antennas: {ant_list}")
        ata_control.reserve_antennas(ant_list)

        # Get LNA status, and raise an exception if any is not on
        self.write_status("Getting LNA status")
        lnas = ata_control.get_lnas(ant_list)
        lnas_off = []

        for ant in ant_list:
            if not lnas[ant]['on']:
                lnas_off.append(ant)

        # At least 1 antenna has LNA off!
        if lnas_off:
            raise RuntimeError(f"LNAs for {lnas_off} are off!")


class ReleaseAntennas(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        needed_keys = ["ant_list"]
        self.check_consistency(needed_keys)

    def execute(self):
        ant_list = self.config['ant_list']
        self.write_status(f"Releasing antennas: {ant_list}")
        ata_control.release_antennas(ant_list, False)


class SetFreqTunning(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        needed_keys = ["ant_list", "RFgain", "IFgain",
                       "EQlevel", "Focus"]
        self.check_consistency(needed_keys)

    def execute(self):
        # Get all the needed LOs
        los   = []
        freqs = []
        for t in ["a", "b", "c", "d"]: 
            t_config = 'Tuning'+t.upper()
            # Check if tunings are in the config
            if t_config in self.config:
                f = self.config[t_config]
                # check if frequency is valid
                if f != '' and f != '0':
                    los.append(t)
                    freqs.append(float(f))
        if los:
            self.write_status("Setting frequencies for LOs: %s" %los)
            max_freq = max(freqs)
            lo_max_freq = los[freqs.index(max_freq)]

            for lo, freq in zip(los, freqs):
                if freq == max_freq:
                    focus_bool = bool(int(self.config['Focus']))
                    self.write_status(f"Setting frequency {freq} for LO {lo}, setting focus: {focus_bool}")
                    # "notfocus" is a bit confusing, but I set nofocus to True
                    # if I don't want to set focus
                    ata_control.set_freq(freq, self.config['ant_list'], 
                                         lo=lo, nofocus= not focus_bool)
                    # no feedback from focus freq mechanism
                    # so I just wait for 20 seconds to make sure it happens
                    if focus_bool:
                        time.sleep(20)
                else:
                    ata_control.set_freq(freq, self.config['ant_list'], 
                                         lo=lo, nofocus=True)
                    self.write_status(f"Setting frequency {freq} for LO {lo}")

        if bool(int(self.config['RFgain'])):
            self.write_status("Tunning RF...")
            ata_control.autotune(self.config['ant_list'])
            self.write_status("Done")

        if bool(int(self.config['IFgain'])):
            self.write_status("Tuning IF...")
            ata_if.tune_if(self.config['ant_list'], los=los)
            self.write_status("Done")

        if bool(int(self.config['EQlevel'])):
            self.write_status("EQ level setting is not implemented yet", fg='red')


class WaitFor(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        needed_keys = ["twait"]
        self.check_consistency(needed_keys)
    def execute(self):
        t = float(self.config["twait"])
        self.write_status(f"Waiting for {t} seconds")

        t_unix_end = time.time() + t

        while time.time() < t_unix_end:
            if self.interrupt_requested():
                self.write_status(f"observation stop requested", fg='red')
                return
            time.sleep(1)


class WaitUntil(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        needed_keys = ["dt"]
        self.check_consistency(needed_keys)

    def execute(self):
        dt_str = self.config["dt"]
        dt = datetime.datetime.strptime(dt_str, WAIT_DTFMT)
        self.write_status(f"Waiting until: {dt_str}")
        self.wait_until(dt)
        self.write_status(f"Done waiting")

    def wait_until(self, target_time: datetime.datetime):
        """
        Pauses execution until the specified target time.

        Parameters:
        - target_time (datetime.datetime): The datetime to wait until.

        Raises:
        - ValueError: If target_time is in the past.
        """
        now = datetime.datetime.now().astimezone()

        if target_time <= now:
            self.write_status(f"Target time {target_time} is in the past. Please provide a future time...",
                    "red")
            return

        # Calculate the remaining time in seconds
        remaining_time = (target_time - now).total_seconds()
        self.write_status(f"Waiting for {remaining_time} seconds until {target_time}...")

        # Sleep for the remaining time
        t_unix_end = time.time() + remaining_time
        while time.time() < t_unix_end:
            if self.interrupt_requested():
                self.write_status(f"observation stop requested", fg='red')
                return
            time.sleep(1)
        self.write_status("Reached target time!")

class WaitPrompt(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def execute(self):
        root = tk.Tk()
        root.geometry("350x150")  # Set the size of the window
        root.title("Wait prompt")

        self.write_status("User prompt: press 'continue' to proceed with observing script")
        label = tk.Label(root, text="Press to continue observation", font=("Arial", 18))
        def on_click():
            root.destroy()

        label.pack(pady=20)  # Add some padding around the label
        continue_button = tk.Button(root, text="Continue", 
            command = on_click, font=("Arial", 14))
        continue_button.pack(pady=10)

        root.mainloop()
        self.write_status("User prompt: continuing observing script")





class SetBackend(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        needed_keys = ["ProjectID", "Backend", 
                "Postprocessor", "hp_targets"]
        self.check_consistency(needed_keys)

        self.check_heartbeat = False

    def execute(self):
        projectid_mapping      = load_mapping(PROJECTID_FNAME)
        backends_mapping       = load_mapping(BACKENDS_FNAME)
        postprocessors_mapping = load_mapping(POSTPROCESSORS_FNAME)

        backend_config  = backends_mapping[self.config['Backend']]
        postproc_script = postprocessors_mapping[self.config['Postprocessor']]

        # Set backend
        self.write_status(f"executing: ansible-playbook {backend_config}")
        os.system(f"ansible-playbook {backend_config}")

        if self.config['Backend'].upper().startswith("XGPU"):
            res = parse('xGPU_{xtimeint}s{tmp}', self.config['Backend']+"tmp")
            xtimeint = float(res['xtimeint'])
            keyval_dict = {'XTIMEINT': xtimeint}

            hp_targets = self.config['hp_targets']

            hpguppi_auxillary.publish_keyval_dict_to_redis(keyval_dict,
                            hp_targets, postproc=False)



        # Set postprocessor
        self.write_status(f"executing: {postproc_script}")
        os.system(postproc_script)

        if self.check_heartbeat:
            time.sleep(1)
            self.write_status("Checking for DAQPULSE")
            get_daqpulse(self.config['hp_targets'])
            self.write_status("Done")


class SetAzEl(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        needed_keys = ["ant_list", "Az", "El"]
        self.check_consistency(needed_keys)

    def execute(self):
        ant_list = self.config['ant_list']
        Az, El = float(self.config['Az']), float(self.config['El'])
        self.write_status(f"Setting antennas to Az,El = ({Az}, {El})")
        ata_control.set_az_el(ant_list, self.config['Az'], self.config['El'])


        
class TrackAndObserve(Executable):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        needed_keys = ["ant_list", "hp_targets", "Source",
                "ObsTime"]
        self.check_consistency(needed_keys)

    def execute(self):
        ant_list = self.config['ant_list']
        source   = self.config['Source']

        if source.upper() != "NONE":
            self.write_status(f"Tracking source {source}")
            ata_control.make_and_track_ephems(source, ant_list)
        else: 
            # we got a "none" source to track, so let's get the source the 
            # antennas are currently observing
            sources = list(ata_control.get_eph_source(ant_list).values())
            # this will get the source for all the allocated antennas
            sources_unique = list(set(sources))

            if len(sources) == 1:
                # all antennas are pointed at the same place
                source = sources_unique[0]
            else:
                # Why are we using the beamformer if not all antennas are
                # pointed at the same source??
                # I'll get the most common source the antennas are pointed at
                source = most_common(sources)



        obstime = float(self.config['ObsTime'])
        hp_targets = self.config['hp_targets']

        if obstime != 0:
            current_backend = get_current_backend(hp_targets)

            # If beamformer, let's configure the beams
            if 'BLADE' in current_backend.upper():
                try:
                    ra, dec = ata_control.get_source_ra_dec(source)
                except Exception as e:
                    # source not in database...?
                    # just get the ra, dec from first antenna
                    ra, dec = ata_control.get_ra_dec(ant_list[0])[ant_list[0]]

                # First populate the central beam
                # Note: these can be overwritten if user passes 
                # "RA_OFF0" and "DEC_OFF0"
                keyval_dict = {'RA_OFF0': ra, 'DEC_OFF0': dec}

                # cluncky way to do things, but I want to search for the 
                # number of beams, so I assume if RA_OFF is present, 
                # it means we have a beam on sky
                beams = []
                for key in self.config.keys():
                    if 'RA_OFF' in key.upper():
                        beams.append(key.replace("RA_OFF", "")) # I am collecting beam numbers

                for beam in beams:
                    # Make sure both RA_OFFX and DEC_OFFX exist for X beam
                    if f"DEC_OFF{beam}" not in self.config:
                        self.write_status(f"DEC_OFF{beam} does not exist!")
                    else:
                        keyval_dict[f"RA_OFF{beam}"] = self.config[f"RA_OFF{beam}"]
                        keyval_dict[f"DEC_OFF{beam}"] = self.config[f"DEC_OFF{beam}"]

                hpguppi_auxillary.publish_keyval_dict_to_redis(keyval_dict,
                        hp_targets, postproc=False)

            elif "XGPU" in current_backend.upper():
                # set integration time if provided
                if "XTIMEINT" in self.config:
                    keyval_dict = {'XTIMEINT': self.config['XTIMEINT']}
                    hpguppi_auxillary.publish_keyval_dict_to_redis(keyval_dict,
                            hp_targets, postproc=False)

            obs_start_in = 10
            hpguppi_record_in.record_in(obs_start_in, obstime,
                    hashpipe_targets = hp_targets)
            self.write_status(f"Recording for {obstime}")

            t_unix_end = time.time() + obstime + obs_start_in + 5
            
            while time.time() < t_unix_end:
                if self.interrupt_requested():
                    hpguppi_record_in.record_in(reset=True,
                            hashpipe_targets = hp_targets)
                    return
                time.sleep(1)




class ScheduleExecutor:
    def __init__(self, action_type, config, write_status=print):
        self.executor = self._get_executor(action_type, config, write_status)
        self.action_type = action_type
        self.config = config

    def _get_executor(self, action_type, config, write_status):
        if action_type == "SETFREQ":
            return SetFreqTunning(config, write_status)
        elif action_type == "BACKEND":
            return SetBackend(config, write_status)
        elif action_type == "TRACK":
            return TrackAndObserve(config, write_status)
        elif action_type == "WAITPROMPT":
            return WaitPrompt(config, write_status)
        elif action_type == "WAITUNTIL":
            return WaitUntil(config, write_status)
        elif action_type == "WAITFOR":
            return WaitFor(config, write_status)
        elif action_type == "SETAZEL":
            return SetAzEl(config, write_status)
        elif action_type == "RESERVEANTENNAS":
            return ReserveAntennas(config, write_status)
        elif action_type == "RELEASEANTENNAS":
            return ReleaseAntennas(config, write_status)
        else:
            raise RuntimeError(f"No known executor for action: {action_type}")

    # this can be ran in a thread
    def execute(self):
        self.executor.execute()

    # Call to interrupt execution
    def interrupt(self):
        self.executor.interrupt = True
