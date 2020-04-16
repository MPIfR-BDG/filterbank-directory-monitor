# APSUSE Directory Monitor

import os
import glob
import redis
import numpy as np
from time import sleep
from threading import Thread
from sigpyproc.Readers import FilReader

"""
Idea:

Connect clients to FBFUSE and APSUSE to scrape information.
The following is desired:

 - FBFUSE beam positions and tiling pattern (with markers for beams that are bein recorded by apsuse)
 - APSUSE current recoding directory (currently just subarray_1) [key = array_X_current_recording_directory]

This can be used to create:
 - bandpasses for coherent and incoherent beams
 - folds for pulsars in both coherent and incoherent beam
q = psrqpy.QueryATNF(params=['JName'], circular_boundary=(opts.ra, opts.dec, opts.radius), assoc=opts.assoc, psrtype=opts.psrtype)
"""


class BandpassGenerator(Thread):
    def __init__(self, root_dir, interval=300):
        Thread.__init__(self)
        self.setDaemon(True)
        self._root_dir = root_dir
        self._interval = interval
        self._redis = redis.StrictRedis("apsuse-monitor-redis")

    def generate_bandpass(self, fname):
        fil = FilReader(fname)
        ar = np.recarray(fil.header.nchans, dtype=[
            ("frequency", "float32"), ("mean", "float32"), ("std", "float32")])
        fil.getStats(gulp=10000)
        ar["mean"] = fil.chan_means
        ar["std"] = fil.chan_stdevs
        ar["frequency"] = np.linspace(
            fil.header.fbottom, fil.header.ftop, fil.header.nchans)
        return ar

    def callback(self):
        # first find the most recent directory:
        directory = max(glob.glob("/{}/*/*/*/".format(self._root_dir)),
            key=os.path.getctime)
        coherent_dir = sorted(glob.glob("{}/cfbf*/"))[0]
        # Take the second to last file as it is guaranteed to be finished writing
        coherent_file = sorted(glob.glob("{}/*.fil".format(coherent_dir)))[-2]
        incoherent_dir = sorted(glob.glob("{}/ifbf*/"))[0]
        # Take the second to last file as it is guaranteed to be finished writing
        incoherent_file = sorted(glob.glob("{}/*.fil".format(coherent_dir)))[-2]
        self._redis.set("filterbank-directory-monitor:directory", directory)
        self._redis.set("filterbank-directory-monitor:coherent:bandpass",
            self.generate_bandpass(coherent_file).tobytes())
        self._redis.set("filterbank-directory-monitor:incoherent:bandpass",
            self.generate_bandpass(incoherent_file).tobytes())
        self._redis.set("filterbank-directory-monitor:coherent:file",
            coherent_file.split("/")[-1])
        self._redis.set("filterbank-directory-monitor:incoherent:file",
            incoherent_file.split("/")[-1])

    def run(self):
        while True:
            try:
                self.callback()
            except Exception as error:
                print("Error: {}".format(str(error)))
            finally:
                sleep(self._interval)


if __name__ == "__main__":
    scraper = BandpassGenerator("/beegfs/DATA/TRAPUM/")
    scraper.start()
    scraper.join()
