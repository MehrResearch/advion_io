import ctypes
from gzip import GzipFile
from pathlib import Path
import pickle

import numpy as np

from .constants import DATA_NAMES, AdvionDataErrorCode, get_dll_path

lib = ctypes.cdll.LoadLibrary(get_dll_path("AdvionData.dll"))

bindings = {}

for demangled, (mangled, arg_types, res_type) in DATA_NAMES.items():
    bindings[demangled] = lib[mangled]
    bindings[demangled].argtypes = arg_types
    bindings[demangled].restype = res_type


class AdvionData:
    def __init__(self, path, debug_output, decode_spectra):
        self.handle = ctypes.create_string_buffer(32)
        bindings["DataReader"](
            ctypes.byref(self.handle), path, debug_output, decode_spectra
        )
    
    def __del__(self):
        print('Freeing up AdvionData instance')
        bindings["~DataReader"](ctypes.byref(self.handle))

    def get_num_masses(self):
        return bindings["DataReader::getNumMasses"](ctypes.byref(self.handle))

    def get_num_spectra(self):
        return bindings["DataReader::getNumSpectra"](ctypes.byref(self.handle))

    def get_masses(self):
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings["DataReader::getMasses"](ctypes.byref(self.handle), buffer)
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_retention_times(self):
        num_spectra = self.get_num_spectra()
        buffer = (ctypes.c_float * num_spectra)()
        err_no = bindings["DataReader::getRetentionTimes"](
            ctypes.byref(self.handle), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_TIC(self, index):
        return bindings["DataReader::getTIC"](ctypes.byref(self.handle), index)

    def get_spectrum(self, index):
        max_spectrum = self.get_num_spectra() - 1
        if index > max_spectrum:
            raise IndexError(
                f"Requested index {index} needs to be smaller than {max_spectrum}."
            )
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings["DataReader::getSpectrum"](
            ctypes.byref(self.handle), index, buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)
    
    def set_delta_background_parameters(self, start_time, end_time, threshold, min_width, noise_offset):
        err_no = bindings["DataReader::setDeltaBackgroundParameters"](
            ctypes.byref(self.handle), start_time, end_time, threshold, min_width, noise_offset
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)

    def get_data_set_validity(self):
        err_no = bindings["DataReader::getDataSetValidity"](ctypes.byref(self.handle))
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)

    def get_date(self):
        result = bindings["DataReader::getDate"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_is_centroid(self):
        return bindings["DataReader::getIsCentroid"](ctypes.byref(self.handle))

    def get_delta_spectrum(self, index):
        max_spectrum = self.get_num_spectra() - 1
        if index > max_spectrum:
            raise IndexError(f"Requested index {index} needs to be smaller than {max_spectrum}.")
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings["DataReader::getDeltaSpectrum"](
            ctypes.byref(self.handle), index, buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_delta_background_spectrum(self):
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        err_no = bindings["DataReader::getDeltaBackgroundSpectrum"](
            ctypes.byref(self.handle), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_averaged_spectrum(self, spectra_indices):
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        indices_array = (ctypes.c_int * len(spectra_indices))(*spectra_indices)
        err_no = bindings["DataReader::getAveragedSpectrum"](
            ctypes.byref(self.handle), indices_array, len(spectra_indices), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_averaged_delta_spectrum(self, spectra_indices):
        num_masses = self.get_num_masses()
        buffer = (ctypes.c_float * num_masses)()
        indices_array = (ctypes.c_int * len(spectra_indices))(*spectra_indices)
        err_no = bindings["DataReader::getAveragedDeltaSpectrum"](
            ctypes.byref(self.handle), indices_array, len(spectra_indices), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def generate_xic(self, mass_indices):
        num_spectra = self.get_num_spectra()
        buffer = (ctypes.c_float * num_spectra)()
        indices_array = (ctypes.c_int * len(mass_indices))(*mass_indices)
        err_no = bindings["DataReader::generateXIC"](
            ctypes.byref(self.handle), indices_array, len(mass_indices), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def generate_delta_xic(self, mass_indices):
        num_spectra = self.get_num_spectra()
        buffer = (ctypes.c_float * num_spectra)()
        indices_array = (ctypes.c_int * len(mass_indices))(*mass_indices)
        err_no = bindings["DataReader::generateDeltaXIC"](
            ctypes.byref(self.handle), indices_array, len(mass_indices), buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_delta_ic(self, index):
        return bindings["DataReader::getDeltaIC"](ctypes.byref(self.handle), index)

    def get_software_version(self):
        result = bindings["DataReader::getSoftwareVersion"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_firmware_version(self):
        result = bindings["DataReader::getFirmwareVersion"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_hardware_type(self):
        result = bindings["DataReader::getHardwareType"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_instrument_id(self):
        result = bindings["DataReader::getInstrumentID"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_method_xml(self):
        result = bindings["DataReader::getMethodXML"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_experiment_xml(self):
        result = bindings["DataReader::getExperimentXML"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_icpms_experiment_xml(self):
        result = bindings["DataReader::getIcpmsExperimentXML"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_icpms_instrument_settings_xml(self):
        result = bindings["DataReader::getIcpmsInstrumentSettingsXML"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_scan_mode_index(self):
        return bindings["DataReader::getScanModeIndex"](ctypes.byref(self.handle))

    def get_num_segments(self):
        return bindings["DataReader::getNumSegments"](ctypes.byref(self.handle))

    def get_segment_time(self, index):
        return bindings["DataReader::getSegmentTime"](ctypes.byref(self.handle), index)

    def get_ion_source_optimization_xml(self, index=0):
        result = bindings["DataReader::getIonSourceOptimizationXML"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def get_tune_parameters_xml(self, index=0):
        result = bindings["DataReader::getTuneParametersXML"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def get_experiment_log(self):
        result = bindings["DataReader::getExperimentLog"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""

    def get_num_scalar_channels(self):
        return bindings["DataReader::getNumScalarChannels"](ctypes.byref(self.handle))

    def get_scalar_channel_name(self, index):
        result = bindings["DataReader::getScalarChannelName"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def get_scalar_channel_num_samples(self, index):
        return bindings["DataReader::getScalarChannelNumSamples"](ctypes.byref(self.handle), index)

    def get_scalar_channel_times(self, index):
        num_samples = self.get_scalar_channel_num_samples(index)
        buffer = (ctypes.c_float * num_samples)()
        err_no = bindings["DataReader::getScalarChannelTimes"](
            ctypes.byref(self.handle), index, buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_scalar_channel_values(self, index):
        num_samples = self.get_scalar_channel_num_samples(index)
        buffer = (ctypes.c_float * num_samples)()
        err_no = bindings["DataReader::getScalarChannelValues"](
            ctypes.byref(self.handle), index, buffer
        )
        if err_no != 0:
            err_code = AdvionDataErrorCode(err_no)
            raise IOError(err_code)
        return np.ctypeslib.as_array(buffer)

    def get_scalar_channel_num_attributes(self, index):
        return bindings["DataReader::getScalarChannelNumAttributes"](ctypes.byref(self.handle), index)

    def get_scalar_channel_attribute_name(self, index, attribute_index):
        result = bindings["DataReader::getScalarChannelAttributeName"](
            ctypes.byref(self.handle), index, attribute_index
        )
        return result.decode('utf-8') if result else ""

    def get_scalar_channel_attribute_value(self, index, attribute_index):
        return bindings["DataReader::getScalarChannelAttributeValue"](
            ctypes.byref(self.handle), index, attribute_index
        )

    def get_num_aux_files(self):
        return bindings["DataReader::getNumAuxFiles"](ctypes.byref(self.handle))

    def get_aux_file_name(self, index):
        result = bindings["DataReader::getAuxFileName"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def get_aux_file_type(self, index):
        result = bindings["DataReader::getAuxFileType"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def get_aux_file_text(self, index):
        result = bindings["DataReader::getAuxFileText"](ctypes.byref(self.handle), index)
        return result.decode('utf-8') if result else ""

    def save(self, path):
        with Path(path).open("wb") as p:
            with GzipFile(fileobj=p, mode='wb') as f:
                pickle.dump(
                    {
                        'masses': self.get_masses(),
                        'times': self.get_retention_times(),
                        'intensities': np.array([self.get_spectrum(index) for index in range(self.get_num_spectra())]),
                    },
                    f,
                )