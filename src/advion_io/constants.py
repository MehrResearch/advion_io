import ctypes
from enum import IntEnum


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
}