import ctypes
from enum import IntEnum
from pathlib import Path


def get_dll_path(dll_name):
    """Resolve DLL path relative to package location."""
    package_root = Path(__file__).parent.parent.parent
    dll_path = package_root / "lib" / "Release" / dll_name
    if not dll_path.exists():
        raise FileNotFoundError(f"DLL not found: expected {dll_path}")
    return str(dll_path)


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


class AdvionCMSErrorCode(IntEnum):
    CMS_OK = 0
    CMS_NO_USB_CONNECTION = 1
    CMS_USB_CONNECTED = 2
    CMS_LOST_USB_CONNECTION = 3
    CMS_INCOMPATIBLE_FIRMWARE = 4
    CMS_HIVOLT_OFF_BAD_VACUUM = 10
    CMS_STANDBY_IONSOURCE_REMOVED = 11
    CMS_STANDBY_IONSOURCE_UNPLUGGED = 12
    CMS_VACUUM_TOO_LOW = 13
    CMS_VACUUM_OK = 14
    CMS_ALREADY_ACQUIRING = 20
    CMS_ALREADY_PAUSED = 21
    CMS_NOT_ACQUIRING = 22
    CMS_NOT_PAUSED = 23
    CMS_NOT_WRITING_DATA = 24
    CMS_WRITE_FAILED = 25
    CMS_SWITCHING_NOT_ALLOWED = 26
    CMS_SEGMENTS_NOT_ALLOWED = 27
    CMS_SCAN_MODE_OUT_OF_RANGE = 28
    CMS_TUNE_INDEX_OUT_OF_RANGE = 30
    CMS_CONTROLLER_ALREADY_STARTED = 40
    CMS_CONTROLLER_NOT_STARTED = 41
    CMS_INSTRUMENT_IS_OPERATING = 42
    CMS_PUMP_ALREADY_ON = 43
    CMS_OPERATING_NOT_ALLOWED = 44
    CMS_STANDBY_NOT_ALLOWED = 45
    CMS_INSTRUMENT_NOT_OPERATING = 46
    CMS_PARSING_FAILED = 47
    CMS_INDEX_OUT_OF_RANGE = 48
    CMS_INSTRUMENT_TYPE_UNKNOWN = 49
    CMS_ALREADY_AUTO_TUNING = 50
    CMS_CANCELLED = 51
    CMS_PEAKS_NOT_FOUND = 52
    CMS_COULD_NOT_AUTOTUNE = 53
    CMS_NOT_ENOUGH_TUNING_MASSES = 54
    CMS_RANGE_SCAN_TIME_TOO_LOW = 60
    CMS_RANGE_SCAN_TIME_TOO_HIGH = 61
    CMS_SIM_DWELL_TIME_TOO_LOW = 62
    CMS_SIM_DWELL_TIME_TOO_HIGH = 63
    CMS_SCAN_SPEED_TOO_HIGH = 64
    CMS_SIM_NO_MASSES = 65
    CMS_DATA_READ_FAIL = 70
    CMS_INVALID_FILTER_PARAMS = 71
    CMS_PARAMETER_OUT_OF_RANGE = 80
    CMS_DATASET_FOLDER_LOCKED = 81
    CMS_PATH_TOO_LONG = 82
    CMS_NOT_LICENSED = 83
    CMS_NOT_SUPPORTED = 84


class InstrumentState(IntEnum):
    Fault = 0
    Initializing = 1
    Vented = 2
    PumpingDown = 3
    Standby = 4
    Operate = 5


class OperationMode(IntEnum):
    Idle = 0
    Tuning = 1
    AutoTuning = 2
    Acquiring = 3


class AcquisitionState(IntEnum):
    Prevented = 0
    Ready = 1
    Waiting = 2
    Underway = 3
    Paused = 4


class AcquisitionScanMode(IntEnum):
    ASM_Unknown = 0
    ASM_CMS_SIM = 1
    ASM_CMS_Range = 2


class TuneParameter(IntEnum):
    CapillaryTemperature = 0
    CapillaryVoltage = 1
    SourceGasTemperature = 2
    TransferLineTemperature = 3
    ESIVoltage = 4
    APCICoronaDischarge = 5
    SourceVoltageOffset = 6
    SourceVoltageSpan = 7
    ExtractionElectrode = 8
    HexapoleBias = 9
    HexapoleRFOffset = 10
    HexapoleRFSpan = 11
    IonEnergyOffset = 12
    IonEnergySpan = 13
    ResolutionOffset = 14
    ResolutionSpan = 15
    DetectorVoltage = 16


