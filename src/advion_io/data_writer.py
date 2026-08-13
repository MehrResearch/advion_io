"""Pure-Python writer for Advion ``.datx`` mass-spectrometry data sets.

This module mirrors the Advion ``DataWriter`` API.  Every public
method on the reference class has a ``snake_case`` Python equivalent
here; output is bit-for-bit compatible on the read side, so a file
produced here loads with :class:`advion_io.DataReader` as well as with
the vendor's own reader.

The reference C++ implementation operates on a *folder* of loose data
files while data acquisition is happening and only zips them up to a
``.datx`` archive at the very end (via :meth:`create_datx_file`).  We
mirror that pattern so the workflow is identical:

.. code-block:: python

    with DataWriter("/tmp", "MyRun", is_centroid=False) as w:
        w.set_metadata("1.0", "fw1", "myInst", "CMS-L")
        w.write_method(method_xml)
        w.write_tune_params(tune_xml)
        w.write_ion_source_opt(ion_source_xml)
        w.write_spectrum_masses(masses)              # float32, length M
        for t, intensities in scans:
            w.write_scan_data(intensities, t, tic)   # uint32 or float
        w.create_datx_file()

The per-scan binary format is the inverse of :func:`decode_intensities_blob`
from :mod:`advion_io.data_reader`.
"""
from __future__ import annotations

import struct
import zipfile
from pathlib import Path
from typing import Iterator, Sequence
from xml.sax.saxutils import escape

import numpy as np

from .constants import AdvionDataErrorCode
from .data_reader import decode_intensities_blob

__all__ = ["DataWriter", "encode_intensities_blob", "MAX_EXTENSIONS_PER_GROUP"]


# ---------------------------------------------------------------------------
# Per-scan encoder
# ---------------------------------------------------------------------------
#
# The encoder is the inverse of :func:`advion_io.data_reader.decode_intensities_blob`.
# It walks the intensity array and groups runs of consecutive equal
# values into "run-length" groups, then emits up to 14 "delta extension"
# samples after each non-zero group so neighbouring nearly-equal samples
# don't waste a whole new base-value slot.

MAX_EXTENSIONS_PER_GROUP = 14


def _pack_bits(values: Iterator[int] | Sequence[int], width: int) -> bytes:
    """Pack integer ``values`` LSB-first using ``width`` bits each.

    Width 0 is treated as a no-op (returns ``b""``); ``width == 32``
    is handled by the caller, which falls back to writing little-endian
    ``uint32`` rather than packing.
    """
    if width == 0:
        return b""
    out = bytearray()
    bit_buf = 0
    bit_count = 0
    for v in values:
        v &= (1 << width) - 1
        bit_buf |= v << bit_count
        bit_count += width
        while bit_count >= 8:
            out.append(bit_buf & 0xFF)
            bit_buf >>= 8
            bit_count -= 8
    if bit_count:
        out.append(bit_buf & 0xFF)
    return bytes(out)


def _bit_width(max_value: int) -> int:
    """Number of bits required to encode ``max_value`` (>= 0).

    ``_bit_width(0) == 0`` means "no stream emitted".  Values that
    require more than 32 bits cannot be encoded in the bit-packed
    format; :class:`DataWriter` falls back to the float32 layout in
    that case (``<storeAsFloat>true</storeAsFloat>``).
    """
    if max_value <= 0:
        return 0
    return max_value.bit_length()


