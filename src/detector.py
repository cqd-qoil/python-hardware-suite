from abc import abstractmethod
from collections.abc import Sequence
import sys
import time
import clr
import pyvisa as visa
import numpy as np
from ThorlabsPM100 import ThorlabsPM100
from System import Array, Byte, Int64, Int32
from TimeTag import TTInterface, Logic

# Add Logic16 driver to the path (ensure it's the 64-bit version and permissions are granted)
sys.path.append('.')
clr.AddReference('.\\bin\\ttInterface.dll')

# Abstract base class for detectors
class Detector:
    @abstractmethod
    def read(self):
        pass


# PowerMeter class for interacting with a Thorlabs PM100 power meter device
class PowerMeter(Detector):
    def __init__(self, device_name):
        self.address = self.get_power_meter_address(device_name)
        self.pm = self.power_meter_init(wv=780)

    def get_power_meter_address(self, device_name):
        """
        Search for the power meter by device name and return its VISA address.
        """
        rm = visa.ResourceManager()
        for item in rm.list_resources():
            try:
                inst = rm.open_resource(item)
                idn = inst.query('*IDN?').strip()
                if device_name in idn:
                    return item
            except Exception as e:
                print(f"Error querying VISA resource {item}: {e}")
        print("Power meter not found.")
        return None

    def power_meter_init(self, wv=780):
        """
        Initialize power meter and configure it to the specified wavelength.
        """
        if self.address:
            rm = visa.ResourceManager()
            inst = rm.open_resource(self.address)
            power_meter = ThorlabsPM100(inst=inst)
            power_meter.configure.scalar.power()
            power_meter.sense.correction.wavelength = wv
            return power_meter
        print("Power meter address not found")
        return None

    def read(self, power_samples=30):
        """
        Read power samples, calculate average and return the mean.
        """
        power = np.array([self.pm.read for i in range(power_samples)])
        return power.mean()


# Helper function to convert channel to binary code
def binary_code(channel):
    """
    For use in Logic16
    """
    if isinstance(channel, Sequence):
        return sum([binary_code(k) for k in channel])
    else:
        return 2**(channel-1)

