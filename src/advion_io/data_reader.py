"""Pure-Python reader for Advion ``.datx`` mass-spectrometry data sets.

This module is the read-side counterpart to :mod:`advion_io.data_writer`.
Two layers are exposed:

* :class:`DatxFile` \u2014 thin container that opens a ``.datx`` archive,
  exposes the m/z axis, retention times and per-scan intensities, and
  hands back the metadata XML payloads.  Useful when you just want the
  numbers.
* :class:`DataReader` \u2014 high-fidelity Advion-shaped API on top of
  :class:`DatxFile`.  Method names and return types match the Advion
  reference implementation, so existing code written against it needs
  no changes.

Usage
-----
.. code-block:: python

    from advion_io import DataReader, DatxFile

    with DataReader("acquisition.datx") as dr:
        masses = dr.get_masses()
        for i in range(dr.get_num_spectra()):
            spectrum = dr.get_spectrum(i)
            ...

    with DatxFile("acquisition.datx") as dx:
        intensities = dx.intensities    # (num_spectra, num_masses) float32

The per-scan binary format used inside ``.spectra`` is decoded by
:func:`decode_intensities_blob`; the inverse (encoding) lives in
:func:`advion_io.data_writer.encode_intensities_blob`.
"""
from __future__ import annotations

import re
import struct
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Sequence
from xml.etree import ElementTree as ET

import numpy as np

from .constants import AdvionDataErrorCode

__all__ = [
    "DataReader",
    "DatxFile",
    "ScanIndex",
    "decode_intensities_blob",
]


# ---------------------------------------------------------------------------
# Lightweight helpers
# ---------------------------------------------------------------------------

# Per-scan entries inside ``.scans`` look like
#   <scan><time>T</time><index>I</index><size>S</size><tic>X</tic></scan>
# A regex is faster and friendlier than full XML parsing for this part.
_SCAN_RE = re.compile(
    r"<time>\s*([\d.eE+\-]+)\s*</time>"
    r"\s*<index>\s*(\d+)\s*</index>"
    r"\s*<size>\s*(\d+)\s*</size>"
    r"\s*<tic>\s*([\d.eE+\-]+)\s*</tic>",
)


def _strip_ns(tag: str) -> str:
    """Return the local tag name (``{ns}foo`` \u2192 ``foo``)."""
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


@dataclass(frozen=True)
class ScanIndex:
    """Index entry for one scan inside the ``.spectra`` blob."""

    time: float          # retention time (units as written by the source)
    offset: int          # byte offset into the ``.spectra`` blob
    size: int            # encoded size in bytes
    tic: float           # advertised total ion current


# ---------------------------------------------------------------------------
# Per-scan decoder
# ---------------------------------------------------------------------------
#
# The on-disk layout for one scan inside ``.spectra``:
#
#   * 14-byte header:
#       uint8  m0   bit width of the run-length values (~9-11)
#       uint8  m1   bit width of the base-intensity values (~25-29)
#       uint32 a    number of non-zero base values (length of stream2)
#       uint32 b    number of run-length groups   (length of stream1)
#       uint32 c    bitmap length in bytes        (= ceil(num_samples / 8))
#   * c bytes bitmap (LSB-first within each byte; only the first b bits
#     are used).  Bit g == 1 means "group g has a base value of zero",
#     == 0 means "the next entry of stream2 is the base value".
#   * stream1: b values of m0 bits each, LSB-first.  These are run
#     lengths.  Their sum equals num_samples minus the total number of
#     delta extensions.
#   * stream2: a values of m1 bits each, LSB-first.  These are the
#     non-zero base intensities.
#   * int32 base_count: total number of signed-byte deltas in the scan.
#   * nibbles: ceil(a/2) bytes; one 4-bit nibble per stream2 entry,
#     low-nibble first.  The nibble for group g is the number of
#     delta-encoded samples that follow group g's base value.
#   * deltas: base_count signed int8 bytes, consumed in order.


def _read_bits(buf: bytes, bit_offset: int, count: int, width: int) -> np.ndarray:
    """Read ``count`` LSB-first unsigned integers of ``width`` bits each.

    Uses :func:`numpy.unpackbits` (MSB-first per byte) with a bit-reverse
    lookup, which is dramatically faster than the obvious Python loop.
    """
    if count == 0:
        return np.zeros(0, dtype=np.int64)
    total_bits = count * width
    first_byte = bit_offset >> 3
    last_byte = (bit_offset + total_bits + 7) >> 3
    slab = np.frombuffer(bytes(buf[first_byte:last_byte]), dtype=np.uint8)
    bits = np.unpackbits(_BIT_REVERSE_TABLE[slab])
    start = bit_offset - first_byte * 8
    bits = bits[start : start + total_bits].reshape(count, width)
    weights = np.int64(1) << np.arange(width, dtype=np.int64)
    return bits.astype(np.int64) @ weights


