import ctypes

from .constants import (
    CMS_NAMES, 
    AdvionCMSErrorCode, 
    InstrumentState, 
    OperationMode, 
    TuneParameter, 
    InstrumentSwitch, 
    BinaryReadback, 
    NumberReadback
)

lib = ctypes.cdll.LoadLibrary("./lib/Release/AdvionCMS.dll")

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