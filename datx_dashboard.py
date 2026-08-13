import marimo

__generated_with = "0.23.6"
app = marimo.App(width="medium")


@app.cell
def _():
    from pathlib import Path

    from matplotlib import pyplot as plt

    from advion_io import DatxFile

    return DatxFile, Path, plt


@app.cell
def _(DatxFile, Path):
    path = Path("tests/data/example.datx")
    f = DatxFile(path)
    return (f,)


@app.cell
def _(f, plt):
    plt.plot(f.masses, f.intensities.T)
    plt.xlabel("m/z")
    plt.ylabel("intensity")
    plt.gca()
    return


@app.cell
def _(f, plt):
    plt.plot(f.retention_times, f.intensities.sum(axis=1))
    plt.xlabel("retention time (min)")
    plt.ylabel("TIC")
    plt.gca()
    return


if __name__ == "__main__":
    app.run()