_BIT_REVERSE_TABLE = np.array(
    [int(f"{i:08b}"[::-1], 2) for i in range(256)], dtype=np.uint8
)


def decode_intensities_blob(
    chunk: bytes | memoryview,
    samples_per_scan: int,
) -> np.ndarray:
    """Decode one scan from its raw ``.spectra`` byte slice.

    Parameters
    ----------
    chunk:
        Bytes for a single scan, sliced from the ``.spectra`` blob using
        the ``index`` and ``size`` fields of the corresponding scan
        entry in the ``.scans`` XML.
    samples_per_scan:
        ``samplesPerScan`` from the ``.scans`` XML (typically 11999 for
        an m/z 100\u2013700 acquisition at 0.05 spacing).

    Returns
    -------
    numpy.ndarray
        Shape ``(samples_per_scan,)``, dtype ``float32``; values match
        what the Advion reference implementation hands back for the same
        scan.
    """
    if len(chunk) < 14:
        raise ValueError("scan chunk too short for header")

    m0 = chunk[0]
    m1 = chunk[1]
    a, b, c = struct.unpack_from("<III", chunk, 2)

    off_bitmap = 14
    off_s1 = off_bitmap + c
    s1_bytes = (b * m0 + 7) // 8
    off_s2 = off_s1 + s1_bytes
    s2_bytes = (a * m1 + 7) // 8
    off_base_count = off_s2 + s2_bytes
    base_count = struct.unpack_from("<i", chunk, off_base_count)[0]
    off_nib = off_base_count + 4
    nib_bytes = (a + 1) // 2
    off_delta = off_nib + nib_bytes

    expected_size = off_delta + base_count
    if len(chunk) != expected_size:
        raise ValueError(
            f"scan size {len(chunk)} != expected {expected_size} "
            f"(m0={m0}, m1={m1}, a={a}, b={b}, c={c}, base_count={base_count})"
        )

    stream1 = _read_bits(chunk, off_s1 * 8, b, m0)
    stream2 = _read_bits(chunk, off_s2 * 8, a, m1)

    out = np.zeros(samples_per_scan, dtype=np.int64)
    out_idx = 0
    s2_idx = 0
    nib_idx = -1
    d_idx = 0
    d_used = 0

    bitmap = chunk  # accessed via offsets below
    nibbles_start = off_nib
    deltas_start = off_delta

    for g in range(b):
        bit = (bitmap[off_bitmap + (g >> 3)] >> (g & 7)) & 1
        if bit == 0:
            v = stream2[s2_idx]
            if s2_idx < a:
                nib_idx += 1
                s2_idx += 1
        else:
            v = 0

        if out_idx >= samples_per_scan:
            break

        if stream1[g] > 0:
            out[out_idx] = v

        if v != 0:
            nb = bitmap[nibbles_start + (nib_idx >> 1)]
            ext = (nb >> 4) & 0xF if (nib_idx & 1) else (nb & 0xF)
            for k in range(ext):
                if d_used >= base_count:
                    break
                db = bitmap[deltas_start + d_idx]
                if db >= 128:
                    db -= 256
                if out_idx + 1 + k >= samples_per_scan:
                    break
                out[out_idx + 1 + k] = out[out_idx + k] + db
                d_idx += 1
                d_used += 1
            out_idx += ext

        # Run-length pad: ``stream1[g] - 1`` more copies of ``v``.
        for k in range(1, stream1[g]):
            pos = out_idx + k
            if pos >= samples_per_scan:
                break
            out[pos] = v

        out_idx += stream1[g]

    return out.astype(np.float32, copy=False)


# ---------------------------------------------------------------------------
# Low-level archive accessor
# ---------------------------------------------------------------------------


