#!/home/obsuser/miniconda3/envs/ATAobs/bin/python
from flask import Flask
import plotly.graph_objects as go
from plotly.subplots import make_subplots

import dash
import dash_table
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output

import numpy as np
import pandas as pd
import time
import os
from concurrent.futures import ThreadPoolExecutor
import pytz
from datetime import datetime

#from simulator import ata_snap_fengine
from ata_snap import ata_snap_fengine
from SNAPobs import snap_defaults, snap_config
from ATATools import ata_control
import casperfpga
from threading import Thread
from itertools import repeat
import atexit

from ATATools import ata_helpers
from ATATools.device_lock import set_device_lock, release_device_lock

ATA_CFG = snap_config.get_ata_cfg()
ATA_SNAP_TAB = snap_config.get_ata_snap_tab()

BW = snap_defaults.bw #MHz
NCHANS = snap_defaults.nchan
FOFF = BW/NCHANS

TZ = pytz.timezone('America/Los_Angeles')

snaps = ['frb-snap1-pi', 'frb-snap2-pi', 
        'frb-snap3-pi', 'frb-snap4-pi',
        'frb-snap5-pi', 'frb-snap6-pi',
        'frb-snap7-pi', 'frb-snap8-pi',
        'frb-snap9-pi', 'frb-snap10-pi',
        'frb-snap11-pi', 'frb-snap12-pi',
        ]




class cfreqThread(Thread):
    def __init__(self, LOs, *args, **kwargs):
        super(cfreqThread,self).__init__(*args, **kwargs)
        self.LOs = LOs
        self.cfreqs = {}
        for lo in LOs:
            try:
                self.cfreqs[lo] = ata_control.get_sky_freq(lo)
            except:
                self.cfreqs[lo] = 15000

    def run(self):
        while True:
            time.sleep(20)
            for lo in LOs:
                try:
                    self.cfreqs[lo] = ata_control.get_sky_freq(lo)
                except:
                    self.cfreqs[lo] = 15000


class SnapThread(Thread):
    def __init__(self, fengs, *args, **kwargs):
        super(SnapThread,self).__init__(*args, **kwargs)
        self.fengs = fengs
        self.hosts = [snap.host for snap in fengs]
        self.nsnap = len(self.hosts)
        self.snaps_res = dict.fromkeys(self.hosts)

        self.defs = {}
        self.defs['def_xx'] = np.ones(NCHANS) * 200000
        self.defs['def_yy'] = np.ones(NCHANS) * 200000
        self.defs['def_adc_x'] = np.random.normal(size=NCHANS)
        self.defs['def_adc_y'] = np.random.normal(size=NCHANS)

    @staticmethod
    def get_bp_thread(snap, defs):
        ntries = 3
        itry = 0
        while (itry < ntries):
            try:
                set_device_lock(snap.host)
                acc_len = snap.fpga.read_int('timebase_sync_period')*8/4096/2
                xx,yy = snap.spec_read()
                adc_x, adc_y = snap.adc_get_samples()
                release_device_lock(snap.host)

                xx = xx / acc_len
                yy = yy / acc_len
                return (xx,yy,adc_x,adc_y)
            except Exception as e:
                time.sleep(0.5)
                itry += 1
        return (defs['def_xx'], defs['def_yy'], 
                defs['def_adc_x'], defs['def_adc_y'])

    def run(self):
        conn = ThreadPoolExecutor(max_workers=self.nsnap)
        while True:
            t = time.time()
            snaps_res = conn.map(self.get_bp_thread, self.fengs, 
                    repeat(self.defs))
            self.snaps_res = {host:data for host,data in
                    zip(self.hosts,snaps_res)}
            time.sleep(1)

LOs = pd.unique(ATA_SNAP_TAB.LO)
cfreq_thread = cfreqThread(LOs)
cfreq_thread.daemon = True
cfreq_thread.start()


fengs = [ata_snap_fengine.AtaSnapFengine(snap, 
    transport=casperfpga.KatcpTransport) 
        for snap in snaps]
for feng in fengs:
    feng.fpga.get_system_information(ATA_CFG['SNAPFPG'])

snap_thread = SnapThread(fengs)
snap_thread.daemon = True
snap_thread.start()

# give the thread sometime to pull data
time.sleep(10)
snaps_res = snap_thread.snaps_res