class InstrumentSwitch(IntEnum):
    PositiveIon = 0
    FullNebulizationGas = 1
    StandbyNebulizationGas = 2
    SourceGas = 3
    CapillaryHeater = 4
    SourceGasHeater = 5
    TransferLineHeater = 6
    PositiveCalibrant = 7
    NegativeCalibrant = 8
    UsingHelium = 9


class BinaryReadback(IntEnum):
    CommunicationOK = 0
    FirmwareVersionOK = 1
    PumpSpeedOK = 2
    VacuumOK = 3
    SafetySwitchOK = 4
    FIASignal = 5
    DigitalInput1 = 6
    DigitalInput2 = 7
    DigitalInput3 = 8
    DigitalInput4 = 9
    PumpPowerRB = 10
    HighVoltagesRB = 11
    PositiveIonRB = 12
    FullNebulizationGasRB = 13
    StandbyNebulizationGasRB = 14
    SourceGasRB = 15
    CapillaryHeaterRB = 16
    SourceGasHeaterRB = 17
    TransferLineHeaterRB = 18
    PositiveCalibrantRB = 19
    NegativeCalibrantRB = 20
    UsingHeliumRB = 21


class NumberReadback(IntEnum):
    PiraniPressureRB = 0
    TurboSpeedRB = 1
    CapillaryTemperatureRB = 2
    SourceGasTemperatureRB = 3
    TransferLineTemperatureRB = 4
    CapillaryVoltageRB = 5
    SourceVoltageRB = 6
    ExtractionElectrodeRB = 7
    HexapoleBiasRB = 8
    PoleBiasRB = 9
    HexapoleRFRB = 10
    RectifiedRFRB = 11
    ESIVoltageRB = 12
    APCICurrentRB = 13
    DetectorVoltageRB = 14
    DynodeVoltageRB = 15
    DC1RB = 16
    DC2RB = 17


class SeverityCode(IntEnum):
    CMS_SEVERITY_INFORMATION = 1
    CMS_SEVERITY_WARNING = 2
    CMS_SEVERITY_ERROR = 3
    CMS_SEVERITY_FATAL = 4


class OperatePreventer(IntEnum):
    NoCommunication = 0x00000001
    PumpOff = 0x00000002
    PumpSpeedTooLow = 0x00000004
    VacuumTooHigh = 0x00000008
    WaitingAfterPumpDown = 0x00000010
    NoIonSource = 0x00000020
    SafetySwitchTripped = 0x00000040
    IncompatibleFirmware = 0x00000080


class HardwareType(IntEnum):
    CMS = 0
    CMS_S = 1
    CMS_L = 2
    CMS_OEM = 3
    CMS_S_OEM = 4
    CMS_L_OEM = 5
    CMS_C = 6


class SourceType(IntEnum):
    NO_SOURCE = 0
    ESI_SOURCE = 1
    APCI_SOURCE = 2
    DART_SOURCE = 3
    VAPCI_SOURCE = 4
    ESI_OPSI_SOURCE = 5


class LicensableUpgrade(IntEnum):
    APCI_IonSource = 0
    ASAP_IonSource = 1
    ESI_OPSI_IonSource = 2
    Plate_Express_Peripheral = 3
    Isocratic_Pump_Peripheral = 4
    MRA_Valve_Peripheral = 5
    Avant_HPLC_Peripheral = 6


class HeaterId(IntEnum):
    CapillaryHeaterId = 0
    SourceGasHeaterId = 1
    TransferLineHeaterId = 2


class TuningLevel(IntEnum):
    ResolutionOnlyTune = 0
    RegularTune = 1
    FindPeaksTune = 2
    DetectorGainTune = 3


class TuningTask(IntEnum):
    TestingPerformance = 0
    Calibrating = 1
    CalculatingBaseline = 2
    CenteringPeaks = 3
    TuningExtractionElectrode = 4
    TuningHexapoleBias = 5
    TuningResolution = 6
    TuningIonEnergyAndResolution = 7
    TuningDetectorGain = 8


class MassCalibrationLevel(IntEnum):
    SlowSpeed = 0
    DefaultSpeed = 1
    HighSpeed = 2