class DatxFile:
    """Read an Advion ``.datx`` archive without any vendor code.

    The class can be used as a context manager.  Once opened, all the
    interesting binary parts of the archive are kept in memory; for a
    typical ~2 MB file this is fine.  Spectra are decoded lazily and
    cached.
    """

    # File extensions inside the archive.  Each archive contains a
    # single inner directory named like the archive itself.
    _SCANS_EXT = ".scans"
    _MASSES_EXT = ".masses"
    _SPECTRA_EXT = ".spectra"
    _META_EXT = ".meta"
    _LOG_EXT = ".log"
    _METHOD_EXT = ".method"
    _TUNE_EXT = ".tune"
    _ION_EXT = ".ion"

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self._files: dict[str, bytes] = {}
        self._load()

        scans_xml = self._text(self._SCANS_EXT)
        self.samples_per_scan = self._extract_int(scans_xml, "samplesPerScan")
        self.data_type = self._extract_text(scans_xml, "dataType")
        self.store_as_float = (
            self._extract_text(scans_xml, "storeAsFloat", "").lower() == "true"
        )
        self.software_version = self._extract_text(scans_xml, "softwareVersion", "")
        self.firmware_version = self._extract_text(scans_xml, "firmwareVersion", "")
        self.hardware_id = self._extract_text(scans_xml, "hardwareID", "")
        self.date = self._extract_text(scans_xml, "date", "")

        self.scans: list[ScanIndex] = [
            ScanIndex(time=float(t), offset=int(o), size=int(s), tic=float(tic))
            for t, o, s, tic in _SCAN_RE.findall(scans_xml)
        ]

        self._spectra_cache: list[np.ndarray | None] = [None] * len(self.scans)
        self._all_intensities: np.ndarray | None = None

    # -- context manager helpers ----------------------------------------

    def __enter__(self) -> "DatxFile":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        """Drop all cached data and references."""
        self._files.clear()
        self._spectra_cache = []
        self._all_intensities = None

    # -- public API -----------------------------------------------------

    @property
    def num_spectra(self) -> int:
        """Number of acquired scans."""
        return len(self.scans)

    @property
    def num_masses(self) -> int:
        """Number of m/z samples per scan."""
        return int(self.samples_per_scan)

    @property
    def masses(self) -> np.ndarray:
        """The m/z axis as a 1-D ``float32`` array of length ``num_masses``."""
        raw = self._files[self._MASSES_EXT]
        return np.frombuffer(raw, dtype="<f4").copy()

    @property
    def retention_times(self) -> np.ndarray:
        """Retention times as a 1-D ``float32`` array."""
        return np.array([s.time for s in self.scans], dtype=np.float32)

    @property
    def tic(self) -> np.ndarray:
        """Total ion current values as stored in the ``.scans`` index."""
        return np.array([s.tic for s in self.scans], dtype=np.float64)

    def get_spectrum(self, index: int) -> np.ndarray:
        """Return the decoded intensities for scan ``index`` as ``float32``."""
        if index < 0 or index >= self.num_spectra:
            raise IndexError(
                f"spectrum index {index} out of range [0, {self.num_spectra})"
            )
        cached = self._spectra_cache[index]
        if cached is not None:
            return cached
        scan = self.scans[index]
        blob = self._files[self._SPECTRA_EXT]
        chunk = blob[scan.offset : scan.offset + scan.size]
        spectrum = decode_intensities_blob(chunk, self.samples_per_scan)
        self._spectra_cache[index] = spectrum
        return spectrum

    @property
    def intensities(self) -> np.ndarray:
        """Full ``(num_spectra, num_masses)`` matrix of intensities.

        Decoded lazily on first access and cached.
        """
        if self._all_intensities is None:
            arr = np.empty((self.num_spectra, self.num_masses), dtype=np.float32)
            for i in range(self.num_spectra):
                arr[i] = self.get_spectrum(i)
            self._all_intensities = arr
        return self._all_intensities

    def iter_spectra(self) -> Iterator[np.ndarray]:
        """Yield decoded scans one at a time (no full-matrix allocation)."""
        for i in range(self.num_spectra):
            yield self.get_spectrum(i)

    def get_averaged_spectrum(self, indices: Sequence[int]) -> np.ndarray:
        """Return the mean spectrum over the given scan indices."""
        if len(indices) == 0:
            raise ValueError("indices must be non-empty")
        acc = np.zeros(self.num_masses, dtype=np.float64)
        for i in indices:
            acc += self.get_spectrum(i)
        return (acc / len(indices)).astype(np.float32)

    def generate_xic(self, mass_indices: Sequence[int]) -> np.ndarray:
        """Sum intensities over a set of mass indices across every scan."""
        xic = np.zeros(self.num_spectra, dtype=np.float64)
        mass_indices = np.asarray(list(mass_indices), dtype=np.int64)
        for i in range(self.num_spectra):
            spec = self.get_spectrum(i)
            xic[i] = spec[mass_indices].sum()
        return xic.astype(np.float32)

    # -- Optional access to text files inside the archive --------------

    @property
    def method_xml(self) -> str:
        return self._text(self._METHOD_EXT, "")

    @property
    def tune_xml(self) -> str:
        return self._text(self._TUNE_EXT, "")

    @property
    def ion_source_xml(self) -> str:
        return self._text(self._ION_EXT, "")

    @property
    def meta_xml(self) -> str:
        return self._text(self._META_EXT, "")

    @property
    def experiment_log(self) -> str:
        return self._text(self._LOG_EXT, "")

    def list_files(self) -> list[str]:
        """Return the inner file names (full paths) present in the archive."""
        return [k for k in self._files if "/" in k]

    # -- internals ------------------------------------------------------

    def _load(self) -> None:
        """Load every member of the ``.datx`` archive into memory.

        Each entry is indexed three ways for convenience: by full path
        (``"<stem>/<stem>.spectra"``), by basename
        (``"<stem>.spectra"``) and by extension (``".spectra"``).
        """
        with zipfile.ZipFile(self.path, "r") as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                blob = zf.read(info)
                name = info.filename
                basename = name.rsplit("/", 1)[-1]
                self._files[name] = blob
                self._files.setdefault(basename, blob)
                if "." in basename:
                    ext = "." + basename.rsplit(".", 1)[-1]
                    # First file with this extension wins.
                    self._files.setdefault(ext, blob)

        required = (self._SCANS_EXT, self._MASSES_EXT, self._SPECTRA_EXT)
        missing = [e for e in required if e not in self._files]
        if missing:
            raise ValueError(f"{self.path}: missing required entries {missing}")

    def _raw(self, key: str, default: bytes | None = None) -> bytes | None:
        """Return the raw bytes of a member by ext, basename, or full path."""
        return self._files.get(key, default)

    def _text(self, ext: str, default: str | None = None) -> str:
        data = self._files.get(ext)
        if data is None:
            if default is None:
                raise KeyError(f"{ext} not present in {self.path}")
            return default
        return data.decode("utf-8")

    @staticmethod
    def _extract_text(xml: str, tag: str, default: str | None = None) -> str:
        """Return the text content of ``<tag>...</tag>`` in ``xml``."""
        m = re.search(
            rf"<{re.escape(tag)}>\s*(.*?)\s*</{re.escape(tag)}>", xml, re.DOTALL,
        )
        if m is None:
            if default is None:
                raise KeyError(f"<{tag}> not found")
            return default
        return m.group(1)

    @classmethod
    def _extract_int(cls, xml: str, tag: str) -> int:
        return int(cls._extract_text(xml, tag))


