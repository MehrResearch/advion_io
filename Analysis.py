# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "advion-io @ git+https://github.com/MehrResearch/advion_io",
#     "anywidget==0.11.0",
#     "marimo>=0.23.14",
#     "matplotlib>=3.9",
#     "numpy>=2.1",
#     "scipy>=1.14",
#     "seaborn==0.13.2",
#     "traitlets>=5.14",
# ]
# ///

import marimo

__generated_with = "0.24.0"
app = marimo.App(width="medium")


@app.cell(hide_code=True)
def _():
    import base64
    import functools
    import io
    import math
    import xml.etree.ElementTree as ET
    from pathlib import Path

    import anywidget
    import matplotlib.pyplot as plt
    import numpy as np
    import seaborn as sns
    import traitlets
    from scipy.signal import find_peaks

    from advion_io import DataReader

    import marimo as mo

    return (
        DataReader,
        ET,
        Path,
        anywidget,
        base64,
        find_peaks,
        functools,
        io,
        math,
        mo,
        np,
        plt,
        sns,
        traitlets,
    )


@app.cell(hide_code=True)
def _(mo, plt, sns):
    plt.rcParams["figure.dpi"] = 200
    mo._runtime.context.get_context().marimo_config["runtime"]["output_max_bytes"] = 250_000_000
    sns.set_theme(context="talk", style="ticks", font="Arial",
                  rc={"svg.fonttype": "none", "savefig.format": "svg"})
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md("""
    # MS analysis dashboard
    """)
    return


@app.cell(hide_code=True)
def _(Path):
    OUTPUT_HOME = Path("./out").resolve()
    return (OUTPUT_HOME,)


@app.cell(hide_code=True)
def _(mo):
    datx_browser = mo.ui.file_browser(
        initial_path=".",
        filetypes=[".datx"],
        selection_mode="file",
        multiple=False,
        restrict_navigation=False,
        label="Open a `.datx` acquisition",
    )
    return (datx_browser,)


@app.cell(hide_code=True)
def load_experiment(DataReader, ET, Path, functools, np):
    def _leaves(xml: str) -> dict[str, str]:
        """Flatten an XML document to `{tag path: text}` for its leaf nodes.

        Advion's method / tune / ion-source documents are shallow bags of
        settings, so a flat mapping is all the display code needs; namespaces
        and the `xsi:type` attribute (which is how the scan mode and source
        type are recorded) are folded in as well.
        """
        try:
            root = ET.fromstring(xml)
        except ET.ParseError:
            return {}

        def tag(element) -> str:
            return element.tag.rsplit("}", 1)[-1]

        leaves: dict[str, str] = {}

        def walk(element, prefix: str) -> None:
            for child in element:
                name = f"{prefix}{tag(child)}"
                kind = next(
                    (
                        value
                        for key, value in child.attrib.items()
                        if key.rsplit("}", 1)[-1] == "type"
                    ),
                    None,
                )
                if kind:
                    leaves[f"{name}/@type"] = kind
                if len(child):
                    walk(child, f"{name}/")
                elif (child.text or "").strip():
                    leaves[name] = child.text.strip()

        walk(root, "")
        return leaves

    @functools.lru_cache(maxsize=8)
    def _read_datx(path: Path, _mtime: int) -> dict:
        with DataReader(path) as reader:
            return {
                "path": path,
                "masses": np.asarray(reader.get_masses(), dtype=float),
                "times": np.asarray(reader.get_retention_times(), dtype=float),
                # Stacking per-scan decodes keeps this working against any
                # released advion_io; the reader caches each scan either way.
                "intensities": np.stack(
                    [
                        np.asarray(reader.get_spectrum(index), dtype=float)
                        for index in range(reader.get_num_spectra())
                    ]
                ),
                "date": reader.get_date(),
                "hardware_type": reader.get_hardware_type(),
                "instrument_id": reader.get_instrument_id(),
                "software_version": reader.get_software_version(),
                "firmware_version": reader.get_firmware_version(),
                "is_centroid": reader.get_is_centroid(),
                "segment_times": [
                    reader.get_segment_time(index)
                    for index in range(reader.get_num_segments())
                ],
                "scalar_channels": [
                    reader.get_scalar_channel_name(index)
                    for index in range(reader.get_num_scalar_channels())
                ],
                "aux_files": [
                    (reader.get_aux_file_name(index), reader.get_aux_file_type(index))
                    for index in range(reader.get_num_aux_files())
                ],
                "method": _leaves(reader.get_method_xml()),
                "tune": _leaves(reader.get_tune_parameters_xml()),
                "ion_source": _leaves(reader.get_ion_source_optimization_xml()),
                "log": reader.get_experiment_log(),
            }

    def load_experiment(path: Path) -> dict:
        """Read one Advion acquisition: arrays plus its acquisition metadata.

        Decoding a run costs a noticeable fraction of a second and several cells
        want the same arrays, so results are cached; the modification time is
        part of the key, meaning a re-acquired file is picked up automatically.
        """
        path = Path(path)
        return _read_datx(path, path.stat().st_mtime_ns)

    return (load_experiment,)


@app.cell(hide_code=True)
def smooth_trace(np):
    def smooth_trace(values, window: int):
        """Centered N-point moving average with edge padding."""
        trace = np.asarray(values, dtype=float)
        window = min(int(window), trace.size)
        if window % 2 == 0:
            window -= 1
        if window <= 1 or trace.size < 2:
            return trace
        pad = window // 2
        padded = np.pad(trace, pad, mode="edge")
        return np.convolve(padded, np.ones(window) / window, mode="valid")


    return (smooth_trace,)


