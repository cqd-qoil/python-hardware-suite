from seabreeze.spectrometers import Spectrometer
import numpy as np
from scipy.optimize import curve_fit
from scipy.stats import norm
from scipy.interpolate import UnivariateSpline
import time
import pandas as pd

class Spectro:
    def __init__(self, integration_time=100000):
        # Initialize the spectrometer and set integration time
        self.spec = Spectrometer.from_first_available()
        self.spec.integration_time_micros(integration_time)

    def __del__(self):
        # Close the spectrometer connection when done
        self.spec.close()

    def filter_idx(self, w_min, w_max):
        """
        Filter the wavelengths within the specified range [w_min, w_max].
        """
        wavelengths = self.spec.wavelengths()
        idx = np.where((w_min < wavelengths) & (wavelengths < w_max))
        self.f = idx[0]

    @staticmethod
    def gauss(x, x0=0, sigma=1, a=1, b=0):
        return a * np.exp(-((x - x0) / sigma) ** 2) + b

    def FWHM(self, X, Y):
        half_max = max(Y) / 2
        d = np.sign(half_max - np.array(Y[:-1])) - np.sign(half_max - np.array(Y[1:]))
        left_idx = np.where(d > 0)[0]
        right_idx = np.where(d < 0)[-1]
        return X[right_idx] - X[left_idx]

    def get_width(self, w0, i0, method='fwhm'):
        """
        Get the width of the spectral peak within the specified window. Two methods are available:
        - 'spline'
        - 'fwhm' on gaussian fit
        """
        if method.lower() == 'spline':
            # Using Univariate Spline to calculate the half-maximum and find roots
            spline = UnivariateSpline(w0, i0 - np.max(i0) / 2, s=0)
            roots = spline.roots()

            # Check if roots were found, otherwise fall back to 'fwhm'
            if len(roots) >= 2:
                return roots[-1] - roots[0]
            else:
                print("Spline method failed to find valid roots, falling back to 'fwhm'.")
                return self.get_width(w0=w0, i0=i0, method='fwhm')  # Fallback to 'fwhm' method
        else:
            # Using Gaussian fit to calculate Full Width at Half Maximum (FWHM)
            popt, _ = curve_fit(self.gauss, xdata=w0, ydata=i0, p0=[np.mean(w0), 2, max(i0), min(i0)])
            w1 = np.linspace(w0[0], w0[-1], 100)
            i1 = self.gauss(w1, *popt)
            return self.FWHM(w1, i1)



    def log_laser(self, window=[765, 785], method='fwhm'):
        """
        Log the central wavelength and amplitude of the laser within the specified window.
        """
        self.filter_idx(*window)
        wavelengths = self.spec.wavelengths()
        intensities = self.spec.intensities()
        w0, i0 = wavelengths[self.f], intensities[self.f]

        # Find the central wavelength and amplitude
        central_wv = w0[np.argmax(i0)]
        amplitude = max(i0)
        width = self.get_width(w0=w0,i0=i0,method=method)

        return dict(wavelength = central_wv, amplitude = amplitude, width=width)

# Example of usage:
if __name__ == "__main__":
    # Create a SpectrometerAnalysis instance with a specific integration time
    analysis = SpectrometerAnalysis(integration_time=100000)

    # Get the width of the spectral peak
    width = analysis.get_width(window=[765, 785])
    print(f"Spectral width: {width}")

    # Log the laser data
    central_wv, amplitude = analysis.log_laser(window=[770, 780])
    print(f"Central wavelength: {central_wv} nm, Amplitude: {amplitude}")