# ---------------------------------------------------------------------------
# Advion-shaped DataReader API
# ---------------------------------------------------------------------------


class DataReader:
    """Read an Advion mass-spectrometry ``.datx`` data set.

    The public surface (method names, return shapes, error semantics)
    matches the Advion reference implementation of
    ``AdvionData::DataReader``, so callers written against it require
    no changes.

    Parameters
    ----------
    path:
        Path to a ``.datx`` archive (``bytes`` or ``str`` accepted).
        Folder-style inputs are not supported.
    debug_output:
        Accepted for API compatibility; this reader does not emit
        debug output.
    decode_spectra:
        Accepted for API compatibility.  When true, every scan is
        decoded eagerly into the in-memory cache so subsequent
        ``get_spectrum`` calls are O(1).
    """

    # ------------------------------------------------------------------
    # Construction / destruction
    # ------------------------------------------------------------------

    def __init__(
        self,
        path: str | bytes | Path,
        debug_output: bool = False,
        decode_spectra: bool = False,
    ) -> None:
        if isinstance(path, bytes):
            path = path.decode("utf-8")
        self.path = Path(path)
        self.debug_output = bool(debug_output)
        self.decode_spectra = bool(decode_spectra)

        self._dx = DatxFile(self.path)

        # Lazily-parsed metadata caches.
        self._segments: list[_Segment] | None = None
        self._scalar_channels: list[_ScalarChannel] | None = None
        self._aux_files: list[_AuxFile] | None = None
        self._is_centroid: bool | None = None

        # Peak Express delta-background state.  The Advion contract is
        # "set parameters, then ask for delta data"; we honour that by
        # keeping the background uncomputed until the user touches
        # either side.
        self._bg_start_time = 0.0
        self._bg_end_time = 0.0
        self._bg_threshold = 1.0
        self._bg_min_width = 0.05
        self._bg_noise_offset = 0
        self._bg_dirty = True
        self._bg_spectrum: np.ndarray | None = None

        if self.decode_spectra:
            _ = self._dx.intensities  # forces full decode + caching

    def close(self) -> None:
        """Release any resources held by the reader."""
        if self._dx is not None:
            self._dx.close()
            self._dx = None  # type: ignore[assignment]

    def __enter__(self) -> "DataReader":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    # ------------------------------------------------------------------
    # Validity / basic shape
    # ------------------------------------------------------------------

    def get_data_set_validity(self) -> None:
        """Raise :class:`IOError` mirroring ``ADVIONDATA_NO_SPECTRA`` etc."""
        if self._dx is None:
            raise IOError(AdvionDataErrorCode.FILE_OPEN_FAILED)
        if self._dx.num_masses <= 0:
            raise IOError(AdvionDataErrorCode.NO_SPECTRA)
        if self._dx.num_spectra <= 0:
            raise IOError(AdvionDataErrorCode.NO_SPECTRA)

    def get_num_masses(self) -> int:
        return self._dx.num_masses

    def get_num_spectra(self) -> int:
        return self._dx.num_spectra

    def get_is_centroid(self) -> bool:
        if self._is_centroid is None:
            self._is_centroid = (self._dx.data_type or "").lower() == "centroid"
        return self._is_centroid

    def get_date(self) -> str:
        return self._dx.date

    def get_software_version(self) -> str:
        return self._dx.software_version

    def get_firmware_version(self) -> str:
        return self._dx.firmware_version

    def get_hardware_type(self) -> str:
        """Return the hardware type recorded in the ``.meta`` file."""
        try:
            root = ET.fromstring(self._dx.meta_xml)
        except ET.ParseError:
            return ""
        for el in root.iter():
            if _strip_ns(el.tag) == "hardwareType":
                return (el.text or "").strip()
        return ""

    def get_instrument_id(self) -> str:
        return self._dx.hardware_id

    # ------------------------------------------------------------------
    # Mass / time / spectrum access
    # ------------------------------------------------------------------

    def get_masses(self) -> np.ndarray:
        """Return the m/z axis as a float32 array of length ``getNumMasses``."""
        return self._dx.masses

    def get_retention_times(self) -> np.ndarray:
        """Return the retention times as a float32 array of length ``getNumSpectra``."""
        return self._dx.retention_times

    def get_TIC(self, index: int) -> float:
        """Return the TIC recorded for ``index`` in the ``.scans`` XML.

        This is the value stored at acquisition time, not the recomputed
        sum of decoded intensities (they differ by ~1 ULP because of
        the int \u2192 float32 cast in :meth:`get_spectrum`).
        """
        self._check_spectrum_index(index)
        return float(self._dx.scans[index].tic)

    def get_spectrum(self, index: int) -> np.ndarray:
        self._check_spectrum_index(index)
        return self._dx.get_spectrum(index)

    def get_averaged_spectrum(self, spectra_indices: Sequence[int]) -> np.ndarray:
        if len(spectra_indices) == 0:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        for i in spectra_indices:
            self._check_spectrum_index(int(i))
        return self._dx.get_averaged_spectrum([int(i) for i in spectra_indices])

    def generate_xic(self, mass_indices: Sequence[int]) -> np.ndarray:
        for m in mass_indices:
            self._check_mass_index(int(m))
        return self._dx.generate_xic([int(m) for m in mass_indices])

    # ------------------------------------------------------------------
    # Peak Express delta background / delta spectrum
    # ------------------------------------------------------------------

    def set_delta_background_parameters(
        self,
        start_time: float,
        end_time: float,
        threshold: float,
        min_width: float,
        noise_offset: int,
    ) -> None:
        """Configure the Peak Express delta background calculation.

        ``startTime >= 0`` and ``< endTime``; ``threshold >= 1``;
        ``minWidth >= 0.05``.  Out-of-range parameters raise
        ``IOError(ADVIONDATA_PARAMETER_OUT_OF_RANGE)``.
        """
        if start_time < 0 or start_time >= end_time:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        if threshold < 1:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        if min_width < 0.05:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        self._bg_start_time = float(start_time)
        self._bg_end_time = float(end_time)
        self._bg_threshold = float(threshold)
        self._bg_min_width = float(min_width)
        self._bg_noise_offset = int(noise_offset)
        self._bg_dirty = True
        self._bg_spectrum = None

    def get_delta_background_spectrum(self) -> np.ndarray:
        """Return the current Peak Express delta-background spectrum."""
        self._ensure_background()
        assert self._bg_spectrum is not None
        return self._bg_spectrum.copy()

    def get_delta_spectrum(self, index: int) -> np.ndarray:
        """Return the Peak Express delta signals for one spectrum."""
        self._check_spectrum_index(index)
        bg = self._ensure_background()
        spec = self._dx.get_spectrum(index)
        return self._compute_delta(spec, bg)

    def get_averaged_delta_spectrum(self, spectra_indices: Sequence[int]) -> np.ndarray:
        if len(spectra_indices) == 0:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        bg = self._ensure_background()
        acc = np.zeros(self.get_num_masses(), dtype=np.float64)
        n = 0
        for i in spectra_indices:
            i = int(i)
            self._check_spectrum_index(i)
            acc += self._compute_delta(self._dx.get_spectrum(i), bg)
            n += 1
        if n > 1:
            acc /= n
        return acc.astype(np.float32)

    def generate_delta_xic(self, mass_indices: Sequence[int]) -> np.ndarray:
        bg = self._ensure_background()
        cols = np.asarray([int(m) for m in mass_indices], dtype=np.int64)
        for m in cols:
            self._check_mass_index(int(m))
        out = np.zeros(self.get_num_spectra(), dtype=np.float32)
        for i in range(self.get_num_spectra()):
            delta = self._compute_delta(self._dx.get_spectrum(i), bg)
            out[i] = float(delta[cols].sum())
        return out

    def get_delta_ic(self, index: int) -> float:
        """Return :math:`\\sum` :meth:`get_delta_spectrum` ``(index)``."""
        return float(self.get_delta_spectrum(index).sum())

    # ------------------------------------------------------------------
    # XML / log accessors
    # ------------------------------------------------------------------

    def get_method_xml(self) -> str:
        return self._dx.method_xml

    def get_experiment_xml(self) -> str:
        # Advion stores the experiment XML in an aux file named
        # ``experiment``.  Older datasets may not have one.
        for af in self._aux_file_records():
            if af.name == "experiment":
                return af.text
        return ""

    def get_icpms_experiment_xml(self) -> str:
        for af in self._aux_file_records():
            if af.name == "icpmsExperiment":
                return af.text
        return ""

    def get_icpms_instrument_settings_xml(self) -> str:
        for af in self._aux_file_records():
            if af.name == "icpmsInstrumentSettings":
                return af.text
        return ""

    def get_experiment_log(self) -> str:
        return self._dx.experiment_log

    def get_ion_source_optimization_xml(self, index: int = 0) -> str:
        seg = self._get_segment(index)
        return seg.ion_source_xml if seg is not None else ""

    def get_tune_parameters_xml(self, index: int = 0) -> str:
        seg = self._get_segment(index)
        return seg.tune_params_xml if seg is not None else ""

    # ------------------------------------------------------------------
    # Scan-mode / segment metadata
    # ------------------------------------------------------------------

    def get_scan_mode_index(self) -> int:
        try:
            root = ET.fromstring(self._dx.meta_xml)
        except ET.ParseError:
            return 0
        for el in root.iter():
            if _strip_ns(el.tag) == "scanModeIndex":
                try:
                    return int((el.text or "0").strip())
                except ValueError:
                    return 0
        return 0

    def get_num_segments(self) -> int:
        return len(self._get_segments())

    def get_segment_time(self, index: int) -> float:
        segments = self._get_segments()
        if index < 0 or index >= len(segments):
            return 0.0
        return float(segments[index].start_time)

    # ------------------------------------------------------------------
    # Scalar channels
    # ------------------------------------------------------------------

    def get_num_scalar_channels(self) -> int:
        return len(self._get_scalar_channels())

    def get_scalar_channel_name(self, index: int) -> str:
        chans = self._get_scalar_channels()
        if 0 <= index < len(chans):
            return chans[index].name
        return ""

    def get_scalar_channel_num_samples(self, index: int) -> int:
        chans = self._get_scalar_channels()
        if 0 <= index < len(chans):
            return chans[index].times.shape[0]
        return 0

    def get_scalar_channel_times(self, index: int) -> np.ndarray:
        chans = self._get_scalar_channels()
        if not (0 <= index < len(chans)):
            raise IOError(AdvionDataErrorCode.CHANNEL_NOT_DEFINED)
        return chans[index].times.copy()

    def get_scalar_channel_values(self, index: int) -> np.ndarray:
        chans = self._get_scalar_channels()
        if not (0 <= index < len(chans)):
            raise IOError(AdvionDataErrorCode.CHANNEL_NOT_DEFINED)
        return chans[index].values.copy()

    def get_scalar_channel_num_attributes(self, index: int) -> int:
        chans = self._get_scalar_channels()
        if 0 <= index < len(chans):
            return len(chans[index].attributes)
        return -1

    def get_scalar_channel_attribute_name(self, index: int, attribute_index: int) -> str:
        chans = self._get_scalar_channels()
        if 0 <= index < len(chans):
            attrs = chans[index].attributes
            if 0 <= attribute_index < len(attrs):
                return attrs[attribute_index][0]
        return ""

    def get_scalar_channel_attribute_value(self, index: int, attribute_index: int) -> float:
        chans = self._get_scalar_channels()
        if 0 <= index < len(chans):
            attrs = chans[index].attributes
            if 0 <= attribute_index < len(attrs):
                return attrs[attribute_index][1]
        return 0.0

    # ------------------------------------------------------------------
    # Auxiliary files
    # ------------------------------------------------------------------

    def get_num_aux_files(self) -> int:
        return len(self._aux_file_records())

    def get_aux_file_name(self, index: int) -> str:
        files = self._aux_file_records()
        return files[index].name if 0 <= index < len(files) else ""

    def get_aux_file_type(self, index: int) -> str:
        files = self._aux_file_records()
        return files[index].type if 0 <= index < len(files) else ""

    def get_aux_file_text(self, index: int) -> str:
        files = self._aux_file_records()
        return files[index].text if 0 <= index < len(files) else ""

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------

    def save(self, path: str | Path) -> None:
        """Pickle ``{'masses', 'times', 'intensities'}`` to a gzipped file."""
        import gzip
        import pickle

        payload = {
            "masses": self.get_masses(),
            "times": self.get_retention_times(),
            "intensities": np.stack(
                [self.get_spectrum(i) for i in range(self.get_num_spectra())]
            ),
        }
        with Path(path).open("wb") as p, gzip.GzipFile(fileobj=p, mode="wb") as gz:
            pickle.dump(payload, gz)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _check_spectrum_index(self, index: int) -> None:
        if index < 0 or index >= self.get_num_spectra():
            raise IndexError(
                f"spectrum index {index} out of range "
                f"[0, {self.get_num_spectra()})"
            )

    def _check_mass_index(self, index: int) -> None:
        if index < 0 or index >= self.get_num_masses():
            raise IndexError(
                f"mass index {index} out of range [0, {self.get_num_masses()})"
            )

    # -- background / delta math ---------------------------------------

    def _ensure_background(self) -> np.ndarray:
        if not self._bg_dirty and self._bg_spectrum is not None:
            return self._bg_spectrum
        n_masses = self.get_num_masses()
        bg = np.zeros(n_masses, dtype=np.float64)
        n = 0
        times = self._dx.retention_times
        for i in range(self.get_num_spectra()):
            t = float(times[i])
            if self._bg_start_time <= t <= self._bg_end_time:
                bg += self._dx.get_spectrum(i)
                n += 1
        if n > 0:
            bg = bg / n + self._bg_noise_offset
        # When no scans fall inside the window we leave ``bg`` at zero;
        # ``_compute_delta`` short-circuits to a zero output in that
        # case to avoid divide-by-zero.
        self._bg_spectrum = bg.astype(np.float32)
        self._bg_dirty = False
        return self._bg_spectrum

    def _compute_delta(
        self, spectrum: np.ndarray, background: np.ndarray
    ) -> np.ndarray:
        """Compute the Peak Express delta signal for one spectrum.

        Algorithm (matching the Advion reference):

        1. ``delta = (spectrum - bg) / bg`` everywhere ``bg > 0``;
           values below ``threshold`` are zeroed.
        2. Drop runs of consecutive non-zero deltas whose m/z width
           (``masses[run_end] - masses[run_start]``) is less than
           ``min_width``.
        """
        delta = np.zeros_like(spectrum, dtype=np.float32)
        bg = background.astype(np.float32, copy=False)
        nonzero = bg > 0
        if nonzero.any():
            d = (spectrum[nonzero] - bg[nonzero]) / bg[nonzero]
            d = np.where(d < self._bg_threshold, 0.0, d)
            delta[nonzero] = d

        # Pass 2: drop runs of consecutive non-zero deltas narrower
        # than ``min_width`` m/z.  We find run boundaries with
        # ``np.diff`` and then zero the offending slices.
        masses = self._dx.masses
        is_peak = delta > 0
        edges = np.diff(np.concatenate(([False], is_peak, [False])).astype(np.int8))
        starts = np.where(edges == 1)[0]
        ends = np.where(edges == -1)[0]  # exclusive
        last_mass = float(masses[-1])
        for s, e in zip(starts, ends):
            end_mass = float(masses[e]) if e < masses.size else last_mass
            if end_mass - float(masses[s]) < self._bg_min_width:
                delta[s:e] = 0.0

        return delta

    # -- metadata parsing ----------------------------------------------

    def _get_segments(self) -> list["_Segment"]:
        if self._segments is None:
            self._segments = _parse_segments(self._dx)
        return self._segments

    def _get_segment(self, index: int) -> "_Segment | None":
        segments = self._get_segments()
        if 0 <= index < len(segments):
            return segments[index]
        return None

    def _get_scalar_channels(self) -> list["_ScalarChannel"]:
        if self._scalar_channels is None:
            self._scalar_channels = _parse_scalar_channels(self._dx)
        return self._scalar_channels

    def _aux_file_records(self) -> list["_AuxFile"]:
        if self._aux_files is None:
            self._aux_files = _parse_aux_files(self._dx)
        return self._aux_files