@app.cell(hide_code=True)
def peak_base_bounds(np, smooth_trace):
    def peak_base_bounds(
        trace,
        peaks,
        detect_window: int = 15,
        rise_tolerance: float = 0.10,
        return_fraction: float = 0.05,
        max_base_level: float = 0.5,
        width_limit: float = 4.0,
    ):
        """Locate integration bases either side of every peak.

        Returns ``(start, stop, left_level, right_level)`` per peak, where the
        levels are the denoised signal at each base — anchoring the baseline to
        single raw samples lets noise spikes tilt the tie line above the trace
        and yield negative areas.

        Flanks are followed on a smoothed copy, since scan-to-scan noise in a
        raw XIC stops a naive walk after one or two points. Each apex is first
        snapped to the corresponding maximum of that copy. A flank ends when the
        trace turns back up by more than ``rise_tolerance`` of the peak height
        *and* the valley has fallen below ``max_base_level`` (so shoulders of a
        doublet are not mistaken for bases), or once it returns to within
        ``return_fraction`` of the baseline. Arms are capped at ``width_limit``
        times the median half-width of all peaks, which keeps peaks riding on a
        broad hump from running away.
        """
        trace = np.asarray(trace, dtype=float)
        peaks = np.atleast_1d(peaks).astype(int)
        detect = smooth_trace(trace, detect_window)
        floor = float(np.percentile(detect, 5))

        apexes = []
        half_widths = []
        for peak in peaks:
            apex = peak
            for step in (-1, 1):
                index = peak
                while 0 <= index + step < detect.size and detect[index + step] > detect[index]:
                    index += step
                if detect[index] > detect[apex]:
                    apex = index
            apexes.append(apex)
            half_level = floor + 0.5 * (detect[apex] - floor)
            arms = []
            for step in (-1, 1):
                index = apex
                while 0 <= index + step < detect.size and detect[index + step] > half_level:
                    index += step
                arms.append(abs(index - apex) + 1)
            half_widths.append(max(arms))
        reach = max(3, int(width_limit * float(np.median(half_widths)))) if half_widths else 3

        bounds = []
        for peak, apex in zip(peaks, apexes):
            height = detect[apex] - floor
            stop_level = floor + return_fraction * height
            base_level = floor + max_base_level * height
            slack = rise_tolerance * height
            edges = []
            for step in (-1, 1):
                valley = index = apex
                while 0 <= index + step < detect.size and abs(index + step - apex) <= reach:
                    index += step
                    if detect[index] <= detect[valley]:
                        valley = index
                    if detect[index] <= stop_level:
                        valley = index
                        break
                    if detect[index] > detect[valley] + slack and detect[valley] <= base_level:
                        break
                edges.append(valley)
            start = min(edges[0], peak)
            stop = max(edges[1], peak) + 1
            bounds.append((start, stop, float(detect[start]), float(detect[stop - 1])))
        return bounds


    return (peak_base_bounds,)


@app.cell(hide_code=True)
def annotate_chromatogram_peaks(find_peaks, math, np, peak_base_bounds):
    def annotate_chromatogram_peaks(
        ax,
        times,
        values,
        *,
        plot_times=None,
        scale: float = 1.0,
        offset: float = 0.0,
        color=None,
        label_fontsize: float = 8.75,
        peak_threshold: float = 0.5,
        peak_spacing: float = 100.0,
        peak_bases: bool = False,
        integration_scans: int = 20,
        detect_window: int = 15,
        rise_tolerance: float = 0.10,
        return_fraction: float = 0.05,
        width_limit: float = 4.0,
    ):
        """Mark, shade and label the integrated peaks of one chromatogram.

        Decorates an existing trace rather than drawing it, so the caller keeps
        control of the line itself. ``scale`` and ``offset`` map signal units
        onto the axes, which lets stacked XIC lanes share this code with a TIC
        plotted in raw units. Returns the peak indices and their areas.
        """
        times = np.asarray(times, dtype=float)
        values = np.asarray(values, dtype=float)
        if plot_times is None:
            plot_times = times
        deltas = np.diff(times)
        positive = deltas[deltas > 0]
        median_step = float(np.median(positive)) if positive.size else 1.0
        detection = values / (float(values.max()) or 1.0)
        drawn = values / scale + offset
        peaks = find_peaks(
            detection,
            height=peak_threshold,
            distance=max(1, math.ceil(peak_spacing / median_step)),
        )[0]
        if peak_bases and peaks.size:
            bounds = peak_base_bounds(
                values,
                peaks,
                detect_window=detect_window,
                rise_tolerance=rise_tolerance,
                return_fraction=return_fraction,
                width_limit=width_limit,
            )
        else:
            bounds = [
                (
                    max(0, int(peak) - 1),
                    min(int(peak) + integration_scans, values.size),
                    0.0,
                    0.0,
                )
                for peak in peaks
            ]

        areas = []
        for peak, (start, stop, left_level, right_level) in zip(peaks, bounds):
            window = slice(start, stop)
            window_times = times[window]
            window_values = values[window]
            if peak_bases and window_values.size > 1:
                base = np.interp(
                    window_times,
                    window_times[[0, -1]],
                    [left_level, right_level],
                )
            else:
                base = np.zeros_like(window_values)
            area = (
                float(
                    np.trapezoid(
                        np.maximum(window_values - base, 0.0), window_times
                    )
                )
                if window_values.size > 1
                else float(window_values[0] * median_step)
            )
            areas.append(area)

            base_curve = base / scale + offset
            ax.fill_between(
                plot_times[window],
                base_curve,
                np.maximum(drawn[window], base_curve),
                color=color,
                alpha=0.24,
                zorder=1,
            )
            if peak_bases and window_values.size > 1:
                ax.plot(
                    plot_times[window],
                    base_curve,
                    color=color,
                    linewidth=1.0,
                    linestyle="--",
                    zorder=2,
                )
            ax.scatter(
                plot_times[peak],
                drawn[peak],
                color=color,
                edgecolor="black",
                linewidth=0.5,
                s=24,
                zorder=3,
            )
            ax.annotate(
                f"A={area:.2e}",
                xy=(plot_times[peak], drawn[peak]),
                xytext=(6, -7),
                textcoords="offset points",
                fontsize=label_fontsize,
                color=color,
                ha="left",
                va="top",
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": "none",
                    "alpha": 0.7,
                },
                zorder=4,
            )
        return peaks, areas


    return (annotate_chromatogram_peaks,)