FIGS = {}
for snap in fengs:
    fig = make_subplots(rows=1, cols=2, 
            column_widths=[0.8, 0.2], horizontal_spacing=0.05,
            )

    cfreqs = cfreq_thread.cfreqs
    lo = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname == snap.host].LO.values[0]
    cfreq = cfreqs[lo]

    xx,yy,adc_x,adc_y = snaps_res[snap.host]
    #x = np.linspace(cfreq - BW/2, cfreq + BW/2, len(xx)) - FOFF/2.
    #x = np.linspace(cfreq - BW/2 + FOFF/2., cfreq + BW/2 + FOFF/2., 
    #        len(xx)+1) - FOFF/2.
    #x = x[:-1]
    x = np.arange(cfreq - BW/2, cfreq + BW/2, FOFF)

    fig.append_trace({
	    'x': x,
	    'y': 10*np.log(xx+0.1),
	    'name': 'X-pol',
	    'mode': 'lines',
	    'type': 'scatter'
	}, 1, 1)
    fig.append_trace({
	    'x': x,
	    'y': 10*np.log(yy+0.1),
	    'name': 'Y-pol',
	    'mode': 'lines',
	    'type': 'scatter'
	}, 1, 1)

    fig.append_trace(
            go.Histogram(x=adc_x, name='RMS_x: %.2f' %np.std(adc_x), 
                marker_color='blue'), 
            1, 2)
    fig.append_trace(
            go.Histogram(x=adc_y, name='RMS_y: %.2f' %np.std(adc_y), 
                marker_color='red'), 
            1, 2)

    ant_name = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname == snap.host].ANT_name
    ant_name = ant_name.values[0]
    #ind = np.where(snap_ant[:,0] == snap.host)[0]
    #ant_name = snap_ant[ind,1][0]

    fig.update_layout(
            title="<b>Antenna:</b> %s  ---  <b>Snap:</b> %s  "
            "---  <b>LO:</b> %s, <b>cfreq:</b> %.4f"
              %(ant_name, snap.host, lo, cfreq),
            xaxis_title = 'Frequency (MHz)',
            yaxis_title = 'Power (dB)',
            xaxis2_title = 'ADC values',
            margin=dict(l=30, r=30, b=50, t=50),
            font = dict(family='Times new roman', size=20),
            #annotations = dict(size=60)
            )

    FIGS[snap.host] = fig


graphs = [dcc.Graph(figure=FIGS[snap_name], id=snap_name) for snap_name in snaps]
FIGS_HTML = html.Div(graphs, id='figs_html')
TIME_HTML = html.Div(html.H3(""), id="time_html")

app = dash.Dash()
#app = Flask(__name__)
app.layout = html.Div(
    [html.H1('ATA snap monitor')] +
    [TIME_HTML] + 
    [html.Br()]*3 +
    [FIGS_HTML] + 
    [dcc.Interval(
        id='plot-update',
        interval = 5*1000,
        n_intervals = 0)]
    )

@app.callback(
        [Output("figs_html", "children")],
        [Input("plot-update", "n_intervals")])
def gen_bp(interval=None):
    #cfreq = cfreq_thread.cfreq
    cfreqs = cfreq_thread.cfreqs
    snaps_res = snap_thread.snaps_res.copy()


    for i,snap in enumerate(fengs):
        xx, yy, adc_x, adc_y = snaps_res[snap.host]
        lo = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname == snap.host].LO.values[0]
        cfreq = cfreqs[lo]
        ant_name = ATA_SNAP_TAB[ATA_SNAP_TAB.snap_hostname ==\
                snap.host].ANT_name
        ant_name = ant_name.values[0]
        #x = np.linspace(cfreq - BW/2, cfreq + BW/2, len(xx)) - FOFF/2.
        #x = np.linspace(cfreq - BW/2 + FOFF/2., cfreq + BW/2 + FOFF/2., 
        #        len(xx)+1) - FOFF/2.
        #x = x[:-1]
        x = np.arange(cfreq - BW/2, cfreq + BW/2, FOFF)
        FIGS_HTML.children[i].figure.data[0].y = 10*np.log10(xx + 0.1)
        FIGS_HTML.children[i].figure.data[0].x = x
        FIGS_HTML.children[i].figure.data[1].y = 10*np.log10(yy + 0.1)
        FIGS_HTML.children[i].figure.data[1].x = x

        FIGS_HTML.children[i].figure.data[2].x = adc_x
        FIGS_HTML.children[i].figure.data[2].name = 'RMS_x: %.2f' %np.std(adc_x)
        FIGS_HTML.children[i].figure.data[3].x = adc_y
        FIGS_HTML.children[i].figure.data[3].name = 'RMS_y: %.2f' %np.std(adc_y)

        FIGS_HTML.children[i].figure.layout.title="""<b>Antenna:</b> %s  ---  
<b>Snap:</b> %s  
---  <b>LO:</b> %s, <b>cfreq:</b> %.4f"""\
                %(ant_name, snap.host, lo, cfreq)


    return [FIGS_HTML.children]

@app.callback(
        [Output("time_html", "children")],
        [Input("plot-update", "n_intervals")])
def update_time(interval=None):
    tstr = datetime.now(tz=TZ).strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
    TIME_HTML.children = html.H3("Last updated (local time): %s" %tstr)
    return [TIME_HTML.children]

HOST = "snapmon"
PORT = 8880
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='ATA snap monitor')
    parser.add_argument('-i', dest='interface', type=str, default=HOST,
            required=False, help='Host name (default: %s)' %HOST)
    parser.add_argument('-p', dest='port', type=int, default=PORT,
            required=False, help='Port number (defaults: %i)' %PORT)

    args = parser.parse_args()

    #from waitress import serve
    #serve(app, host=HOST, port = PORT)
    app.run_server(port=args.port, host=args.interface)
