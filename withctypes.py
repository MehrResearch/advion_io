#%%
import ctypes
from enum import IntEnum
import logging
import numpy as np

logging.basicConfig(level=logging.DEBUG)

class AdvionDataErrorCode(IntEnum):
    OK = 0
    FILE_OPEN_FAILED = 1
    FILE_WRITE_FAILED = 2
    OUT_OF_MEMORY = 3
    CREATE_DATX_FAILED = 4
    OPEN_DATX_FAILED = 5
    CHANNEL_NOT_DEFINED = 6
    AUX_FILE_NOT_DEFINED = 7
    DATA_VERSION_TOO_HIGH = 8
    DATA_PARAMETER_IS_NULL = 9
    PARSING_FAILED = 10
    INDEX_OUT_OF_RANGE = 11
    PARAMETER_OUT_OF_RANGE = 12
    NO_SPECTRA = 13
    CHANNEL_HEADER_CLOSED = 14
    DATASET_FOLDER_LOCKED = 15
    PATH_TOO_LONG = 16

NAMES = {
    'DataReader': ('??0DataReader@AdvionData@@QEAA@PEBD_N1@Z', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool], None),
    'DataReader::getNumMasses': ('?getNumMasses@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getNumSpectra': ('?getNumSpectra@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getMasses': ('?getMasses@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getRetentionTimes': ('?getRetentionTimes@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getTIC': ('?getTIC@DataReader@AdvionData@@QEAAMH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_float),
}

EXAMPLE = b"data\\2024_7_1_14_0_16.datx"

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
        ret_val = bindings['DataReader'](ctypes.byref(self.handle), path, debug_output, decode_spectra)
        logging.debug('DataReader() returned %s', ret_val)

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

# %%
data = AdvionData(EXAMPLE, False, False)
data.get_num_masses(), data.get_num_spectra()
# %%
data.get_masses(), data.get_retention_times()