@app.cell(hide_code=True)
def MatplotlibRangeBrush(anywidget, traitlets):
    class MatplotlibRangeBrush(anywidget.AnyWidget):
        image = traitlets.Unicode().tag(sync=True)
        width = traitlets.Int().tag(sync=True)
        height = traitlets.Int().tag(sync=True)
        axes_bounds = traitlets.List(traitlets.Float()).tag(sync=True)
        times = traitlets.List(traitlets.Float()).tag(sync=True)
        selection_start = traitlets.Int(0).tag(sync=True)
        selection_stop = traitlets.Int(1).tag(sync=True)

        _esm = r"""
        const SVG_NS = "http://www.w3.org/2000/svg";

        function svgNode(name, attrs = {}) {
          const node = document.createElementNS(SVG_NS, name);
          for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
          return node;
        }

        function render({ model, el }) {
          const controller = new AbortController();
          const { signal } = controller;
          el.classList.add("mpl-range-brush");

          const instruction = document.createElement("div");
          instruction.className = "mpl-range-instruction";
          instruction.textContent = "Click for one scan · drag horizontally for a scan range";
          const stage = document.createElement("div");
          stage.className = "mpl-range-stage";
          const image = document.createElement("img");
          image.alt = "Total-ion chromatogram";
          image.draggable = false;
          const svg = svgNode("svg");
          const selection = svgNode("rect", { class: "mpl-range-selection" });
          const leftHandle = svgNode("line", { class: "mpl-range-handle" });
          const rightHandle = svgNode("line", { class: "mpl-range-handle" });
          const overlay = svgNode("rect", { class: "mpl-range-overlay" });
          svg.append(selection, leftHandle, rightHandle, overlay);
          stage.append(image, svg);
          el.append(instruction, stage);

          let dragging = false;
          let anchor = 0;
          let preview = null;

          function dimensions() {
            const width = model.get("width");
            const height = model.get("height");
            const [left, top, right, bottom] = model.get("axes_bounds");
            return { width, height, left, top, right, bottom };
          }

          function nearestPosition(event) {
            const times = model.get("times");
            const { width, left, right } = dimensions();
            const rect = svg.getBoundingClientRect();
            const px = ((event.clientX - rect.left) / rect.width) * width;
            const ratio = Math.max(0, Math.min(1, (px - left) / (right - left)));
            const target = times[0] + ratio * (times[times.length - 1] - times[0]);
            let low = 0;
            let high = times.length - 1;
            while (low < high) {
              const mid = Math.floor((low + high) / 2);
              if (times[mid] < target) low = mid + 1;
              else high = mid;
            }
            if (low > 0 && Math.abs(times[low - 1] - target) < Math.abs(times[low] - target)) {
              return low - 1;
            }
            return low;
          }

          function xForPosition(position) {
            const times = model.get("times");
            const { left, right } = dimensions();
            const span = times[times.length - 1] - times[0] || 1;
            return left + ((times[position] - times[0]) / span) * (right - left);
          }

          function draw() {
            const times = model.get("times");
            const { width, height, left, top, right, bottom } = dimensions();
            image.src = model.get("image");
            svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
            overlay.setAttribute("x", left);
            overlay.setAttribute("y", top);
            overlay.setAttribute("width", right - left);
            overlay.setAttribute("height", bottom - top);

            let start = model.get("selection_start");
            let stop = model.get("selection_stop");
            if (preview) [start, stop] = preview;
            start = Math.max(0, Math.min(start, times.length - 1));
            stop = Math.max(start + 1, Math.min(stop, times.length));
            const last = stop - 1;
            const leftX = xForPosition(start);
            const rightX = xForPosition(last);
            const halfStep = Math.max((right - left) / Math.max(times.length - 1, 1) / 2, 1.5);
            const brushLeft = Math.max(left, leftX - halfStep);
            const brushRight = Math.min(right, rightX + halfStep);
            selection.setAttribute("x", brushLeft);
            selection.setAttribute("y", top);
            selection.setAttribute("width", Math.max(3, brushRight - brushLeft));
            selection.setAttribute("height", bottom - top);
            for (const [handle, x] of [[leftHandle, brushLeft], [rightHandle, brushRight]]) {
              handle.setAttribute("x1", x);
              handle.setAttribute("x2", x);
              handle.setAttribute("y1", top);
              handle.setAttribute("y2", bottom);
            }
            const count = stop - start;
          }

          svg.addEventListener("pointerdown", (event) => {
            event.preventDefault();
            dragging = true;
            anchor = nearestPosition(event);
            preview = [anchor, anchor + 1];
            svg.setPointerCapture(event.pointerId);
            draw();
          }, { signal });
          svg.addEventListener("pointermove", (event) => {
            if (!dragging) return;
            const current = nearestPosition(event);
            const first = Math.min(anchor, current);
            const last = Math.max(anchor, current);
            preview = [first, last + 1];
            draw();
          }, { signal });
          svg.addEventListener("pointerup", (event) => {
            if (!dragging) return;
            dragging = false;
            const current = nearestPosition(event);
            const first = Math.min(anchor, current);
            const last = Math.max(anchor, current);
            preview = null;
            model.set("selection_start", first);
            model.set("selection_stop", last + 1);
            model.save_changes();
            draw();
          }, { signal });
          svg.addEventListener("pointercancel", () => {
            dragging = false;
            preview = null;
            draw();
          }, { signal });

          model.on("change:image", draw);
          model.on("change:selection_start", draw);
          model.on("change:selection_stop", draw);
          draw();
          return () => controller.abort();
        }

        export default { render };
        """

        _css = r"""
        .mpl-range-brush { width: 100%; max-width: 100%; }
        .mpl-range-stage { position: relative; width: 100%; line-height: 0; }
        .mpl-range-stage img { display: block; width: 100%; height: auto; user-select: none; }
        .mpl-range-stage svg { position: absolute; inset: 0; width: 100%; height: 100%; }
        .mpl-range-overlay { fill: transparent; cursor: crosshair; touch-action: none; }
        .mpl-range-selection { fill: #f28e2b; fill-opacity: 0.22; pointer-events: none; }
        .mpl-range-handle { stroke: #e07000; stroke-width: 2; vector-effect: non-scaling-stroke; pointer-events: none; }
        .mpl-range-instruction { margin: 0 0 4px; font-size: 0.84rem; opacity: 0.72; }
        .mpl-range-status { margin-top: 4px; font: 600 0.86rem/1.35 ui-monospace, SFMono-Regular, monospace; }
        @media (prefers-color-scheme: dark) {
          .mpl-range-selection { fill: #ffad55; }
          .mpl-range-handle { stroke: #ffad55; }
        }
        """

    return (MatplotlibRangeBrush,)