DATA_NAMES = {
    'DataReader': ('??0DataReader@AdvionData@@QEAA@PEBD_N1@Z', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool], None),
    '~DataReader': ('??1DataReader@AdvionData@@QEAA@XZ', [ctypes.c_void_p], None),
    'DataReader::getNumMasses': ('?getNumMasses@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getNumSpectra': ('?getNumSpectra@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getMasses': ('?getMasses@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getRetentionTimes': ('?getRetentionTimes@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getTIC': ('?getTIC@DataReader@AdvionData@@QEAAMH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_float),
    'DataReader::getSpectrum': ('?getSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@HPEAM@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::setDeltaBackgroundParameters': ('?setDeltaBackgroundParameters@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@NNNNH@Z', [ctypes.c_void_p, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_int], ctypes.c_int),
    'DataReader::getDataSetValidity': ('?getDataSetValidity@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@XZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getDate': ('?getDate@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getIsCentroid': ('?getIsCentroid@DataReader@AdvionData@@QEAA_NXZ', [ctypes.c_void_p], ctypes.c_bool),
    'DataReader::getDeltaSpectrum': ('?getDeltaSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@HPEAM@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getDeltaBackgroundSpectrum': ('?getDeltaBackgroundSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getAveragedSpectrum': ('?getAveragedSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEBHHPEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getAveragedDeltaSpectrum': ('?getAveragedDeltaSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEBHHPEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::generateXIC': ('?generateXIC@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEBHHPEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::generateDeltaXIC': ('?generateDeltaXIC@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEBHHPEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_int), ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getDeltaIC': ('?getDeltaIC@DataReader@AdvionData@@QEAAMH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_float),
    'DataReader::getSoftwareVersion': ('?getSoftwareVersion@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getFirmwareVersion': ('?getFirmwareVersion@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getHardwareType': ('?getHardwareType@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getInstrumentID': ('?getInstrumentID@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getMethodXML': ('?getMethodXML@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getExperimentXML': ('?getExperimentXML@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getIcpmsExperimentXML': ('?getIcpmsExperimentXML@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getIcpmsInstrumentSettingsXML': ('?getIcpmsInstrumentSettingsXML@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getScanModeIndex': ('?getScanModeIndex@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getNumSegments': ('?getNumSegments@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getSegmentTime': ('?getSegmentTime@DataReader@AdvionData@@QEAANH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'DataReader::getIonSourceOptimizationXML': ('?getIonSourceOptimizationXML@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getTuneParametersXML': ('?getTuneParametersXML@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getExperimentLog': ('?getExperimentLog@DataReader@AdvionData@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'DataReader::getNumScalarChannels': ('?getNumScalarChannels@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getScalarChannelName': ('?getScalarChannelName@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getScalarChannelNumSamples': ('?getScalarChannelNumSamples@DataReader@AdvionData@@QEAAHH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
    'DataReader::getScalarChannelTimes': ('?getScalarChannelTimes@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@HPEAM@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getScalarChannelValues': ('?getScalarChannelValues@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@HPEAM@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getScalarChannelNumAttributes': ('?getScalarChannelNumAttributes@DataReader@AdvionData@@QEAAHH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_int),
    'DataReader::getScalarChannelAttributeName': ('?getScalarChannelAttributeName@DataReader@AdvionData@@QEAAPEBDHH@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getScalarChannelAttributeValue': ('?getScalarChannelAttributeValue@DataReader@AdvionData@@QEAANHH@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.c_int], ctypes.c_double),
    'DataReader::getNumAuxFiles': ('?getNumAuxFiles@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getAuxFileName': ('?getAuxFileName@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getAuxFileType': ('?getAuxFileType@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
    'DataReader::getAuxFileText': ('?getAuxFileText@DataReader@AdvionData@@QEAAPEBDH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_char_p),
}

CMS_NAMES = {
    # USBInstrument constructors
    'USBInstrument': ('??0USBInstrument@AdvionCMS@@QEAA@_N0@Z', [ctypes.c_void_p, ctypes.c_bool, ctypes.c_bool], None),
    '~USBInstrument': ('??1USBInstrument@AdvionCMS@@UEAA@XZ', [ctypes.c_void_p], None),
    
    # SimulatedInstrument constructors
    'SimulatedInstrument': ('??0SimulatedInstrument@AdvionCMS@@QEAA@PEBD@Z', [ctypes.c_void_p, ctypes.c_char_p], None),
    '~SimulatedInstrument': ('??1SimulatedInstrument@AdvionCMS@@UEAA@XZ', [ctypes.c_void_p], None),
    
    # InstrumentController static methods
    'InstrumentController::startController': ('?startController@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@PEAVInstrument@2@@Z', [ctypes.c_void_p], ctypes.c_int),
    'InstrumentController::stopController': ('?stopController@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'InstrumentController::getState': ('?getState@InstrumentController@AdvionCMS@@SA?AW4InstrumentState@2@XZ', [], ctypes.c_int),
    'InstrumentController::getOperationMode': ('?getOperationMode@InstrumentController@AdvionCMS@@SA?AW4OperationMode@2@XZ', [], ctypes.c_int),
    'InstrumentController::canOperate': ('?canOperate@InstrumentController@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'InstrumentController::canStandby': ('?canStandby@InstrumentController@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'InstrumentController::canVent': ('?canVent@InstrumentController@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'InstrumentController::canPumpDown': ('?canPumpDown@InstrumentController@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'InstrumentController::getOperatePreventers': ('?getOperatePreventers@InstrumentController@AdvionCMS@@SAIXZ', [], ctypes.c_uint),
    'InstrumentController::operate': ('?operate@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'InstrumentController::standby': ('?standby@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'InstrumentController::vent': ('?vent@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'InstrumentController::pumpDown': ('?pumpDown@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'InstrumentController::getSoftwareVersion': ('?getSoftwareVersion@InstrumentController@AdvionCMS@@SAPEBDXZ', [], ctypes.c_char_p),
    'InstrumentController::getTuneParameters': ('?getTuneParameters@InstrumentController@AdvionCMS@@SAPEADXZ', [], ctypes.c_char_p),
    'InstrumentController::setTuneParameters': ('?setTuneParameters@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@PEBD@Z', [ctypes.c_char_p], ctypes.c_int),
    'InstrumentController::getIonSourceOptimization': ('?getIonSourceOptimization@InstrumentController@AdvionCMS@@SAPEADXZ', [], ctypes.c_char_p),
    'InstrumentController::setIonSourceOptimization': ('?setIonSourceOptimization@InstrumentController@AdvionCMS@@SA?AW4ErrorCode@2@PEBD@Z', [ctypes.c_char_p], ctypes.c_int),
    
    # Instrument instance methods
    'Instrument::getBinaryReadback': ('?getBinaryReadback@Instrument@AdvionCMS@@QEAA_NW4BinaryReadback@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_bool),
    'Instrument::setInstrumentSwitchOn': ('?setInstrumentSwitchOn@Instrument@AdvionCMS@@QEAAXW4InstrumentSwitch@2@_N@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.c_bool], None),
    'Instrument::getTuneParameter': ('?getTuneParameter@Instrument@AdvionCMS@@QEAANW4TuneParameter@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::setTuneParameter': ('?setTuneParameter@Instrument@AdvionCMS@@QEAAXW4TuneParameter@2@N@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.c_double], None),
    'Instrument::getTuneParameterUserMin': ('?getTuneParameterUserMin@Instrument@AdvionCMS@@QEAANW4TuneParameter@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::getTuneParameterUserMax': ('?getTuneParameterUserMax@Instrument@AdvionCMS@@QEAANW4TuneParameter@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::getNumberReadback': ('?getNumberReadback@Instrument@AdvionCMS@@QEAANW4NumberReadback@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::getFirmwareVersion': ('?getFirmwareVersion@Instrument@AdvionCMS@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'Instrument::getSerialNumber': ('?getSerialNumber@Instrument@AdvionCMS@@QEAAPEBDXZ', [ctypes.c_void_p], ctypes.c_char_p),
    'Instrument::getMinMass': ('?getMinMass@Instrument@AdvionCMS@@QEAANXZ', [ctypes.c_void_p], ctypes.c_double),
    'Instrument::getMaxMass': ('?getMaxMass@Instrument@AdvionCMS@@QEAANXZ', [ctypes.c_void_p], ctypes.c_double),
    'Instrument::getMaxScanSpeed': ('?getMaxScanSpeed@Instrument@AdvionCMS@@QEAANXZ', [ctypes.c_void_p], ctypes.c_double),
    'Instrument::getPumpDownRemainingSeconds': ('?getPumpDownRemainingSeconds@Instrument@AdvionCMS@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'Instrument::readAnalogInput': ('?readAnalogInput@Instrument@AdvionCMS@@QEAANH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::getHardwareType': ('?getHardwareType@Instrument@AdvionCMS@@QEAA?AW4HardwareType@2@XZ', [ctypes.c_void_p], ctypes.c_int),
    'Instrument::getSourceType': ('?getSourceType@Instrument@AdvionCMS@@QEAA?AW4SourceType@2@XZ', [ctypes.c_void_p], ctypes.c_int),
    'Instrument::getSourceGasTemperatureUserMax': ('?getSourceGasTemperatureUserMax@Instrument@AdvionCMS@@QEAANW4SourceType@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_double),
    'Instrument::isHeaterTemperatureEquilibrated': ('?isHeaterTemperatureEquilibrated@Instrument@AdvionCMS@@QEAA_NW4HeaterId@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_bool),
    'Instrument::isHeaterTemperatureWithinMaximum': ('?isHeaterTemperatureWithinMaximum@Instrument@AdvionCMS@@QEAA_NW4HeaterId@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_bool),
    'Instrument::isLicensedUpgrade': ('?isLicensedUpgrade@Instrument@AdvionCMS@@QEAA_NW4LicensableUpgrade@2@@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_bool),
    
    # AcquisitionManager static methods
    'AcquisitionManager::canAcquireToFolder': ('?canAcquireToFolder@AcquisitionManager@AdvionCMS@@SA_NPEBD@Z', [ctypes.c_char_p], ctypes.c_bool),
    'AcquisitionManager::canPerformSwitching': ('?canPerformSwitching@AcquisitionManager@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'AcquisitionManager::canCalculateDeltaData': ('?canCalculateDeltaData@AcquisitionManager@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'AcquisitionManager::getMinRangeScanTime': ('?getMinRangeScanTime@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getMinSIMDwellTime': ('?getMinSIMDwellTime@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getMaxRangeScanTime': ('?getMaxRangeScanTime@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getMaxSIMDwellTime': ('?getMaxSIMDwellTime@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::start': ('?start@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@PEBD0000@Z', [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p], ctypes.c_int),
    'AcquisitionManager::startWithSwitching': ('?startWithSwitching@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@PEBD000000@Z', [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p, ctypes.c_char_p], ctypes.c_int),
    'AcquisitionManager::stop': ('?stop@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'AcquisitionManager::pause': ('?pause@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@_N@Z', [ctypes.c_bool], ctypes.c_int),
    'AcquisitionManager::resume': ('?resume@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@XZ', [], ctypes.c_int),
    'AcquisitionManager::extend': ('?extend@AcquisitionManager@AdvionCMS@@SAHH@Z', [ctypes.c_int], ctypes.c_int),
    'AcquisitionManager::isFinalizingData': ('?isFinalizingData@AcquisitionManager@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'AcquisitionManager::getState': ('?getState@AcquisitionManager@AdvionCMS@@SA?AW4AcquisitionState@2@XZ', [], ctypes.c_int),
    'AcquisitionManager::isUsingTwoIonSources': ('?isUsingTwoIonSources@AcquisitionManager@AdvionCMS@@SA_NXZ', [], ctypes.c_bool),
    'AcquisitionManager::getNumScanModes': ('?getNumScanModes@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getScanMode': ('?getScanMode@AcquisitionManager@AdvionCMS@@SA?AW4AcquisitionScanMode@2@H@Z', [ctypes.c_int], ctypes.c_int),
    'AcquisitionManager::getCurrentName': ('?getCurrentName@AcquisitionManager@AdvionCMS@@SAPEBDHH@Z', [ctypes.c_int, ctypes.c_int], ctypes.c_char_p),
    'AcquisitionManager::getCurrentFolder': ('?getCurrentFolder@AcquisitionManager@AdvionCMS@@SAPEBDXZ', [], ctypes.c_char_p),
    'AcquisitionManager::getMaxNumScans': ('?getMaxNumScans@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getMaxNumMasses': ('?getMaxNumMasses@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getRuntime': ('?getRuntime@AcquisitionManager@AdvionCMS@@SANXZ', [], ctypes.c_double),
    'AcquisitionManager::getTotalRunTime': ('?getTotalRunTime@AcquisitionManager@AdvionCMS@@SANXZ', [], ctypes.c_double),
    'AcquisitionManager::getNumScansDone': ('?getNumScansDone@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getLastScanIndex': ('?getLastScanIndex@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getLastScanModeIndex': ('?getLastScanModeIndex@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getLastScanIonSource': ('?getLastScanIonSource@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getLastRetentionTime': ('?getLastRetentionTime@AcquisitionManager@AdvionCMS@@SANXZ', [], ctypes.c_double),
    'AcquisitionManager::getLastNumMasses': ('?getLastNumMasses@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::getLastTIC': ('?getLastTIC@AcquisitionManager@AdvionCMS@@SANXZ', [], ctypes.c_double),
    'AcquisitionManager::getLastXIC': ('?getLastXIC@AcquisitionManager@AdvionCMS@@SANNN@Z', [ctypes.c_double, ctypes.c_double], ctypes.c_double),
    'AcquisitionManager::getLastDeltaIC': ('?getLastDeltaIC@AcquisitionManager@AdvionCMS@@SANXZ', [], ctypes.c_double),
    'AcquisitionManager::getLastDeltaXIC': ('?getLastDeltaXIC@AcquisitionManager@AdvionCMS@@SANNN@Z', [ctypes.c_double, ctypes.c_double], ctypes.c_double),
    'AcquisitionManager::getLastAnalogOutput': ('?getLastAnalogOutput@AcquisitionManager@AdvionCMS@@SANH_N@Z', [ctypes.c_int, ctypes.c_bool], ctypes.c_double),
    'AcquisitionManager::getLastSpectrumMasses': ('?getLastSpectrumMasses@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@PEAN@Z', [ctypes.POINTER(ctypes.c_double)], ctypes.c_int),
    'AcquisitionManager::getLastSpectrumIntensities': ('?getLastSpectrumIntensities@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@PEAN@Z', [ctypes.POINTER(ctypes.c_double)], ctypes.c_int),
    'AcquisitionManager::getLastDeltaSpectrumIntensities': ('?getLastDeltaSpectrumIntensities@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@PEAN@Z', [ctypes.POINTER(ctypes.c_double)], ctypes.c_int),
    'AcquisitionManager::getAcquisitionBinsPerAMU': ('?getAcquisitionBinsPerAMU@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::setAcquisitionBinsPerAMU': ('?setAcquisitionBinsPerAMU@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@H@Z', [ctypes.c_int], ctypes.c_int),
    'AcquisitionManager::getWriteBinsPerAMU': ('?getWriteBinsPerAMU@AcquisitionManager@AdvionCMS@@SAHXZ', [], ctypes.c_int),
    'AcquisitionManager::setWriteBinsPerAMU': ('?setWriteBinsPerAMU@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@H@Z', [ctypes.c_int], ctypes.c_int),
    'AcquisitionManager::createScalarChannel': ('?createScalarChannel@AcquisitionManager@AdvionCMS@@SAHPEBD@Z', [ctypes.c_char_p], ctypes.c_int),
    'AcquisitionManager::writeScalarEntry': ('?writeScalarEntry@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@HNN@Z', [ctypes.c_int, ctypes.c_double, ctypes.c_double], ctypes.c_int),
    'AcquisitionManager::writeScalarEntries': ('?writeScalarEntries@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@HPEAN0H@Z', [ctypes.c_int, ctypes.POINTER(ctypes.c_double), ctypes.POINTER(ctypes.c_double), ctypes.c_int], ctypes.c_int),
    'AcquisitionManager::createAuxiliaryFile': ('?createAuxiliaryFile@AcquisitionManager@AdvionCMS@@SAHPEBD0@Z', [ctypes.c_char_p, ctypes.c_char_p], ctypes.c_int),
    'AcquisitionManager::writeTextToFile': ('?writeTextToFile@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@HPEBD@Z', [ctypes.c_int, ctypes.c_char_p], ctypes.c_int),
    'AcquisitionManager::writeLogMessage': ('?writeLogMessage@AcquisitionManager@AdvionCMS@@SAXPEBD@Z', [ctypes.c_char_p], None),
    'AcquisitionManager::writeExperiment': ('?writeExperiment@AcquisitionManager@AdvionCMS@@SAXPEBD@Z', [ctypes.c_char_p], None),
    'AcquisitionManager::updateIonSourceOptimization': ('?updateIonSourceOptimization@AcquisitionManager@AdvionCMS@@SA?AW4ErrorCode@2@HPEBD@Z', [ctypes.c_int, ctypes.c_char_p], ctypes.c_int),
}