# ---------------------------------------------------------------------------
# Metadata records / parsers
# ---------------------------------------------------------------------------


class _Segment:
    """One ``<segment>`` element from the ``.meta`` file."""

    __slots__ = ("start_time", "ion_source_xml", "tune_params_xml")

    def __init__(self, start_time: float, ion_source_xml: str, tune_params_xml: str):
        self.start_time = start_time
        self.ion_source_xml = ion_source_xml
        self.tune_params_xml = tune_params_xml


class _ScalarChannel:
    __slots__ = ("name", "times", "values", "attributes")

    def __init__(
        self,
        name: str,
        times: np.ndarray,
        values: np.ndarray,
        attributes: list[tuple[str, float]],
    ):
        self.name = name
        self.times = times
        self.values = values
        self.attributes = attributes


class _AuxFile:
    __slots__ = ("name", "type", "text")

    def __init__(self, name: str, type_: str, text: str):
        self.name = name
        self.type = type_
        self.text = text


def _parse_segments(dx: DatxFile) -> list[_Segment]:
    meta_xml = dx.meta_xml
    if not meta_xml:
        return []
    try:
        root = ET.fromstring(meta_xml)
    except ET.ParseError:
        return []

    out: list[_Segment] = []
    for el in root.iter():
        if _strip_ns(el.tag) != "segment":
            continue
        start_time = 0.0
        ion_file = ""
        tune_file = ""
        for child in el:
            local = _strip_ns(child.tag)
            text = (child.text or "").strip()
            if local == "startTime":
                try:
                    start_time = float(text)
                except ValueError:
                    pass
            elif local == "ionSourceFile":
                ion_file = text
            elif local == "tuneParamsFile":
                tune_file = text

        ion_xml = _read_member_text(dx, ion_file) if ion_file else ""
        tune_xml = _read_member_text(dx, tune_file) if tune_file else ""
        out.append(_Segment(start_time, ion_xml, tune_xml))
    return out


