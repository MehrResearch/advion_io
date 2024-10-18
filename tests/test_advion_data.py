from advion_io import AdvionData

EXAMPLE = b"data\\2024_7_1_14_0_16.datx"

def test_advion_data_reader():
    data = AdvionData(EXAMPLE, False, False)
    assert(data.get_num_masses() > 1)
    assert(data.get_num_spectra() > 1)
    assert(data.get_TIC(10) > 1.0)
    assert(len(data.get_retention_times()) == data.get_num_spectra())

    assert(len(data.get_masses()) == len(data.get_spectrum(34)))