def encode_intensities_blob(intensities: np.ndarray | Sequence[int]) -> bytes:
    """Encode one scan into the per-scan binary format used by ``.spectra``.

    Parameters
    ----------
    intensities:
        ``samples_per_scan`` non-negative integer values (anything
        coerced via :func:`int` works).  Values outside ``uint32`` are
        not supported; for those use the ``storeAsFloat=true`` layout
        which :class:`DataWriter` handles automatically.

    Returns
    -------
    bytes
        The opaque per-scan blob.
        :func:`advion_io.data_reader.decode_intensities_blob(blob, len(intensities))`
        round-trips back to ``intensities`` bit-exactly.
    """
    arr = np.asarray(intensities, dtype=np.int64)
    if arr.ndim != 1:
        raise ValueError("intensities must be 1-D")
    if (arr < 0).any():
        raise ValueError("intensities must be non-negative")
    if (arr > 0xFFFFFFFF).any():
        raise ValueError("intensities must fit in uint32")
    n = int(arr.size)
    if n == 0:
        raise ValueError("intensities must not be empty")

    # --- Outer pass: build run-length groups + delta extensions -----
    #
    # The encoder maintains a *current* group whose base value is
    # ``prev`` and whose run length (number of consecutive samples
    # equal to ``prev``) is ``run_len``.  When ``arr[i] != prev`` we
    # close the current group and start a new one.
    #
    # Subtlety (matching the Advion reference):
    #
    # * When closing a group, the *base value* and *run length*
    #   recorded are those of the group just being closed.
    # * However, the extension search performed at the same moment
    #   looks for samples to attach to the *next* group (whose base
    #   will be ``cur``).  The resulting nibble is therefore written
    #   alongside the *next* non-zero base, not the one we just
    #   closed.
    # * Consequently the deltas are computed relative to ``cur`` (the
    #   next group's base), and the extension samples consumed are
    #   ``arr[i+1], arr[i+2], ...`` \u2014 they do *not* count toward the
    #   next group's run length.
    run_lengths: list[int] = []          # stream1, length b
    base_values: list[int] = []          # stream2, length a (only non-zero bases)
    nibbles: list[int] = []              # length a, parallel to base_values
    deltas: list[int] = []               # signed int8 stream
    bitmap_bits: list[int] = []          # 1 -> zero base, 0 -> entry in stream2

    prev = int(arr[0])
    run_len = 1
    i = 1
    pending_nibble = 0     # ext count to write for the NEXT non-zero base
    while i <= n:
        cur = int(arr[i]) if i < n else 0
        if cur == prev and i < n:
            run_len += 1
            i += 1
            continue

        # Close the current group.
        run_lengths.append(run_len)
        if prev == 0:
            bitmap_bits.append(1)
        else:
            bitmap_bits.append(0)
            base_values.append(prev)
            nibbles.append(pending_nibble)
        pending_nibble = 0

        # Extension search for the *next* group (whose base is
        # ``cur``).  Bail early when ``cur`` is zero, the array is
        # exhausted, or the candidate fails the delta predicate.
        ext_count = 0
        if cur != 0:
            ref = cur
            j = i + 1
            while ext_count < MAX_EXTENSIONS_PER_GROUP and j < n - 1:
                cand = int(arr[j])
                next_zero = j + 1 < n and int(arr[j + 1]) == 0
                if cand == 0 and next_zero:
                    break
                d = cand - ref
                if d == 0 or d < -127 or d > 127:
                    break
                deltas.append(d & 0xFF)
                ref = cand
                ext_count += 1
                j += 1
        pending_nibble = ext_count

        # Start the next group at ``cur``; the extension samples are
        # consumed (i.e. not part of any group's run length).
        prev = cur
        run_len = 1
        i += 1 + ext_count

    b = len(run_lengths)
    a = len(base_values)
    assert a == len(nibbles), (a, len(nibbles))
    # Each delta extension consumes one sample of the array; the
    # remaining samples are covered by run lengths.
    assert sum(run_lengths) + sum(nibbles) == n, (
        f"run lengths ({sum(run_lengths)}) + extensions ({sum(nibbles)}) "
        f"!= {n}"
    )

    # --- Bit widths ---------------------------------------------------
    max_run = max(run_lengths) if run_lengths else 0
    max_base = max(base_values) if base_values else 0
    m0 = _bit_width(max_run)
    m1 = _bit_width(max_base)
    if m0 > 32 or m1 > 32:
        raise ValueError("intensities too large for the bit-packed format")

    # --- Bitmap (c bytes) --------------------------------------------
    c = (n + 7) // 8
    bitmap = bytearray(c)
    for g, bit in enumerate(bitmap_bits):
        if bit:
            bitmap[g >> 3] |= 1 << (g & 7)

    # --- Bit-packed streams ------------------------------------------
    if m0 == 32:
        s1_bytes = np.asarray(run_lengths, dtype="<u4").tobytes()
    else:
        s1_bytes = _pack_bits(run_lengths, m0)
        target_len = (b * m0 + 7) // 8
        if len(s1_bytes) < target_len:
            s1_bytes = s1_bytes + bytes(target_len - len(s1_bytes))

    if m1 == 32:
        s2_bytes = np.asarray(base_values, dtype="<u4").tobytes()
    else:
        s2_bytes = _pack_bits(base_values, m1)
        target_len = (a * m1 + 7) // 8
        if len(s2_bytes) < target_len:
            s2_bytes = s2_bytes + bytes(target_len - len(s2_bytes))

    # --- Nibbles (a 4-bit values, low-nibble first) -------------------
    nib_bytes = bytearray((a + 1) // 2)
    for k, v in enumerate(nibbles):
        if k & 1:
            nib_bytes[k >> 1] |= (v & 0x0F) << 4
        else:
            nib_bytes[k >> 1] |= v & 0x0F

    # --- Header + concatenation --------------------------------------
    header = bytes([m0 & 0xFF, m1 & 0xFF]) + struct.pack("<III", a, b, c)
    base_count_bytes = struct.pack("<i", len(deltas))
    delta_bytes = bytes(deltas)

    return (
        header
        + bytes(bitmap)
        + s1_bytes
        + s2_bytes
        + base_count_bytes
        + bytes(nib_bytes)
        + delta_bytes
    )


# ---------------------------------------------------------------------------
# High-level DataWriter
# ---------------------------------------------------------------------------


def _datetime_string() -> str:
    """Return an Advion-style date string for the ``.scans`` header."""
    import datetime as _dt
    return _dt.datetime.now().strftime("%Y.%m.%d %H:%M:%S")


def _xml_escape(text: str) -> str:
    """Escape ``&``, ``<``, ``>`` and ``"`` for use inside an XML body."""
    return escape(text, {'"': "&quot;"})


class _ScalarChannel:
    """In-flight scalar channel state.

    One per channel; written out as ``<root>.<id>.scalar`` when the
    dataset is finalised.
    """

    __slots__ = ("name", "attributes", "times", "values", "header_closed")

    def __init__(self, name: str):
        self.name = name
        self.attributes: list[tuple[str, float]] = []
        self.times: list[float] = []
        self.values: list[float] = []
        # Once the first entry has been written, attribute additions
        # are no longer allowed (matches the Advion contract).
        self.header_closed = False


class _AuxFile:
    __slots__ = ("name", "type", "is_html", "body")

    def __init__(self, name: str, type_: str):
        self.name = name
        self.type = type_
        self.is_html = type_ == "text/html"
        self.body = ""


class DataWriter:
    """Write a new Advion mass-spectrometry data set.

    Files are accumulated under ``<folder>/<root_name>/`` during the
    lifetime of the object and zipped into ``<folder>/<root_name>.datx``
    by :meth:`create_datx_file`.

    Parameters
    ----------
    folder:
        Parent directory for the new data set.  Created if absent.
    root_name:
        Logical name of the data set; used as the inner folder name and
        as the prefix on every file inside it.
    is_centroid:
        Stored in the ``.scans`` header as ``<dataType>``: ``centroid``
        when ``True``, ``continuum`` when ``False``.
    debug_output:
        Accepted for API compatibility; ignored.
    """

    # -- Construction / lifecycle --------------------------------------

    def __init__(
        self,
        folder: str | bytes | Path,
        root_name: str | bytes,
        is_centroid: bool,
        debug_output: bool = False,
    ) -> None:
        if isinstance(folder, bytes):
            folder = folder.decode("utf-8")
        if isinstance(root_name, bytes):
            root_name = root_name.decode("utf-8")
        self.folder = Path(folder)
        self.root_name = str(root_name)
        self.is_centroid = bool(is_centroid)
        self.debug_output = bool(debug_output)

        self._inner = self.folder / self.root_name
        self._inner.mkdir(parents=True, exist_ok=True)

        # Metadata that lands in the ``.scans`` XML header.
        self._software_version = ""
        self._firmware_version = ""
        self._instrument_id = ""
        self._hardware_type = "CMS"
        self._date = _datetime_string()

        # Method / tune / ion source / experiment / log.
        self._method_xml: str | None = None
        self._tune_xml: str | None = None  # for the single-segment case
        self._ion_source_xml: str | None = None
        self._experiment_xml: str | None = None
        self._scan_mode_index: int = 0

        # Segments override the single-tune / single-ion mode.  Each
        # entry: (start_time_minutes, ion_source_xml, tune_xml).
        self._segments: list[tuple[float, str, str]] = []

        # Mass axis + scan store.
        self._masses: np.ndarray | None = None
        # tuples of (retention_time, tic, byte_offset, byte_size)
        self._scan_records: list[tuple[float, float, int, int]] = []
        self._spectra_bytes = bytearray()
        self._store_as_float = False
        self._next_scan_index = 0

        # Scalar channels + aux files.
        self._scalar_channels: list[_ScalarChannel] = []
        self._aux_files: list[_AuxFile] = []

        # Experiment log accumulates timestamped log messages.
        self._log_lines: list[str] = []

        self._closed = False

    def __enter__(self) -> "DataWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def close(self) -> None:
        self._closed = True

    # -- Static helpers -----------------------------------------------

    @staticmethod
    def can_write_data(folder: str | Path, root_name: str | None = None) -> int:
        """Mirror ``DataWriter::canWriteData``.

        Returns ``ADVIONDATA_OK`` (0) on success, otherwise the
        appropriate error code.
        """
        folder = Path(folder)
        if root_name is not None:
            full = folder / str(root_name)
            try:
                str(full).encode("utf-8")
            except UnicodeEncodeError:
                return AdvionDataErrorCode.PATH_TOO_LONG
            if len(str(full)) > 240:
                return AdvionDataErrorCode.PATH_TOO_LONG
        if not folder.exists():
            try:
                folder.mkdir(parents=True)
            except OSError:
                return AdvionDataErrorCode.FILE_OPEN_FAILED
        return AdvionDataErrorCode.OK

    # -- Metadata setters ---------------------------------------------

    def set_metadata(
        self,
        software: str | bytes,
        firmware: str | bytes,
        instrument: str | bytes,
        hardware: str | bytes = "CMS",
    ) -> None:
        self._software_version = self._as_text(software)
        self._firmware_version = self._as_text(firmware)
        self._instrument_id = self._as_text(instrument)
        self._hardware_type = self._as_text(hardware)

    def write_method(self, method_xml: str | bytes) -> None:
        self._method_xml = self._as_text(method_xml)

    def write_experiment(self, experiment_xml: str | bytes) -> None:
        """Stores the experiment XML; surfaced as an auxiliary file."""
        self._experiment_xml = self._as_text(experiment_xml)

    def write_ion_source_opt(self, ion_source_xml: str | bytes) -> None:
        self._ion_source_xml = self._as_text(ion_source_xml)

    def write_tune_params(self, tune_xml: str | bytes) -> None:
        self._tune_xml = self._as_text(tune_xml)

    def write_scan_mode_index(self, scan_mode_index: int) -> None:
        self._scan_mode_index = int(scan_mode_index)

    def write_segments(
        self,
        num_segments: int,
        times: Sequence[float],
        ion_source_xmls: Sequence[str],
        tune_xmls: Sequence[str],
    ) -> None:
        if not (len(times) == len(ion_source_xmls) == len(tune_xmls) == num_segments):
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        self._segments = [
            (float(times[i]), self._as_text(ion_source_xmls[i]), self._as_text(tune_xmls[i]))
            for i in range(num_segments)
        ]

    def write_log_message(self, text: str | bytes) -> None:
        line = self._as_text(text)
        self._log_lines.append(line)

    # -- Masses / scan data -------------------------------------------

    def write_spectrum_masses(
        self, masses: np.ndarray | Sequence[float], num: int | None = None
    ) -> None:
        arr = np.asarray(masses, dtype=np.float32).ravel()
        if num is not None and arr.size != num:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        if arr.size == 0:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        self._masses = arr.copy()

    def write_scan_data(
        self,
        intensities: np.ndarray | Sequence[int] | Sequence[float],
        retention_time: float,
        tic: float,
        num: int | None = None,
    ) -> None:
        """Append one scan.

        Mirrors both ``writeScanData(const unsigned int*, ...)`` and
        ``writeScanData(const float*, ...)``.  Integer inputs use the
        compact bit-packed format; float inputs that don't quantise
        cleanly to non-negative ``uint32`` values trigger the
        ``storeAsFloat=true`` fallback (raw float32 dump per scan).
        """
        if self._masses is None:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        arr = np.asarray(intensities)
        if num is not None and arr.size != num:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        if arr.size != self._masses.size:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)

        rounded = arr
        if arr.dtype.kind == "f":
            # Try to compact to ints.  If any sample is negative or
            # non-integer, fall back to float32.
            ints = np.rint(arr).astype(np.int64, copy=False)
            if (
                (ints >= 0).all()
                and (ints <= 0xFFFFFFFF).all()
                and np.array_equal(ints.astype(np.float32), arr.astype(np.float32))
            ):
                rounded = ints
            else:
                self._store_as_float = True

        if self._store_as_float:
            chunk = np.asarray(arr, dtype=np.float32).tobytes()
        else:
            ints = np.asarray(rounded, dtype=np.int64)
            if (ints < 0).any() or (ints > 0xFFFFFFFF).any():
                # Promote to float storage for the whole dataset.
                self._store_as_float = True
                self._promote_existing_to_float()
                chunk = np.asarray(arr, dtype=np.float32).tobytes()
            else:
                chunk = encode_intensities_blob(ints)

        offset = len(self._spectra_bytes)
        self._spectra_bytes.extend(chunk)
        self._scan_records.append(
            (float(retention_time), float(tic), offset, len(chunk))
        )
        self._next_scan_index += 1

    def _promote_existing_to_float(self) -> None:
        """Re-encode previously bit-packed scans as raw float32.

        Called when :meth:`write_scan_data` realises the dataset can't
        stay compacted (typically because a scan contained
        non-integer or out-of-range values).  Since we never kept the
        original floats, we decode each compacted scan back through
        the decoder and store the float32 version.  This matches the
        Advion reference behaviour when a scan can't be compacted.
        """
        if not self._scan_records:
            self._spectra_bytes = bytearray()
            return
        new_bytes = bytearray()
        new_records = []
        for rt, tic, off, size in self._scan_records:
            blob = bytes(self._spectra_bytes[off : off + size])
            spectrum = decode_intensities_blob(blob, self._masses.size)
            new_chunk = np.asarray(spectrum, dtype=np.float32).tobytes()
            new_records.append((rt, tic, len(new_bytes), len(new_chunk)))
            new_bytes.extend(new_chunk)
        self._spectra_bytes = new_bytes
        self._scan_records = new_records

    # -- Scalar channels ---------------------------------------------

    def create_scalar_channel(self, name: str | bytes) -> int:
        channel = _ScalarChannel(self._as_text(name))
        self._scalar_channels.append(channel)
        return len(self._scalar_channels) - 1

    def add_scalar_channel_attribute(
        self, channel_id: int, name: str | bytes, value: float
    ) -> None:
        if not (0 <= channel_id < len(self._scalar_channels)):
            raise IOError(AdvionDataErrorCode.CHANNEL_NOT_DEFINED)
        chan = self._scalar_channels[channel_id]
        if chan.header_closed:
            raise IOError(AdvionDataErrorCode.CHANNEL_HEADER_CLOSED)
        chan.attributes.append((self._as_text(name), float(value)))

    def write_scalar_entry(self, channel_id: int, time: float, value: float) -> None:
        if not (0 <= channel_id < len(self._scalar_channels)):
            raise IOError(AdvionDataErrorCode.CHANNEL_NOT_DEFINED)
        chan = self._scalar_channels[channel_id]
        chan.header_closed = True
        chan.times.append(float(time))
        chan.values.append(float(value))

    def write_scalar_entries(
        self,
        channel_id: int,
        times: Sequence[float],
        values: Sequence[float],
        num_entries: int | None = None,
    ) -> None:
        if not (0 <= channel_id < len(self._scalar_channels)):
            raise IOError(AdvionDataErrorCode.CHANNEL_NOT_DEFINED)
        if num_entries is None:
            num_entries = len(times)
        if len(times) != num_entries or len(values) != num_entries:
            raise IOError(AdvionDataErrorCode.PARAMETER_OUT_OF_RANGE)
        chan = self._scalar_channels[channel_id]
        chan.header_closed = True
        for t, v in zip(times, values):
            chan.times.append(float(t))
            chan.values.append(float(v))

    # -- Auxiliary text files ----------------------------------------

    def create_auxiliary_file(self, name: str | bytes, type_: str | bytes) -> int:
        af = _AuxFile(self._as_text(name), self._as_text(type_))
        self._aux_files.append(af)
        return len(self._aux_files) - 1

    def write_text_to_file(self, aux_id: int, text: str | bytes) -> None:
        if not (0 <= aux_id < len(self._aux_files)):
            raise IOError(AdvionDataErrorCode.AUX_FILE_NOT_DEFINED)
        self._aux_files[aux_id].body += self._as_text(text)

    # -- Finalisation -------------------------------------------------

    def create_datx_file(self) -> Path:
        """Materialise loose files and zip them into ``<root>.datx``.

        Returns
        -------
        pathlib.Path
            The path of the created archive.
        """
        if self._masses is None:
            raise IOError(AdvionDataErrorCode.NO_SPECTRA)
        if not self._scan_records:
            raise IOError(AdvionDataErrorCode.NO_SPECTRA)

        # 1. Write masses (raw little-endian float32).
        masses_path = self._inner / f"{self.root_name}.masses"
        masses_path.write_bytes(self._masses.astype("<f4").tobytes())

        # 2. Concatenated per-scan spectra.
        spectra_path = self._inner / f"{self.root_name}.spectra"
        spectra_path.write_bytes(bytes(self._spectra_bytes))

        # 3. .scans XML index.
        scans_path = self._inner / f"{self.root_name}.scans"
        scans_path.write_text(self._render_scans_xml(), encoding="utf-8")

        # 4. .meta XML (hardware type, scan mode index, segments).
        meta_path = self._inner / f"{self.root_name}.meta"
        meta_path.write_text(self._render_meta_xml(), encoding="utf-8")

        # 5. .method, .tune, .ion files (when present).
        if self._method_xml is not None:
            (self._inner / f"{self.root_name}.method").write_text(
                self._method_xml, encoding="utf-8"
            )
        # The single-segment tune/ion get written under the root name;
        # multi-segment ones get numeric suffixes alongside.
        single_tune = self._tune_xml
        single_ion = self._ion_source_xml
        if self._segments:
            for k, (_t, ion_xml, tune_xml) in enumerate(self._segments):
                if k == 0:
                    ion_name = f"{self.root_name}.ion"
                    tune_name = f"{self.root_name}.tune"
                else:
                    ion_name = f"{self.root_name}.{k}.ion"
                    tune_name = f"{self.root_name}.{k}.tune"
                if ion_xml:
                    (self._inner / ion_name).write_text(ion_xml, encoding="utf-8")
                if tune_xml:
                    (self._inner / tune_name).write_text(tune_xml, encoding="utf-8")
        else:
            if single_ion is not None:
                (self._inner / f"{self.root_name}.ion").write_text(
                    single_ion, encoding="utf-8"
                )
            if single_tune is not None:
                (self._inner / f"{self.root_name}.tune").write_text(
                    single_tune, encoding="utf-8"
                )

        # 6. Experiment log.
        if self._log_lines:
            (self._inner / f"{self.root_name}.log").write_text(
                "\n".join(self._log_lines) + "\n", encoding="utf-8"
            )

        # 7. Scalar channels.
        for i, chan in enumerate(self._scalar_channels):
            (self._inner / f"{self.root_name}.{i}.scalar").write_text(
                self._render_scalar_xml(chan), encoding="utf-8"
            )

        # 8. Auxiliary files.
        if self._aux_files or self._experiment_xml is not None:
            aux_xml = self._render_aux_index_xml()
            (self._inner / "auxfiles").write_text(aux_xml, encoding="utf-8")
            for af in self._aux_files:
                (self._inner / af.name).write_text(af.body, encoding="utf-8")
            if self._experiment_xml is not None and not any(
                af.name == "experiment" for af in self._aux_files
            ):
                (self._inner / "experiment").write_text(
                    self._experiment_xml, encoding="utf-8"
                )

        # 9. Zip the folder into the .datx archive.
        out_path = self.folder / f"{self.root_name}.datx"
        with zipfile.ZipFile(out_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for p in sorted(self._inner.iterdir()):
                if not p.is_file():
                    continue
                zf.write(p, arcname=f"{self.root_name}/{p.name}")
        return out_path

    # -- Rendering helpers --------------------------------------------

    def _render_scans_xml(self) -> str:
        # Match the on-disk format produced by the Advion reference:
        # CRLF line endings, tab indents, header followed by ``<scan>``
        # lines.
        lines = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<scans version="1.1">',
            f"\t<dataType>{'centroid' if self.is_centroid else 'continuum'}</dataType>",
            f"\t<samplesPerScan>{self._masses.size}</samplesPerScan>",
            f"\t<date>{_xml_escape(self._date)}</date>",
            f"\t<softwareVersion>{_xml_escape(self._software_version)}</softwareVersion>",
            f"\t<firmwareVersion>{_xml_escape(self._firmware_version)}</firmwareVersion>",
            f"\t<hardwareID>{_xml_escape(self._instrument_id)}</hardwareID>",
            f"\t<storeAsFloat>{'true' if self._store_as_float else 'false'}</storeAsFloat>",
        ]
        for rt, tic, off, size in self._scan_records:
            lines.append(
                f"<scan><time>{rt}</time><index>{off}</index>"
                f"<size>{size}</size><tic>{tic}</tic></scan>"
            )
        return "\r\n".join(lines) + "\r\n"

    def _render_meta_xml(self) -> str:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<acquisitionMetadata version="1.1">']
        if self._segments:
            for k, (t, _ion, _tune) in enumerate(self._segments):
                if k == 0:
                    ion_name = f"{self.root_name}.ion"
                    tune_name = f"{self.root_name}.tune"
                else:
                    ion_name = f"{self.root_name}.{k}.ion"
                    tune_name = f"{self.root_name}.{k}.tune"
                lines.append("\t<segment>")
                lines.append(f"\t\t<startTime>{t}</startTime>")
                lines.append(f"\t\t<ionSourceFile>{_xml_escape(ion_name)}</ionSourceFile>")
                lines.append(f"\t\t<tuneParamsFile>{_xml_escape(tune_name)}</tuneParamsFile>")
                lines.append("\t</segment>")
        else:
            lines.append("\t<segment>")
            lines.append("\t\t<startTime>0.0</startTime>")
            if self._ion_source_xml is not None:
                lines.append(
                    f"\t\t<ionSourceFile>{_xml_escape(self.root_name)}.ion</ionSourceFile>"
                )
            if self._tune_xml is not None:
                lines.append(
                    f"\t\t<tuneParamsFile>{_xml_escape(self.root_name)}.tune</tuneParamsFile>"
                )
            lines.append("\t</segment>")
        lines.append(f"\t<hardwareType>{_xml_escape(self._hardware_type)}</hardwareType>")
        lines.append(f"\t<scanModeIndex>{int(self._scan_mode_index)}</scanModeIndex>")
        lines.append("</acquisitionMetadata>")
        return "\r\n".join(lines) + "\r\n"

    @staticmethod
    def _render_scalar_xml(chan: _ScalarChannel) -> str:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<scalarChannel version="1.0">',
                 f"\t<name>{_xml_escape(chan.name)}</name>"]
        for name, value in chan.attributes:
            lines.append(
                f"\t<attribute><name>{_xml_escape(name)}</name>"
                f"<value>{value}</value></attribute>"
            )
        for t, v in zip(chan.times, chan.values):
            lines.append(f"\t<entry><time>{t}</time><value>{v}</value></entry>")
        lines.append("</scalarChannel>")
        return "\r\n".join(lines) + "\r\n"

    def _render_aux_index_xml(self) -> str:
        lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<auxFiles>"]
        for af in self._aux_files:
            lines.append("\t<file>")
            lines.append(f"\t\t<name>{_xml_escape(af.name)}</name>")
            type_ = "text" if af.is_html else (af.type or "text")
            lines.append(f"\t\t<type>{_xml_escape(type_)}</type>")
            lines.append(
                f"\t\t<isHTML>{'true' if af.is_html else 'false'}</isHTML>"
            )
            lines.append("\t</file>")
        if self._experiment_xml is not None and not any(
            af.name == "experiment" for af in self._aux_files
        ):
            lines.append("\t<file>")
            lines.append("\t\t<name>experiment</name>")
            lines.append("\t\t<type>text</type>")
            lines.append("\t\t<isHTML>false</isHTML>")
            lines.append("\t</file>")
        lines.append("</auxFiles>")
        return "\r\n".join(lines) + "\r\n"

    # -- Misc helpers --------------------------------------------------

    @staticmethod
    def _as_text(value: str | bytes | None) -> str:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8")
        return str(value)