def _parse_scalar_channels(dx: DatxFile) -> list[_ScalarChannel]:
    """Parse every ``*.scalar`` member of the archive."""
    channels: list[_ScalarChannel] = []
    seen: set[str] = set()
    for full_name in dx.list_files():
        if not full_name.endswith(".scalar") or full_name in seen:
            continue
        seen.add(full_name)
        raw = dx._raw(full_name)
        if raw is None:
            continue
        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            continue
        name = ""
        attributes: list[tuple[str, float]] = []
        times: list[float] = []
        values: list[float] = []
        # Walk direct children of <scalarChannel> only, so a stray
        # <name>...</name> inside <attribute> doesn't shadow the channel
        # name.
        for child in root:
            local = _strip_ns(child.tag)
            if local == "name":
                name = (child.text or "").strip()
            elif local == "attribute":
                # Layout: <attribute><name>X</name><value>1.5</value></attribute>
                # or <attribute name="X" value="1.5"/>.  Support both.
                a_name = child.attrib.get("name", "")
                a_value = child.attrib.get("value", "")
                for sub in child:
                    sub_local = _strip_ns(sub.tag)
                    if sub_local == "name":
                        a_name = (sub.text or "").strip()
                    elif sub_local == "value":
                        a_value = (sub.text or "").strip()
                try:
                    attributes.append((a_name, float(a_value)))
                except ValueError:
                    attributes.append((a_name, 0.0))
            elif local == "entry":
                t = child.attrib.get("time", "")
                v = child.attrib.get("value", "")
                for sub in child:
                    sub_local = _strip_ns(sub.tag)
                    if sub_local == "time":
                        t = (sub.text or "").strip()
                    elif sub_local == "value":
                        v = (sub.text or "").strip()
                try:
                    times.append(float(t))
                    values.append(float(v))
                except ValueError:
                    pass
        channels.append(
            _ScalarChannel(
                name=name,
                times=np.asarray(times, dtype=np.float32),
                values=np.asarray(values, dtype=np.float32),
                attributes=attributes,
            )
        )
    # Sort by name so ``foo.0.scalar`` precedes ``foo.1.scalar``.
    channels.sort(key=lambda c: c.name)
    return channels