@app.cell(hide_code=True)
def _(mo):
    spectrum_mass_range = mo.ui.range_slider(
        0, 100, step=0.5, value=[0, 100], show_value=True,
        label="Mass range (%)", full_width=True,
    )
    spectrum_peak_threshold = mo.ui.slider(
        0, 100, step=1, value=10, show_value=True,
        label="Peak threshold (%)", full_width=True,
    )
    spectrum_min_peak_distance = mo.ui.number(
        0.1, 100, step=0.1, value=1,
        label="Minimum peak distance (m/z)", full_width=True,
    )
    spectrum_prominence = mo.ui.number(
        0, 100, step=0.1, value=0, label="Peak prominence", full_width=True,
    )
    chromatogram_time_range = mo.ui.range_slider(
        0, 100, step=0.5, value=[0, 100], show_value=True,
        label="Time range (%)", full_width=True,
    )
    chromatogram_smoothing = mo.ui.number(
        1, 101, step=2, value=1, label="Smoothing (pts)", full_width=True,
    )
    spectrum_xic_mzs = mo.ui.text(
        placeholder="e.g. 115.4 (Amine), 149.1 (Aldehyde hemiacetal), 231.1 ([1 + 1])",
        label="Extracted-ion m/z values",
        full_width=True,
    )
    spectrum_xic_delta = mo.ui.number(
        0.01, 10, step=0.01, value=0.5,
        label="Extracted-ion tolerance", full_width=True,
    )
    chromatogram_integration_scans = mo.ui.number(
        1, 1000, step=1, value=20,
        label="Scans integrated", full_width=True,
    )
    chromatogram_peak_bases = mo.ui.switch(value=False, label="Peak bases")
    chromatogram_peak_threshold = mo.ui.slider(
        1, 100, step=1, value=50, show_value=True,
        label="Peak threshold (%)", full_width=True,
    )
    chromatogram_peak_spacing = mo.ui.number(
        1, 1000, step=1, value=100,
        label="Minimum peak spacing (s)", full_width=True,
    )
    chromatogram_base_smoothing = mo.ui.number(
        3, 101, step=2, value=15,
        label="Base detection smoothing (pts)", full_width=True,
    )
    chromatogram_base_rise = mo.ui.slider(
        0, 50, step=1, value=10, show_value=True,
        label="Base rise tolerance (%)", full_width=True,
    )
    chromatogram_base_return = mo.ui.slider(
        0, 100, step=1, value=5, show_value=True,
        label="Base return to baseline (%)", full_width=True,
    )
    chromatogram_base_width = mo.ui.number(
        1.0, 20.0, step=0.5, value=4.0,
        label="Max width (x half-width)", full_width=True,
    )
    spectrum_show_peak_intensities = mo.ui.checkbox(
        value=False, label="Label peak intensities"
    )
    spectrum_rotate_labels = mo.ui.checkbox(value=False, label="Rotate peak labels")
    spectrum_series = mo.ui.checkbox(value=False, label="Plot scans individually")
    spectrum_average = mo.ui.checkbox(
        value=False, label="Average selected scans (unchecked: sum)"
    )
    spectrum_truncate_start_time = mo.ui.checkbox(
        value=False, label="Start selected time range at zero"
    )
    return (
        chromatogram_base_return,
        chromatogram_base_rise,
        chromatogram_base_smoothing,
        chromatogram_base_width,
        chromatogram_integration_scans,
        chromatogram_peak_bases,
        chromatogram_peak_spacing,
        chromatogram_peak_threshold,
        chromatogram_smoothing,
        chromatogram_time_range,
        spectrum_average,
        spectrum_mass_range,
        spectrum_min_peak_distance,
        spectrum_peak_threshold,
        spectrum_prominence,
        spectrum_rotate_labels,
        spectrum_series,
        spectrum_show_peak_intensities,
        spectrum_truncate_start_time,
        spectrum_xic_delta,
        spectrum_xic_mzs,
    )


@app.cell(hide_code=True)
def chromatogram_peak_settings(
    chromatogram_base_return,
    chromatogram_base_rise,
    chromatogram_base_smoothing,
    chromatogram_base_width,
    chromatogram_integration_scans,
    chromatogram_peak_bases,
    chromatogram_peak_spacing,
    chromatogram_peak_threshold,
    chromatogram_smoothing,
):
    chromatogram_peak_settings = {
        "peak_threshold": chromatogram_peak_threshold.value / 100,
        "peak_spacing": float(chromatogram_peak_spacing.value),
        "peak_bases": chromatogram_peak_bases.value,
        "integration_scans": int(chromatogram_integration_scans.value),
        "detect_window": max(
            int(chromatogram_base_smoothing.value),
            int(chromatogram_smoothing.value),
        ),
        "rise_tolerance": chromatogram_base_rise.value / 100,
        "return_fraction": chromatogram_base_return.value / 100,
        "width_limit": float(chromatogram_base_width.value),
    }
    return (chromatogram_peak_settings,)


