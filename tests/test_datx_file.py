"""Tests for the low-level :class:`advion_io.DatxFile` archive accessor.

These tests use the example acquisition that ships with the repository
(``tests/data/example.datx``).  They run on any platform.
"""
from __future__ import annotations

import numpy as np
import pytest

from advion_io import DatxFile, decode_intensities_blob
from example_data import EXAMPLE_DATX, SKIP_REASON


@pytest.fixture(scope="module")
def dx():
    if not EXAMPLE_DATX.exists():
        pytest.skip(SKIP_REASON)
    with DatxFile(EXAMPLE_DATX) as f:
        yield f


def test_archive_metadata(dx):
    assert dx.num_spectra == 137
    assert dx.num_masses == 11999
    assert dx.samples_per_scan == 11999
    assert dx.data_type == "continuum"
    assert dx.store_as_float is False
    assert dx.date.startswith("2026")


def test_masses_axis(dx):
    masses = dx.masses
    assert masses.dtype == np.float32
    assert masses.shape == (11999,)
    # Step is uniform and ~0.05 m/z within float32 rounding noise.
    diffs = np.diff(masses)
    assert np.allclose(diffs, 0.05, atol=1e-4)
    assert 0.049 < diffs[0] < 0.051
    # Range covers the canonical Expression CMS-L mass window 100–700.
    assert masses[0] == pytest.approx(99.9, abs=1e-3)
    assert masses[-1] == pytest.approx(699.8, abs=1e-3)


def test_retention_times(dx):
    rts = dx.retention_times
    assert rts.dtype == np.float32
    assert rts.shape == (137,)
    # Times are strictly increasing.
    assert np.all(np.diff(rts) > 0)


def test_spectrum_shape_and_dtype(dx):
    spec = dx.get_spectrum(0)
    assert spec.dtype == np.float32
    assert spec.shape == (dx.num_masses,)
    assert np.all(spec >= 0)


def test_spectrum_tic_matches_index(dx):
    """Σ decoded intensities ≈ TIC recorded by the instrument."""
    rel_errs = []
    for i, scan in enumerate(dx.scans):
        spec = dx.get_spectrum(i)
        rel_errs.append(abs(spec.sum() - scan.tic) / scan.tic)
    rel_errs = np.array(rel_errs)
    # The advertised TIC is stored as a double rounded to four decimals
    # in the .scans XML; the recovered TIC is the sum of single-precision
    # samples, so a few ULPs of float32 (~1e-6) are expected.
    assert rel_errs.max() < 1e-5, f"max rel err {rel_errs.max()}"
    assert np.median(rel_errs) < 1e-6


def test_full_intensity_matrix(dx):
    I = dx.intensities
    assert I.shape == (dx.num_spectra, dx.num_masses)
    assert I.dtype == np.float32
    # cached: same object on second access
    assert dx.intensities is I


def test_spectrum_index_bounds(dx):
    with pytest.raises(IndexError):
        dx.get_spectrum(-1)
    with pytest.raises(IndexError):
        dx.get_spectrum(dx.num_spectra)


def test_averaged_spectrum_matches_manual(dx):
    avg = dx.get_averaged_spectrum([0, 1, 2])
    manual = (
        dx.get_spectrum(0).astype(np.float64)
        + dx.get_spectrum(1).astype(np.float64)
        + dx.get_spectrum(2).astype(np.float64)
    ) / 3.0
    assert np.allclose(avg, manual, rtol=1e-6, atol=1e-3)


def test_xic_matches_manual(dx):
    indices = [100, 200, 300]
    xic = dx.generate_xic(indices)
    assert xic.shape == (dx.num_spectra,)
    # Compare with hand-computed sums for first 3 scans.
    expected = np.array(
        [dx.get_spectrum(i)[indices].sum() for i in range(3)],
        dtype=np.float32,
    )
    np.testing.assert_allclose(xic[:3], expected, rtol=1e-6)


def test_decode_blob_directly(dx):
    """decode_intensities_blob and get_spectrum agree."""
    blob = dx._files[".spectra"]
    scan = dx.scans[5]
    direct = decode_intensities_blob(
        blob[scan.offset : scan.offset + scan.size], dx.samples_per_scan
    )
    np.testing.assert_array_equal(direct, dx.get_spectrum(5))


def test_aux_text_files_accessible(dx):
    # These should all parse to non-empty strings for our example.
    assert "<acquisitionMetadata" in dx.meta_xml
    assert "Acquisition begins" in dx.experiment_log
    assert "ionSourceOptimization" in dx.ion_source_xml
