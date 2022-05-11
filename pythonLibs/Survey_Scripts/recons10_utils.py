import pandas as pd
import numpy as np
import os

FREQ_RANGE = [3350, 4050, 4750, 5450, 6150, 6850, 7550, 8250, 8950, 9650]

def create_entry_csv(original_recons_csv, freq_range=FREQ_RANGE,
        output_csv="sources_observed.csv"):
    """
    Creates the entry databases 
    """
    recons = pd.read_csv(original_recons_csv)
    d = pd.DataFrame()

    d['Name'] = recons['Name']

    for freq in freq_range:
        n = "cfreq_%imhz" %freq
        print(n)
        d[n] = np.zeros_like(d['Name'])

    if os.path.exists(output_csv):
        raise RuntimeError("Output csv [%s] already exist, will not overwrite"\
                %output_csv)
    d.to_csv(output_csv, index=False)

def get_source_names(csv_name):
    """
    returns a list of all the sources in the recons10 database
    """
    d = pd.read_csv(csv_name)
    return list(d['Name'])

def is_observed(csv_name, source, freq_mhz):
    """
    Returns 0 if source has been observed at the frequency, otherwise 1
    """
    assert type(source) == str
    assert type(freq_mhz) == int

    source_entries = pd.read_csv(csv_name)
    cfreq_name = "cfreq_%imhz" %freq_mhz

    row = source_entries.loc[source_entries['Name'] == source]
    return row[cfreq_name].values[0]

def mark_as_observed(csv_name, source, freq_mhz):
    """
    Marks the observation as observed by adding 1 to the database entry
    """
    assert type(source) == str
    assert type(freq_mhz) == int

    source_entries = pd.read_csv(csv_name)
    cfreq_name = "cfreq_%imhz" %freq_mhz

    ival = source_entries.loc[source_entries['Name'] == source, cfreq_name].values[0]

    if ival == 0:
        source_entries.loc[source_entries['Name'] == source, cfreq_name] = 1
        source_entries.to_csv(csv_name, index=False)
    elif ival == 1:
        print("WARNING: has this source been observed before?")