# Logic16 class for controlling UQDevices hardware
class Logic16(Detector):
    def __init__(self, logic_mode=True):
        self.MyTagger = TTInterface()
        self.MyTagger.Open()
        self._resolution = self.MyTagger.GetResolution()
        self._logic_mode = False
        if logic_mode == True:
            self._logic_mode = True
            self.MyLogic = Logic(self.MyTagger)
            self.MyLogic.SwitchLogicMode()

        self._total_channels = self.MyTagger.GetNoInputs()
        self._integration_window = 0.5 # same as self.timeInterval
        self._coincidence_window = 1e-9
        # For antilatch
        self.singles = None
        self._antilatch_timeslice = 0.100 # 100 miliseconds
        self.antilatch_func = lambda: print('test')
        self.coincidences = None

        self.TimerCounter1 = Int32
        self.clear_buffer()

    def __enter__(self):
        """
        Context manager
        """
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """
        Context manager
        """
        self.MyTagger.Close()

    def set_channels(self, singles, coincidences=None):
        assert isinstance(singles, Sequence)
        self.singles = singles
        self._bsingles = [binary_code(channel) for channel in singles]
        if coincidences is not None:
            assert isinstance(coincidences[0], Sequence)
            self.coincidences = coincidences
            self._bcoincidences = [binary_code(pair) for pair in coincidences]

    def set_delays(self, channel_delay_dict=dict(), default_delay=100):
        if hasattr(self,'delays'):
            for k,v in channel_delay_dict.items():
                assert k in range(1, self._total_channels+1)
                self.delays.update({k:v})
                self.MyTagger.SetDelay(k, (v*1e-9)/self._resolution)
        else:
            self.delays = {k:default_delay for k in range(1, self._total_channels+1)}
            self.set_delays(channel_delay_dict=channel_delay_dict)

    def set_input_threshold(self,channel_threshold_dict=None,default_threshold=0.5):
        # Configure the channel for measurement
        if channel_threshold_dict is not None:
            for k,v in channel_threshold_dict.items():
                assert k in range(1, self._total_channels+1)
                self.MyTagger.SetInputThreshold(k, v)
        else:
            for k in range(1, self._total_channels+1): # 16 channels if low-resolution
                self.MyTagger.SetInputThreshold(k, default_threshold)

    def set_coincidence_window(self, window):
        assert self._logic_mode
        self._coincidence_window = window*1e-9
        self.MyLogic.SetWindowWidth(self._coincidence_window/self._resolution)

    def get_status(self):
        msg = '>>> Logic16 counting card\n'
        msg += '> FPGA version:\t\t{}\n'.format(self.MyTagger.GetFpgaVersion())
        msg += '> Resolution:\t\t{}\n'.format(self._resolution)
        msg += '> Input channels:\t{}\n'.format(self.MyTagger.GetNoInputs())
        msg += '> Integration window:\t{} s\n'.format(self._integration_window)
        msg += '> Coincidence window:\t{} ns\n'.format(self._coincidence_window*1e9)
        print(msg)

    def clear_buffer(self):
        self.MyLogic.ReadLogic()
        TimeCounter1 = self.MyLogic.GetTimeCounter()

    def calc_single_count(self, pos, neg):
        """
        Calculates the count for a single channel.
        Uses binary encoding for the positive and negative channels.
        """
        return self.MyLogic.CalcCount(binary_code(pos), binary_code(neg))

    def read_counts(self, pos_coincidence, pos_singles, neg_singles=[0]):
        """
        Reads the counts for singles and coincidences for the specified channels.
        Returns the counts as arrays and the time counter value.
        """
        self.MyLogic.ReadLogic()
        timecounter = self.MyLogic.GetTimeCounter()

        counts_singles = [self.calc_single_count(pos, 0) for pos in pos_singles]
        neg_singles = neg_singles * len(pos_coincidence) if len(neg_singles) == 1 else neg_singles
        assert len(neg_singles) == len(pos_coincidence)
        counts_coinc = [self.calc_single_count(pos, neg_singles[k]) for k, pos in enumerate(pos_coincidence)]

        return np.array(counts_coinc, dtype=int), np.array(counts_singles, dtype=int), timecounter

    def antilatch_check(self, singles_to_check):
        """
        Checks for latching events, both in the case of one detector latching (any) or all detectors latching (all). It is a good idea to differentiate between the two cases: if all detectors latch, it might be indicative of the cryostat being warm.
        """
        check = [singles==0 for singles in singles_to_check]
        return any(check) + all(check)

    def read_counts_integrated(self, pos_coincidence, pos_singles, neg_singles=[0]):
        """
        Reads integrated counts over a specified integration window.
        Handles antilatching by checking for repeated latch events and retrying if necessary.
        """
        iter = 0
        counting_time = 0
        total_c_counts = np.zeros(len(pos_coincidence))
        total_s_counts = np.zeros(len(pos_singles))
        has_latched = 0
        self.clear_buffer()

        # Instead of reading counts for the entire `counting_time` duration, which can be quite large,
        # read for a smaller integration time (we call this the "timeslice"). Doing this reduces the
        # chance of latching events messing up the photon counts.
        while counting_time <= self._integration_window:
            time.sleep(self._antilatch_timeslice)
            c_counts, s_counts, timecounter = self.read_counts(pos_coincidence=pos_coincidence,
                                                               pos_singles=pos_singles,
                                                               neg_singles=neg_singles)
            antilatch_flags = self.antilatch_check(s_counts)
            has_latched += antilatch_flags

            # If detectors keep latching, wait for a bit instead of sending another antilatch request.
            if has_latched > 5:
                self.antilatch_func()
                print('WARNING: several latching events in a row, waiting 1 min.')
                has_latched = 0
                time.sleep(60)
                continue
            if antilatch_flags > 0:
                self.antilatch_func()
                print('.', end='') # Simple way to keep track of antilatch events
                time.sleep(0.2)
                self.clear_buffer()
                continue
            else:
                has_latched = 0
            total_c_counts += c_counts
            total_s_counts += s_counts
            counting_time += timecounter*5e-9
        return total_c_counts, total_s_counts, counting_time
