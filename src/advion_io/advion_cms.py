import ctypes
import numpy as np

from .constants import (
    CMS_NAMES, 
    AdvionCMSErrorCode, 
    InstrumentState, 
    OperationMode, 
    AcquisitionState,
    AcquisitionScanMode,
    TuneParameter, 
    InstrumentSwitch, 
    BinaryReadback, 
    NumberReadback,
    get_dll_path
)

lib = ctypes.cdll.LoadLibrary(get_dll_path("AdvionCMS.dll"))

cms_bindings = {}

for demangled, (mangled, arg_types, res_type) in CMS_NAMES.items():
    cms_bindings[demangled] = lib[mangled]
    cms_bindings[demangled].argtypes = arg_types
    cms_bindings[demangled].restype = res_type


class AdvionInstrument:
    def __init__(self, handle: ctypes.c_void_p):
        self.handle = handle
    
    def get_binary_readback(self, readback: BinaryReadback) -> bool:
        return cms_bindings["Instrument::getBinaryReadback"](ctypes.byref(self.handle), readback)
    
    def set_instrument_switch(self, switch: InstrumentSwitch, value: bool):
        cms_bindings["Instrument::setInstrumentSwitchOn"](ctypes.byref(self.handle), switch, value)
    
    def get_tune_parameter(self, param: TuneParameter) -> float:
        return cms_bindings["Instrument::getTuneParameter"](ctypes.byref(self.handle), param)
    
    def set_tune_parameter(self, param: TuneParameter, value: float):
        cms_bindings["Instrument::setTuneParameter"](ctypes.byref(self.handle), param, value)
    
    def get_tune_parameter_min(self, param: TuneParameter) -> float:
        return cms_bindings["Instrument::getTuneParameterUserMin"](ctypes.byref(self.handle), param)
    
    def get_tune_parameter_max(self, param: TuneParameter) -> float:
        return cms_bindings["Instrument::getTuneParameterUserMax"](ctypes.byref(self.handle), param)
    
    def get_number_readback(self, readback: NumberReadback) -> float:
        return cms_bindings["Instrument::getNumberReadback"](ctypes.byref(self.handle), readback)
    
    def get_firmware_version(self) -> str:
        result = cms_bindings["Instrument::getFirmwareVersion"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""
    
    def get_serial_number(self) -> str:
        result = cms_bindings["Instrument::getSerialNumber"](ctypes.byref(self.handle))
        return result.decode('utf-8') if result else ""
    
    def get_min_mass(self) -> float:
        return cms_bindings["Instrument::getMinMass"](ctypes.byref(self.handle))
    
    def get_max_mass(self) -> float:
        return cms_bindings["Instrument::getMaxMass"](ctypes.byref(self.handle))
    
    def get_max_scan_speed(self) -> float:
        return cms_bindings["Instrument::getMaxScanSpeed"](ctypes.byref(self.handle))
    
    def get_pump_down_remaining_seconds(self) -> int:
        return cms_bindings["Instrument::getPumpDownRemainingSeconds"](ctypes.byref(self.handle))
    
    def read_analog_input(self, line: int) -> float:
        return cms_bindings["Instrument::readAnalogInput"](ctypes.byref(self.handle), line)


class USBInstrument(AdvionInstrument):
    def __init__(self, auto_startup: bool = True, auto_detect: bool = True):
        self.handle = ctypes.create_string_buffer(256)  # Allocate space for the object
        cms_bindings["USBInstrument"](ctypes.byref(self.handle), auto_startup, auto_detect)
        super().__init__(self.handle)
    
    def __del__(self):
        if hasattr(self, 'handle'):
            print('Freeing USBInstrument instance')
            cms_bindings["~USBInstrument"](ctypes.byref(self.handle))


class SimulatedInstrument(AdvionInstrument):
    def __init__(self, config_file: str):
        self.handle = ctypes.create_string_buffer(256)  # Allocate space for the object
        cms_bindings["SimulatedInstrument"](ctypes.byref(self.handle), config_file.encode('utf-8'))
        super().__init__(self.handle)
    
    def __del__(self):
        if hasattr(self, 'handle'):
            print('Freeing SimulatedInstrument instance')
            cms_bindings["~SimulatedInstrument"](ctypes.byref(self.handle))


class AdvionInstrumentController:
    @staticmethod
    def start_controller(instrument: AdvionInstrument) -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::startController"](ctypes.byref(instrument.handle))
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def stop_controller() -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::stopController"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def get_state() -> InstrumentState:
        state = cms_bindings["InstrumentController::getState"]()
        return InstrumentState(state)
    
    @staticmethod
    def get_operation_mode() -> OperationMode:
        mode = cms_bindings["InstrumentController::getOperationMode"]()
        return OperationMode(mode)
    
    @staticmethod
    def can_operate() -> bool:
        return cms_bindings["InstrumentController::canOperate"]()
    
    @staticmethod
    def can_standby() -> bool:
        return cms_bindings["InstrumentController::canStandby"]()
    
    @staticmethod
    def can_vent() -> bool:
        return cms_bindings["InstrumentController::canVent"]()
    
    @staticmethod
    def can_pump_down() -> bool:
        return cms_bindings["InstrumentController::canPumpDown"]()
    
    @staticmethod
    def get_operate_preventers() -> int:
        return cms_bindings["InstrumentController::getOperatePreventers"]()
    
    @staticmethod
    def operate() -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::operate"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def standby() -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::standby"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def vent() -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::vent"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def pump_down() -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::pumpDown"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def get_software_version() -> str:
        result = cms_bindings["InstrumentController::getSoftwareVersion"]()
        return result.decode('utf-8') if result else ""
    
    @staticmethod
    def get_tune_parameters() -> str:
        result = cms_bindings["InstrumentController::getTuneParameters"]()
        return result.decode('utf-8') if result else ""
    
    @staticmethod
    def set_tune_parameters(tune_xml: str) -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::setTuneParameters"](tune_xml.encode('utf-8'))
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def get_ion_source_optimization() -> str:
        result = cms_bindings["InstrumentController::getIonSourceOptimization"]()
        return result.decode('utf-8') if result else ""
    
    @staticmethod
    def set_ion_source_optimization(ion_source_xml: str) -> AdvionCMSErrorCode:
        err_code = cms_bindings["InstrumentController::setIonSourceOptimization"](ion_source_xml.encode('utf-8'))
        return AdvionCMSErrorCode(err_code)


class AdvionAcquisitionManager:
    @staticmethod
    def can_acquire_to_folder(folder: str) -> bool:
        return cms_bindings["AcquisitionManager::canAcquireToFolder"](folder.encode('utf-8'))
    
    @staticmethod
    def can_perform_switching() -> bool:
        return cms_bindings["AcquisitionManager::canPerformSwitching"]()
    
    @staticmethod
    def can_calculate_delta_data() -> bool:
        return cms_bindings["AcquisitionManager::canCalculateDeltaData"]()
    
    @staticmethod
    def get_min_range_scan_time() -> int:
        return cms_bindings["AcquisitionManager::getMinRangeScanTime"]()
    
    @staticmethod
    def get_min_sim_dwell_time() -> int:
        return cms_bindings["AcquisitionManager::getMinSIMDwellTime"]()
    
    @staticmethod
    def get_max_range_scan_time() -> int:
        return cms_bindings["AcquisitionManager::getMaxRangeScanTime"]()
    
    @staticmethod
    def get_max_sim_dwell_time() -> int:
        return cms_bindings["AcquisitionManager::getMaxSIMDwellTime"]()
    
    @staticmethod
    def start(method_xml: str, ion_source_xml: str, tune_xml: str, name: str, folder: str | None = None) -> AdvionCMSErrorCode:
        folder_ptr = folder.encode('utf-8') if folder else ctypes.c_char_p(0)
        err_code = cms_bindings["AcquisitionManager::start"](
            method_xml.encode('utf-8'),
            ion_source_xml.encode('utf-8'),
            tune_xml.encode('utf-8'),
            name.encode('utf-8'),
            folder_ptr
        )
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def start_with_switching(method_xml: str, ion_source1_xml: str, ion_source2_xml: str,
                           tune1_xml: str, tune2_xml: str, name: str, folder: str | None = None) -> AdvionCMSErrorCode:
        folder_ptr = folder.encode('utf-8') if folder else ctypes.c_char_p(0)
        err_code = cms_bindings["AcquisitionManager::startWithSwitching"](
            method_xml.encode('utf-8'),
            ion_source1_xml.encode('utf-8'),
            ion_source2_xml.encode('utf-8'),
            tune1_xml.encode('utf-8'),
            tune2_xml.encode('utf-8'),
            name.encode('utf-8'),
            folder_ptr
        )
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def stop() -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::stop"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def pause(resume_on_digital_input: bool = False) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::pause"](resume_on_digital_input)
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def resume() -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::resume"]()
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def extend(seconds: int) -> int:
        return cms_bindings["AcquisitionManager::extend"](seconds)
    
    @staticmethod
    def is_finalizing_data() -> bool:
        return cms_bindings["AcquisitionManager::isFinalizingData"]()
    
    @staticmethod
    def get_state() -> AcquisitionState:
        state = cms_bindings["AcquisitionManager::getState"]()
        return AcquisitionState(state)
    
    @staticmethod
    def is_using_two_ion_sources() -> bool:
        return cms_bindings["AcquisitionManager::isUsingTwoIonSources"]()
    
    @staticmethod
    def get_num_scan_modes() -> int:
        return cms_bindings["AcquisitionManager::getNumScanModes"]()
    
    @staticmethod
    def get_scan_mode(scan_mode_index: int) -> AcquisitionScanMode:
        mode = cms_bindings["AcquisitionManager::getScanMode"](scan_mode_index)
        return AcquisitionScanMode(mode)
    
    @staticmethod
    def get_current_name(ion_source_index: int = 0, scan_mode_index: int = 0) -> str:
        result = cms_bindings["AcquisitionManager::getCurrentName"](ion_source_index, scan_mode_index)
        return result.decode('utf-8') if result else ""
    
    @staticmethod
    def get_current_folder() -> str:
        result = cms_bindings["AcquisitionManager::getCurrentFolder"]()
        return result.decode('utf-8') if result else ""
    
    @staticmethod
    def get_max_num_scans() -> int:
        return cms_bindings["AcquisitionManager::getMaxNumScans"]()
    
    @staticmethod
    def get_max_num_masses() -> int:
        return cms_bindings["AcquisitionManager::getMaxNumMasses"]()
    
    @staticmethod
    def get_runtime() -> float:
        return cms_bindings["AcquisitionManager::getRuntime"]()
    
    @staticmethod
    def get_total_run_time() -> float:
        return cms_bindings["AcquisitionManager::getTotalRunTime"]()
    
    @staticmethod
    def get_num_scans_done() -> int:
        return cms_bindings["AcquisitionManager::getNumScansDone"]()
    
    @staticmethod
    def get_last_scan_index() -> int:
        return cms_bindings["AcquisitionManager::getLastScanIndex"]()
    
    @staticmethod
    def get_last_scan_mode_index() -> int:
        return cms_bindings["AcquisitionManager::getLastScanModeIndex"]()
    
    @staticmethod
    def get_last_scan_ion_source() -> int:
        return cms_bindings["AcquisitionManager::getLastScanIonSource"]()
    
    @staticmethod
    def get_last_retention_time() -> float:
        return cms_bindings["AcquisitionManager::getLastRetentionTime"]()
    
    @staticmethod
    def get_last_num_masses() -> int:
        return cms_bindings["AcquisitionManager::getLastNumMasses"]()
    
    @staticmethod
    def get_last_tic() -> float:
        return cms_bindings["AcquisitionManager::getLastTIC"]()
    
    @staticmethod
    def get_last_xic(start_mass: float, end_mass: float) -> float:
        return cms_bindings["AcquisitionManager::getLastXIC"](start_mass, end_mass)
    
    @staticmethod
    def get_last_delta_ic() -> float:
        return cms_bindings["AcquisitionManager::getLastDeltaIC"]()
    
    @staticmethod
    def get_last_delta_xic(start_mass: float, end_mass: float) -> float:
        return cms_bindings["AcquisitionManager::getLastDeltaXIC"](start_mass, end_mass)
    
    @staticmethod
    def get_last_analog_output(line: int, return_processed: bool) -> float:
        return cms_bindings["AcquisitionManager::getLastAnalogOutput"](line, return_processed)
    
    @staticmethod
    def get_last_spectrum_masses() -> tuple[AdvionCMSErrorCode, np.ndarray]:
        num_masses = cms_bindings["AcquisitionManager::getLastNumMasses"]()
        if num_masses <= 0:
            return AdvionCMSErrorCode.CMS_OK, np.array([])
        
        masses_array = (ctypes.c_double * num_masses)()
        err_code = cms_bindings["AcquisitionManager::getLastSpectrumMasses"](masses_array)
        # Copy ctypes array to numpy array to ensure Python manages the memory
        masses = np.ctypeslib.as_array(masses_array).copy()
        return AdvionCMSErrorCode(err_code), masses
    
    @staticmethod
    def get_last_spectrum_intensities() -> tuple[AdvionCMSErrorCode, np.ndarray]:
        num_masses = cms_bindings["AcquisitionManager::getLastNumMasses"]()
        if num_masses <= 0:
            return AdvionCMSErrorCode.CMS_OK, np.array([])
        
        intensities_array = (ctypes.c_double * num_masses)()
        err_code = cms_bindings["AcquisitionManager::getLastSpectrumIntensities"](intensities_array)
        # Copy ctypes array to numpy array to ensure Python manages the memory
        intensities = np.ctypeslib.as_array(intensities_array).copy()
        return AdvionCMSErrorCode(err_code), intensities
    
    @staticmethod
    def get_last_delta_spectrum_intensities() -> tuple[AdvionCMSErrorCode, np.ndarray]:
        num_masses = cms_bindings["AcquisitionManager::getLastNumMasses"]()
        if num_masses <= 0:
            return AdvionCMSErrorCode.CMS_OK, np.array([])
        
        intensities_array = (ctypes.c_double * num_masses)()
        err_code = cms_bindings["AcquisitionManager::getLastDeltaSpectrumIntensities"](intensities_array)
        # Copy ctypes array to numpy array to ensure Python manages the memory
        intensities = np.ctypeslib.as_array(intensities_array).copy()
        return AdvionCMSErrorCode(err_code), intensities
    
    @staticmethod
    def get_acquisition_bins_per_amu() -> int:
        return cms_bindings["AcquisitionManager::getAcquisitionBinsPerAMU"]()
    
    @staticmethod
    def set_acquisition_bins_per_amu(bins_per_amu: int) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::setAcquisitionBinsPerAMU"](bins_per_amu)
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def get_write_bins_per_amu() -> int:
        return cms_bindings["AcquisitionManager::getWriteBinsPerAMU"]()
    
    @staticmethod
    def set_write_bins_per_amu(bins_per_amu: int) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::setWriteBinsPerAMU"](bins_per_amu)
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def create_scalar_channel(name: str) -> int:
        return cms_bindings["AcquisitionManager::createScalarChannel"](name.encode('utf-8'))
    
    @staticmethod
    def write_scalar_entry(channel_id: int, time: float, value: float) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::writeScalarEntry"](channel_id, time, value)
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def write_scalar_entries(channel_id: int, times: np.ndarray | list[float], values: np.ndarray | list[float]) -> AdvionCMSErrorCode:
        # Convert to numpy arrays if needed
        times_np = np.asarray(times, dtype=np.float64)
        values_np = np.asarray(values, dtype=np.float64)
        
        if len(times_np) != len(values_np):
            raise ValueError("Times and values arrays must have the same length")
        
        num_entries = len(times_np)
        # Create ctypes arrays from numpy arrays
        times_array = (ctypes.c_double * num_entries)(*times_np)
        values_array = (ctypes.c_double * num_entries)(*values_np)
        
        err_code = cms_bindings["AcquisitionManager::writeScalarEntries"](
            channel_id, times_array, values_array, num_entries
        )
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def create_auxiliary_file(name: str, file_type: str) -> int:
        return cms_bindings["AcquisitionManager::createAuxiliaryFile"](
            name.encode('utf-8'), file_type.encode('utf-8')
        )
    
    @staticmethod
    def write_text_to_file(file_id: int, text: str) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::writeTextToFile"](file_id, text.encode('utf-8'))
        return AdvionCMSErrorCode(err_code)
    
    @staticmethod
    def write_log_message(text: str):
        cms_bindings["AcquisitionManager::writeLogMessage"](text.encode('utf-8'))
    
    @staticmethod
    def write_experiment(experiment_xml: str):
        cms_bindings["AcquisitionManager::writeExperiment"](experiment_xml.encode('utf-8'))
    
    @staticmethod
    def update_ion_source_optimization(ion_source_index: int, ion_source_xml: str) -> AdvionCMSErrorCode:
        err_code = cms_bindings["AcquisitionManager::updateIonSourceOptimization"](
            ion_source_index, ion_source_xml.encode('utf-8')
        )
        return AdvionCMSErrorCode(err_code)