def _parse_aux_files(dx: DatxFile) -> list[_AuxFile]:
    """Parse the optional ``auxfiles`` index plus per-file payloads.

    The Advion schema is::

        <auxFiles>
          <file><name>X</name><type>text</type><isHTML>false</isHTML></file>
          ...
        </auxFiles>

    with the body of each file stored as a separate text member named
    after ``<name>``.
    """
    raw = dx._raw("auxfiles") or dx._raw(".auxfiles")
    if raw is None:
        for fn in dx.list_files():
            if fn.endswith("/auxfiles") or fn.endswith(".auxfiles"):
                raw = dx._raw(fn)
                if raw is not None:
                    break
    if raw is None:
        return []
    try:
        root = ET.fromstring(raw)
    except ET.ParseError:
        return []
    out: list[_AuxFile] = []
    for file_el in root.iter():
        if _strip_ns(file_el.tag) != "file":
            continue
        name = ""
        type_ = "text"
        is_html = False
        for child in file_el:
            local = _strip_ns(child.tag)
            text = (child.text or "").strip()
            if local == "name":
                name = text
            elif local == "type":
                type_ = text
            elif local == "isHTML":
                is_html = text.lower() == "true"
        if is_html and type_ == "text":
            type_ = "text/html"
        body = _read_member_text(dx, name)
        out.append(_AuxFile(name=name, type_=type_, text=body))
    return out


def _read_member_text(dx: DatxFile, name: str) -> str:
    if not name:
        return ""
    blob = dx._raw(name)
    if blob is None:
        for fn in dx.list_files():
            if fn.rsplit("/", 1)[-1] == name:
                blob = dx._raw(fn)
                if blob is not None:
                    break
    if blob is None:
        return ""
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError:
        return blob.decode("utf-8", errors="replace")
