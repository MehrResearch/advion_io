#%%
import ctypes
from enum import IntEnum
import numpy as np

from matplotlib import pyplot as plt

from .constants import AdvionDataErrorCode, NAMES

lib = ctypes.cdll.LoadLibrary('../AdvionAPI.6.4.14.1.VS15x64/Release/AdvionData.dll')

bindings = {}

for demangled, (mangled, arg_types, res_type) in NAMES.items():
    bindings[demangled] = lib[mangled]
    bindings[demangled].argtypes = arg_types
    bindings[demangled].restype = res_type

# %%
class AdvionData:
    def __init__(self, path, debug_output, decode_spectra):
        self.handle = ctypes.create_string_buffer(32)
        bindings['DataReader'](ctypes.byref(self.handle), path, debug_output, decode_spectra)

    def get_num_masses(self):
        return bindings['DataReader::getNumMasses'](ctypes.byref(self.handle))

    def get_num_spectra(self):
        return bindings['DataReader::getNumSpectra'](ctypes.byref(self.handle))
    
    def get_masses(self):
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings['DataReader::getMasses'](ctypes.byref(self.handle), buffer)
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_retention_times(self):
        num_spectra = self.get_num_spectra()
        buffer = (ctypes.c_float * num_spectra)()
        err_no = bindings['DataReader::getRetentionTimes'](ctypes.byref(self.handle), buffer)
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)
    
    def get_TIC(self, index):
        return bindings['DataReader::getTIC'](ctypes.byref(self.handle), index)

    def get_spectrum(self, index):
        max_spectrum = self.get_num_spectra() - 1
        if index >= max_spectrum:
            raise IndexError(f'Requested index {index} needs to be smaller than {max_spectrum}.')
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings['DataReader::getSpectrum'](ctypes.byref(self.handle), index, buffer)
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)
    