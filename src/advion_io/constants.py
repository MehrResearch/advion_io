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

NAMES = {
    'DataReader': ('??0DataReader@AdvionData@@QEAA@PEBD_N1@Z', [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_bool, ctypes.c_bool], None),
    'DataReader::getNumMasses': ('?getNumMasses@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getNumSpectra': ('?getNumSpectra@DataReader@AdvionData@@QEAAHXZ', [ctypes.c_void_p], ctypes.c_int),
    'DataReader::getMasses': ('?getMasses@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getRetentionTimes': ('?getRetentionTimes@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@PEAM@Z', [ctypes.c_void_p, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
    'DataReader::getTIC': ('?getTIC@DataReader@AdvionData@@QEAAMH@Z', [ctypes.c_void_p, ctypes.c_int], ctypes.c_float),
    'DataReader::getSpectrum': ('?getSpectrum@DataReader@AdvionData@@QEAA?AW4ErrorCode@2@HPEAM@Z', [ctypes.c_void_p, ctypes.c_int, ctypes.POINTER(ctypes.c_float)], ctypes.c_int),
}