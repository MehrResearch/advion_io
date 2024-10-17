#%%
import ctypes
import logging

logging.basicConfig(level=logging.DEBUG)

NAMES = {
    'DataReader': ('??0DataReader@AdvionData@@QEAA@PEBD_N1@Z', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool], None),
    'DataReader::getNumMasses': ('?getNumMasses@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int)
}

EXAMPLE = b"2024_7_1_14_0_16.datx"

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
# %%
data = AdvionData(EXAMPLE, False, False)
data.get_num_masses()
# %%