@app.cell(hide_code=True)
def _(
    MatplotlibRangeBrush,
    annotate_chromatogram_peaks,
    base64,
    chromatogram_peak_settings,
    chromatogram_smoothing,
    chromatogram_time_range,
    io,
    load_experiment,
    mo,
    np,
    plt,
    selected_path,
    smooth_trace,
    spectrum_truncate_start_time,
):
    _selector_sample = selected_path.stem
    _selector_data = load_experiment(selected_path)
    _selector_times = np.asarray(_selector_data["times"])
    _selector_intensities = np.asarray(_selector_data["intensities"])
    _selector_plot_times = (
        _selector_times - _selector_times[0]
        if spectrum_truncate_start_time.value
        else _selector_times
    )

    _selector_full_tic = smooth_trace(
        _selector_intensities.sum(axis=1), chromatogram_smoothing.value
    )
    _selector_start_pct, _selector_end_pct = chromatogram_time_range.value
    _selector_span = float(_selector_plot_times[-1] - _selector_plot_times[0])
    _selector_start_time = float(_selector_plot_times[0]) + (
        _selector_span * _selector_start_pct / 100
    )
    _selector_end_time = float(_selector_plot_times[0]) + (
        _selector_span * _selector_end_pct / 100
    )
    _selector_mask = (_selector_plot_times >= _selector_start_time) & (
        _selector_plot_times <= _selector_end_time
    )
    if int(_selector_mask.sum()) < 2:
        _selector_mask = np.ones_like(_selector_plot_times, dtype=bool)
    _selector_indices = np.flatnonzero(_selector_mask)
    tic_range_offset = int(_selector_indices[0])
    _selector_times = _selector_times[_selector_mask]
    _selector_plot_times = _selector_plot_times[_selector_mask]
    _selector_tic = _selector_full_tic[_selector_mask]

    _selector_fig, _selector_ax = plt.subplots(figsize=(12.3, 3.2))
    (_selector_line,) = _selector_ax.plot(_selector_plot_times, _selector_tic)
    annotate_chromatogram_peaks(
        _selector_ax,
        _selector_times,
        _selector_tic,
        plot_times=_selector_plot_times,
        color=_selector_line.get_color(),
        **chromatogram_peak_settings,
    )
    _selector_ax.set(ylabel="TIC", xlabel="Time (s)")
    _selector_fig.tight_layout()
    _selector_fig.canvas.draw()
    _selector_width, _selector_height = _selector_fig.canvas.get_width_height()
    _selector_bbox = _selector_ax.get_window_extent()
    _selector_axes_bounds = [
        float(_selector_bbox.x0),
        float(_selector_height - _selector_bbox.y1),
        float(_selector_bbox.x1),
        float(_selector_height - _selector_bbox.y0),
    ]
    _selector_buffer = io.BytesIO()
    _selector_fig.savefig(_selector_buffer, format="png")
    _selector_png = _selector_buffer.getvalue()
    _selector_svg_buffer = io.BytesIO()
    _selector_fig.savefig(_selector_svg_buffer, format="svg")
    _selector_image = "data:image/png;base64," + base64.b64encode(
        _selector_png
    ).decode("ascii")
    plt.close(_selector_fig)
    _selector_middle = len(_selector_times) // 2

    tic_range_selector = mo.ui.anywidget(
        MatplotlibRangeBrush(
            image=_selector_image,
            width=int(_selector_width),
            height=int(_selector_height),
            axes_bounds=_selector_axes_bounds,
            times=[float(value) for value in _selector_plot_times],
            selection_start=_selector_middle,
            selection_stop=_selector_middle + 1,
        )
    )

    tic_download = mo.download(
        data=_selector_svg_buffer.getvalue(),
        filename=f"{_selector_sample}_TIC.svg",
        mimetype="image/svg+xml",
        label="Save TIC (SVG)",
    )
    return tic_download, tic_range_offset, tic_range_selector


@app.cell(hide_code=True)
def _(Path, datx_browser, mo):
    mo.stop(
        not datx_browser.value,
        mo.vstack(
            [
                mo.md("## Interactive exploration"),
                datx_browser,
                mo.callout(
                    "Pick a `.datx` acquisition above to get started.", kind="info"
                ),
            ],
            gap=0.75,
        ),
    )

    selected_path = Path(datx_browser.value[0].path)

    mo.vstack([mo.md("## Interactive exploration"), datx_browser], gap=0.75)
    return (selected_path,)


@app.cell(hide_code=True)
def _(load_experiment, mo, np, selected_path):
    def _settings_table(settings: dict, title: str):
        """Render a flattened XML settings bag as a two-column table."""
        if not settings:
            return mo.md(f"_No {title.lower()} recorded._")
        # Values are raw XML text, so a stray pipe would split the table row.
        body = "\n".join(
            "| `{}` | {} |".format(key, value.replace("|", r"\|"))
            for key, value in settings.items()
        )
        return mo.md("| Setting | Value |\n| --- | --- |\n" + body)

    _meta_path = selected_path
    _meta = load_experiment(_meta_path)
    _method = _meta["method"]
    _ion = _meta["ion_source"]
    _times = _meta["times"]
    _masses = _meta["masses"]

    # The instrument records the scan window in the method rather than in the
    # data itself, and the scan mode is carried as an xsi:type attribute.
    _scan_mode = _method.get("scanMode/@type", "").removesuffix("ScanMode")
    _scan_window = (
        f"{float(_method['scanMode/start']):g}\u2013{float(_method['scanMode/end']):g}"
        if {"scanMode/start", "scanMode/end"} <= _method.keys()
        else f"{_masses[0]:.1f}\u2013{_masses[-1]:.1f}"
    )
    _scan_time = _method.get("scanMode/scanTime")
    _polarity = {"true": "negative", "false": "positive"}.get(
        _ion.get("negative", ""), "unknown"
    )
    _source = _ion.get("ionSource/@type", "").removesuffix("Source").upper() or "unknown"
    _median_step = float(np.median(np.diff(_times))) if _times.size > 1 else 0.0

    _rows = [
        ("File", f"`{_meta_path.name}`"),
        ("Acquired", _meta["date"] or "—"),
        (
            "Instrument",
            " · ".join(
                _part
                for _part in (_meta["hardware_type"], _meta["instrument_id"])
                if _part
            )
            or "—",
        ),
        (
            "Software / firmware",
            f"{_meta['software_version'] or '—'} / "
            f"{_meta['firmware_version'] or '—'}",
        ),
        ("Ionisation", f"{_source}, {_polarity} mode"),
        (
            "Scan mode",
            f"{_scan_mode or 'unknown'}, m/z {_scan_window}"
            + (f", {float(_scan_time):g} ms/scan" if _scan_time else ""),
        ),
        (
            "Acquisition",
            f"{len(_times):,} scans over {_times[-1] - _times[0]:.1f} s "
            f"({_median_step:.2f} s/scan), "
            f"{'centroid' if _meta['is_centroid'] else 'profile'} data",
        ),
        (
            "m/z axis",
            f"{len(_masses):,} samples, {_masses[0]:.2f}\u2013{_masses[-1]:.2f} "
            f"(\u0394 {float(np.median(np.diff(_masses))):.3f})",
        ),
        (
            "Segments / channels",
            f"{len(_meta['segment_times'])} segment(s)"
            + (
                f", channels: {', '.join(_meta['scalar_channels'])}"
                if _meta["scalar_channels"]
                else ""
            )
            + (
                f", aux: {', '.join(_name for _name, _ in _meta['aux_files'])}"
                if _meta["aux_files"]
                else ""
            ),
        ),
        (
            "Total ion current",
            f"{_meta['intensities'].sum():.3e} "
            f"(max scan {_meta['intensities'].sum(axis=1).max():.3e})",
        ),
    ]

    mo.vstack(
        [
            mo.md(
                "| | |\n| --- | --- |\n"
                + "\n".join(f"| **{_label}** | {_value} |" for _label, _value in _rows)
            ),
            mo.accordion(
                {
                    "Method": _settings_table(_method, "method settings"),
                    "Ion source": _settings_table(_ion, "ion source settings"),
                    "Tune parameters": _settings_table(_meta["tune"], "tune parameters"),
                    "Experiment log": mo.plain_text(_meta["log"] or "No log recorded."),
                }
            ),
        ],
        gap=0.5,
    )
    return


