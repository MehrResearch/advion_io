"""Shared enums for the advion_io package.

Each :class:`~enum.IntEnum` mirrors a corresponding ``enum`` in the
Advion API, so error codes, instrument states and parameter ids can be
compared by name rather than by magic number.  The data-side enums are
used by :mod:`advion_io.data_reader` and :mod:`advion_io.data_writer`;
the instrument-side enums are included for reference and for code that
talks to an instrument by other means.
"""
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