@app.cell(hide_code=True)
def spectrum_result(
    OUTPUT_HOME,
    annotate_chromatogram_peaks,
    chromatogram_base_return,
    chromatogram_base_rise,
    chromatogram_base_smoothing,
    chromatogram_base_width,
    chromatogram_integration_scans,
    chromatogram_peak_bases,
    chromatogram_peak_settings,
    chromatogram_peak_spacing,
    chromatogram_peak_threshold,
    chromatogram_smoothing,
    chromatogram_time_range,
    find_peaks,
    load_experiment,
    math,
    mo,
    np,
    plt,
    selected_path,
    smooth_trace,
    sns,
    spectrum_average,
    spectrum_mass_range,
    spectrum_min_peak_distance,
    spectrum_peak_threshold,
    spectrum_prominence,
    spectrum_rotate_labels,
    spectrum_series,
    spectrum_show_peak_intensities,
    spectrum_truncate_start_time,
    spectrum_xic_delta,
    spectrum_xic_mzs,
    tic_download,
    tic_range_offset,
    tic_range_selector,
):
    _spec_sample = selected_path.stem
    _spec_data = load_experiment(selected_path)
    _spec_times = np.asarray(_spec_data["times"])
    _spec_all_masses = np.asarray(_spec_data["masses"])
    _spec_intensities = np.asarray(_spec_data["intensities"])
    _spec_selector_state = tic_range_selector.value
    _spec_scan_start = max(
        0,
        min(
            tic_range_offset + int(_spec_selector_state["selection_start"]),
            len(_spec_times) - 1,
        ),
    )
    _spec_scan_stop = max(
        _spec_scan_start + 1,
        min(
            tic_range_offset + int(_spec_selector_state["selection_stop"]),
            len(_spec_times),
        ),
    )
    _spec_scan_last = _spec_scan_stop - 1

    _spec_controls = mo.vstack(
        [
            mo.md("## Spectrum explorer"),
            mo.hstack(
                [
                    spectrum_mass_range,
                    chromatogram_time_range,
                    spectrum_peak_threshold,
                    spectrum_min_peak_distance,
                    chromatogram_smoothing,
                ],
                widths=[2, 2, 2, 1, 1],
                align="end",
            ),
            mo.accordion(
                {
                    "Extracted-ion chromatograms": mo.vstack(
                        [
                            mo.hstack(
                                [spectrum_xic_mzs, spectrum_xic_delta],
                                widths=[4, 1],
                                align="end",
                            ),
                        ],
                        gap=0.5,
                    ),
                    "Chromatogram peaks and integration": mo.vstack(
                        [
                            mo.hstack(
                                [
                                    chromatogram_peak_threshold,
                                    chromatogram_peak_spacing,
                                    chromatogram_integration_scans,
                                    chromatogram_peak_bases,
                                ],
                                widths=[2, 1, 1, 1],
                                align="end",
                            ),
                            mo.hstack(
                                [
                                    chromatogram_base_return,
                                    chromatogram_base_rise,
                                    chromatogram_base_smoothing,
                                    chromatogram_base_width,
                                ],
                                widths=[2, 2, 1, 1],
                                align="end",
                            ),
                        ],
                        gap=0.5,
                    ),
                    "Advanced display and peak settings": mo.vstack(
                        [
                            spectrum_prominence,
                            mo.hstack(
                                [
                                    spectrum_show_peak_intensities,
                                    spectrum_rotate_labels,
                                    spectrum_series,
                                    spectrum_average,
                                    spectrum_truncate_start_time,
                                ],
                                justify="start",
                                wrap=True,
                            ),
                        ]
                    ),
                }
            ),
        ],
        gap=1,
    )

    _spec_mass_start_pct, _spec_mass_end_pct = spectrum_mass_range.value
    _spec_mass_start = _spec_all_masses[0] + (
        _spec_all_masses[-1] - _spec_all_masses[0]
    ) * _spec_mass_start_pct / 100
    _spec_mass_end = _spec_all_masses[0] + (
        _spec_all_masses[-1] - _spec_all_masses[0]
    ) * _spec_mass_end_pct / 100
    _spec_mass_mask = (_spec_all_masses >= _spec_mass_start) & (
        _spec_all_masses <= _spec_mass_end
    )
    _spec_masses = _spec_all_masses[_spec_mass_mask]
    mo.stop(
        len(_spec_masses) < 2,
        mo.vstack(
            [_spec_controls, mo.callout("Select a wider mass range.", kind="warn")]
        ),
    )

    _spec_scans = _spec_intensities[
        _spec_scan_start:_spec_scan_stop, _spec_mass_mask
    ]
    _spec_scan = (
        _spec_scans.mean(axis=0)
        if spectrum_average.value
        else _spec_scans.sum(axis=0)
    )
    _spec_tic = _spec_scans.sum()
    _spec_scan_max = float(_spec_scan.max()) if _spec_scan.size else 0.0
    _spec_threshold = spectrum_peak_threshold.value / 100 * _spec_scan_max
    _spec_mass_step = float(np.median(np.diff(_spec_masses)))
    _spec_distance_bins = max(
        1,
        math.ceil(float(spectrum_min_peak_distance.value) / _spec_mass_step),
    )
    _spec_peaks = find_peaks(
        _spec_scan,
        height=_spec_threshold,
        distance=_spec_distance_bins,
        prominence=float(spectrum_prominence.value),
    )[0]
    _spec_xic_entries = []
    for _spec_xic_token in spectrum_xic_mzs.value.split(","):
        _spec_xic_token = _spec_xic_token.strip()
        if not _spec_xic_token:
            continue
        _spec_xic_number, _, _spec_xic_description = _spec_xic_token.partition("(")
        _spec_xic_number = _spec_xic_number.strip()
        _spec_xic_description = _spec_xic_description.strip().rstrip(")").strip()
        try:
            _spec_xic_mz_value = float(_spec_xic_number)
        except ValueError:
            continue
        _spec_xic_entries.append(
            (
                _spec_xic_mz_value,
                f"m/z {_spec_xic_number}"
                + (f" ({_spec_xic_description})" if _spec_xic_description else ""),
            )
        )
    _spec_xic_values = [_spec_entry[0] for _spec_entry in _spec_xic_entries]

    _spec_xic_count = len(_spec_xic_values)
    _spec_xic_fig = None
    _spec_area_fig = None
    _spec_xic_peak_records = []
    if _spec_xic_values:
        _spec_xic_fig, _spec_xic_ax = plt.subplots(
            figsize=(12.3, 1.85 * _spec_xic_count)
        )
    _spec_scan_fig, _spec_scan_ax = plt.subplots(figsize=(12.3, 4.37))
    _spec_plot_times = (
        _spec_times - _spec_times[0]
        if spectrum_truncate_start_time.value
        else _spec_times
    )

    if _spec_xic_values:
        for _spec_offset, (_spec_mz, _spec_xic_label) in enumerate(
            _spec_xic_entries
        ):
            _spec_xic_mask = (
                (_spec_all_masses > _spec_mz - spectrum_xic_delta.value)
                & (_spec_all_masses < _spec_mz + spectrum_xic_delta.value)
            )
            _spec_xic = smooth_trace(
                _spec_intensities[:, _spec_xic_mask].sum(axis=1),
                chromatogram_smoothing.value,
            )
            _spec_xic_scale = float(_spec_xic.max()) or 1.0
            _spec_xic_normalized = _spec_xic / _spec_xic_scale
            _spec_xic_baseline = 1.2 * _spec_offset
            (_spec_xic_line,) = _spec_xic_ax.plot(
                _spec_plot_times,
                _spec_xic_normalized + _spec_xic_baseline,
                label=_spec_xic_label,
                zorder=2,
            )
            _spec_xic_color = _spec_xic_line.get_color()
            _spec_xic_ax.axhline(
                _spec_xic_baseline,
                color="black",
                linewidth=0.8,
                linestyle="-",
                alpha=0.7,
                zorder=0,
            )
            for _spec_xic_fraction in np.arange(0.1, 1.01, 0.1):
                _spec_xic_ax.axhline(
                    _spec_xic_baseline + _spec_xic_fraction,
                    color="0.45",
                    linewidth=0.55,
                    linestyle=":",
                    alpha=0.45,
                    zorder=0,
                )
            _spec_xic_peaks, _spec_xic_areas = annotate_chromatogram_peaks(
                _spec_xic_ax,
                _spec_times,
                _spec_xic,
                plot_times=_spec_plot_times,
                scale=_spec_xic_scale,
                offset=_spec_xic_baseline,
                color=_spec_xic_color,
                **chromatogram_peak_settings,
            )
            _spec_xic_peak_records.append(
                (
                    np.asarray(_spec_plot_times)[_spec_xic_peaks],
                    np.asarray(_spec_xic_areas, dtype=float),
                    _spec_xic_color,
                    _spec_xic_label,
                )
            )
        _spec_xic_tick_fractions = np.arange(0.2, 1.01, 0.2)
        _spec_xic_tick_positions = [
            1.2 * _spec_ion_index + _spec_tick_fraction
            for _spec_ion_index in range(_spec_xic_count)
            for _spec_tick_fraction in _spec_xic_tick_fractions
        ]
        _spec_xic_tick_labels = [
            f"{round(100 * _spec_tick_fraction):d}%"
            for _spec_ion_index in range(_spec_xic_count)
            for _spec_tick_fraction in _spec_xic_tick_fractions
        ]
        _spec_time_start_pct, _spec_time_end_pct = chromatogram_time_range.value
        _spec_time_span = float(_spec_plot_times[-1] - _spec_plot_times[0])
        _spec_time_start = float(_spec_plot_times[0]) + (
            _spec_time_span * _spec_time_start_pct / 100
        )
        _spec_time_end = float(_spec_plot_times[0]) + (
            _spec_time_span * _spec_time_end_pct / 100
        )
        if _spec_time_end <= _spec_time_start:
            _spec_time_end = _spec_time_start + max(_spec_time_span, 1.0) * 1e-3
        _spec_xic_ax.set(
            xlim=(_spec_time_start, _spec_time_end),
            xlabel="Time (s)",
            ylabel="Normalized XIC",
            yticks=_spec_xic_tick_positions,
            yticklabels=_spec_xic_tick_labels,
            ylim=(-0.05, 1.2 * (_spec_xic_count - 1) + 1.05),
        )
        _spec_xic_ax.tick_params(
            axis="y",
            which="major",
            left=False,
            right=True,
            labelleft=False,
            labelright=True,
            labelsize=8.25,
            length=4,
        )
        _spec_xic_ax.legend(
            loc="lower center",
            bbox_to_anchor=(0.5, 1.01),
            fontsize=12.5,
            ncol=max(1, math.ceil(_spec_xic_count / 3)),
            frameon=False,
            borderaxespad=0,
            borderpad=0,
            labelspacing=0.3,
            handlelength=1.2,
            handletextpad=0.4,
            columnspacing=1.0,
        )

    if _spec_xic_values:
        _spec_area_fig, _spec_area_ax = plt.subplots(figsize=(12.3, 6.0))
        for (
            _spec_area_times,
            _spec_area_values,
            _spec_area_color,
            _spec_area_label,
        ) in _spec_xic_peak_records:
            _spec_area_normalized = _spec_area_values / (
                float(_spec_area_values.max()) if _spec_area_values.size else 1.0
            )
            _spec_area_ax.plot(
                _spec_area_times,
                _spec_area_normalized,
                linestyle=":",
                linewidth=0.9,
                alpha=0.55,
                color=_spec_area_color,
                zorder=2,
            )
            _spec_area_ax.plot(
                _spec_area_times,
                _spec_area_normalized,
                linestyle="none",
                marker="o",
                markersize=4.5,
                color=_spec_area_color,
                label=_spec_area_label,
                zorder=3,
            )
        _spec_area_ax.axhline(0.0, color="black", linewidth=0.8, alpha=0.7, zorder=1)
        _spec_area_tick_fractions = np.arange(0.0, 1.01, 0.1)
        for _spec_area_tick_fraction in _spec_area_tick_fractions:
            _spec_area_ax.axhline(
                _spec_area_tick_fraction,
                color="0.45",
                linewidth=0.55,
                linestyle=":",
                alpha=0.45,
                zorder=0,
            )
        _spec_area_ax.set(
            xlim=(_spec_time_start, _spec_time_end),
            ylim=(-0.03, 1.03),
            xlabel="Time (s)",
            ylabel="Normalized peak area",
            yticks=_spec_area_tick_fractions,
            yticklabels=[
                f"{round(100 * _spec_area_tick_fraction):d}%"
                for _spec_area_tick_fraction in _spec_area_tick_fractions
            ],
        )
        _spec_area_ax.tick_params(
            axis="y",
            which="major",
            left=False,
            right=True,
            labelleft=False,
            labelright=True,
            labelsize=8.25,
            length=4,
        )
        _spec_area_ax.legend(
            loc="lower right",
            fontsize=12.5,
            ncol=max(1, math.ceil(_spec_xic_count / 3)),
            labelspacing=0.3,
            handlelength=1.2,
            handletextpad=0.4,
            columnspacing=1.0,
            framealpha=0.85,
        )

    if spectrum_series.value and len(_spec_scans) > 1:
        _spec_colors = sns.color_palette("crest", n_colors=len(_spec_scans))
        for _spec_color, _spec_single_scan in zip(_spec_colors, _spec_scans):
            _spec_scan_ax.plot(_spec_masses, _spec_single_scan, color=_spec_color)
    else:
        _spec_scan_ax.plot(_spec_masses, _spec_scan)
    _spec_scan_ax.scatter(
        _spec_masses[_spec_peaks],
        _spec_scan[_spec_peaks],
        color="tab:red",
        s=30,
        zorder=10,
        marker="x",
        linewidth=1,
    )
    _spec_label_offset = max(
        (_spec_scan_max - float(_spec_scan.min())) * 0.02,
        1e-12,
    )
    for _spec_peak in _spec_peaks:
        _spec_label = f"{_spec_masses[_spec_peak]:.2f}"
        if spectrum_show_peak_intensities.value:
            _spec_label += f"\n{_spec_scan[_spec_peak]:.2e}"
        _spec_scan_ax.text(
            _spec_masses[_spec_peak],
            _spec_scan[_spec_peak] + _spec_label_offset,
            _spec_label,
            color="tab:red",
            fontsize=10,
            horizontalalignment="center",
            rotation=90 if spectrum_rotate_labels.value else 0,
        )
    _spec_aggregation = "Average" if spectrum_average.value else "Sum"
    if len(_spec_scans) == 1:
        _spec_legend_entries = [
            f"Scan {_spec_scan_start}",
            f"t = {_spec_plot_times[_spec_scan_start]:.1f} s",
            f"TIC {_spec_tic:.2e}",
        ]
    else:
        _spec_legend_entries = [
            f"{_spec_aggregation} of {len(_spec_scans)} scans",
            f"Scans {_spec_scan_start}–{_spec_scan_last}",
            f"{_spec_plot_times[_spec_scan_start]:.1f}–"
            f"{_spec_plot_times[_spec_scan_last]:.1f} s",
            f"Integrated TIC {_spec_tic:.2e}",
        ]
    _spec_scan_ax.set(ylabel="Intensity", xlabel="m/z")
    _spec_scan_ax.legend(
        handles=[plt.Line2D([], [], linestyle="none")],
        labels=[" · ".join(_spec_legend_entries)],
        loc="upper right",
        fontsize=10,
        handlelength=0,
        handletextpad=0,
        borderpad=0.4,
        framealpha=0.85,
    )
    if _spec_scan_max > 0:
        _spec_scan_ax.set_ylim(
            0,
            _spec_scan_max * (1.3 if spectrum_rotate_labels.value else 1.15),
        )
    if _spec_xic_fig is not None:
        _spec_xic_fig.tight_layout()
    if _spec_area_fig is not None:
        _spec_area_fig.tight_layout()
    _spec_scan_fig.tight_layout()

    _spec_filename = (
        f"scan{_spec_scan_start}"
        if len(_spec_scans) == 1
        else f"scan{_spec_scan_start}-{_spec_scan_last}"
    )


    def _export_spectrum(_):
        _directory = OUTPUT_HOME / _spec_sample
        _directory.mkdir(parents=True, exist_ok=True)
        _path = _directory / f"{_spec_filename}.csv"
        np.savetxt(
            _path,
            np.column_stack([_spec_masses, _spec_scan]),
            delimiter=",",
            header="m/z,intensity",
            comments="",
        )


    _spec_export = mo.ui.button(label="Export CSV", on_click=_export_spectrum)
    mo.vstack(
        [
            _spec_controls,
            tic_range_selector,
            mo.hstack([tic_download], justify="end"),
            *([_spec_xic_fig] if _spec_xic_fig is not None else []),
            *([_spec_area_fig] if _spec_area_fig is not None else []),
            _spec_scan_fig,
            _spec_export,
        ],
        gap=0.5,
    )
    return


if __name__ == "__main__":
    app.run()
