import pytest

from _testutils import MockHidapiDevice, MockRuntimeStorage
from liquidctl.driver.coolit import Coolit


class MockDevice(MockHidapiDevice):
    def read(self, length, **kwargs):
        data = super().read(length, **kwargs)
        return data if data is not None else [0] * length


@pytest.fixture
def mock_h110i_gt():
    mock_raw_dev = MockDevice(vendor_id=0xDEAD, product_id=0xBEEF, address="42")
    mock_storage = MockRuntimeStorage(key_prefixes=["mock_h110i_gt"])
    dev = Coolit(
        mock_raw_dev,
        "Mock H100i GT",
        fan_count=2,
        rgb_fans=False,
    )
    return dev.connect(runtime_storage=mock_storage)


@pytest.fixture
def mock_commander_mini():
    mock_raw_dev = MockDevice(vendor_id=0x1B1C, product_id=0x0C04, address="42")
    mock_storage = MockRuntimeStorage(key_prefixes=["mock_commander_mini"])
    dev = Coolit(
        mock_raw_dev,
        "Corsair Commander Mini",
        fan_count=6,
        has_pump=False,
        temp_sensor_count=4,
        rgb_fans=False,
    )
    return dev.connect(runtime_storage=mock_storage)


def _probe_handle(device_id):
    handle = MockHidapiDevice(vendor_id=0x1B1C, product_id=0x0C04, address="42")
    if device_id is not None:
        handle.preload_read((0, [0x01, 0x07, device_id] + [0] * 61))
    return handle


def _select_read_response(values):
    resp = []
    for lo, hi in values:
        resp += [0x00, 0x06, 0x00, 0x09, lo, hi]
    return resp


def test_driver_not_totally_broken(mock_h110i_gt):
    cooler = mock_h110i_gt
    cooler.initialize()
    _ = cooler.get_status(pump_mode="extreme")
    cooler.set_fixed_speed("fan1", 42)
    cooler.set_speed_profile("fan2", [(20, 30), (40, 90)])


def test_probe_commander_mini():
    dev = next(Coolit.probe(_probe_handle(0x3D)))
    assert dev.description == "Corsair Commander Mini"
    assert dev._fan_count == 6
    assert dev._has_pump is False
    assert dev._temp_sensor_count == 4
    assert dev._fan_names == ["fan1", "fan2", "fan3", "fan4", "fan5", "fan6"]


def test_probe_h110i_gt():
    dev = next(Coolit.probe(_probe_handle(0x41)))
    assert dev.description == "Corsair H110i GT"
    assert dev._fan_count == 2
    assert dev._has_pump is True
    assert dev._temp_sensor_count == 1


def test_probe_unknown_device_id_falls_back_to_h110i_gt():
    dev = next(Coolit.probe(_probe_handle(0x99)))
    assert dev.description == "Corsair H110i GT"


def test_probe_read_failure_falls_back_to_h110i_gt():
    dev = next(Coolit.probe(_probe_handle(None)))
    assert dev.description == "Corsair H110i GT"


def test_probe_match_filter():
    assert list(Coolit.probe(_probe_handle(0x3D), match="H110i")) == []
    dev = next(Coolit.probe(_probe_handle(0x3D), match="Commander"))
    assert dev.description == "Corsair Commander Mini"


def test_commander_mini_status(mock_commander_mini):
    dev = mock_commander_mini
    speeds = (1000, 1100, 1200, 1300, 1400, 1500)
    dev.device.preload_read((0, _select_read_response([(0, 20), (128, 25), (0, 30), (64, 35)])))
    dev.device.preload_read((0, _select_read_response([(s & 0xFF, s >> 8) for s in speeds])))

    status = dev.get_status()

    assert status == [
        ("Temperature 1", 20.0, "°C"),
        ("Temperature 2", 25.5, "°C"),
        ("Temperature 3", 30.0, "°C"),
        ("Temperature 4", 35.25, "°C"),
        ("Fan 1 speed", 1000, "rpm"),
        ("Fan 2 speed", 1100, "rpm"),
        ("Fan 3 speed", 1200, "rpm"),
        ("Fan 4 speed", 1300, "rpm"),
        ("Fan 5 speed", 1400, "rpm"),
        ("Fan 6 speed", 1500, "rpm"),
    ]


def test_commander_mini_set_fixed_speed(mock_commander_mini):
    dev = mock_commander_mini
    dev.set_fixed_speed("fan3", 50)

    commands = [tuple(r.data) for r in dev.device.sent]

    assert len(commands) == 18
    for index in range(6):
        select, mode, pwm = commands[index * 3 : index * 3 + 3]
        assert select[1:4] == (0x06, 0x10, index)
        assert mode[1:4] == (0x06, 0x12, 0x02)
        assert pwm[1:4] == (0x06, 0x13, 0x80 if index == 2 else 0xFF)


def test_commander_mini_set_speed_profile(mock_commander_mini):
    dev = mock_commander_mini
    dev.set_speed_profile("fan5", [(20, 30), (40, 90)])

    commands = [tuple(r.data) for r in dev.device.sent]

    multi = [c for c in commands if len(c) == 63]
    assert len(multi) == 1
    assert multi[0][1:4] == (0x06, 0x10, 0x04)
    assert any(c[1:4] == (0x06, 0x12, 0x0E) for c in commands if len(c) == 4)


# fmt: off
_H110I_GT_BASELINE = {
    "INIT": ["020901"],
    "STATUS": ["03090e040610000509160606100107091608061002090916000000000000000000000000000000000000000000000000000000000000000000000000000000"],
    "FIXED1": ["0a061000", "0b061202", "0c06136b", "0d061001", "0e061202", "0f0613ff", "100610021108142e09000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"],
    "FIXED2": ["12061000", "13061202", "1406136b", "15061001", "16061202", "170613c4", "180610021908142e09000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"],
    "PROFILE1": ["1a0610001b09170000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "1c061000", "1d06120e", "1e0a190a00000000000000000000", "1f0a1a0a00140028003c003c003c", "01061001", "02061202", "030613c4", "040610020508142e09000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"],
    "PROFILE2": ["060610000709170000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "08061000", "0906120e", "0a0a190a00000000000000000000", "0b0a1a0a00140028003c003c003c", "0c0610000d09170000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000", "0e061001", "0f06120e", "100a190a00000000000000000000", "110a1a0a00140028003c003c003c", "120610021308142e09000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"],
}
# fmt: on


def test_h110i_gt_unchanged_byte_for_byte():
    dev = MockDevice(vendor_id=0x1B1C, product_id=0x0C04, address="42")
    storage = MockRuntimeStorage(key_prefixes=["h110i_gt_regression"])
    cooler = Coolit(
        dev,
        "Corsair H110i GT",
        fan_count=2,
        has_pump=True,
        temp_sensor_count=1,
        rgb_fans=False,
    )
    cooler.connect(runtime_storage=storage)

    def capture(fn):
        dev.sent.clear()
        fn()
        return [bytes(r.data).hex() for r in dev.sent]

    result = capture(cooler.initialize)
    assert result == _H110I_GT_BASELINE["INIT"]
    result = capture(cooler.get_status)
    assert result == _H110I_GT_BASELINE["STATUS"]
    result = capture(lambda: cooler.set_fixed_speed("fan1", 42))
    assert result == _H110I_GT_BASELINE["FIXED1"]
    result = capture(lambda: cooler.set_fixed_speed("fan2", 77))
    assert result == _H110I_GT_BASELINE["FIXED2"]
    result = capture(lambda: cooler.set_speed_profile("fan1", [(20, 30), (40, 90)]))
    assert result == _H110I_GT_BASELINE["PROFILE1"]
    result = capture(lambda: cooler.set_speed_profile("fan2", [(20, 30), (40, 90)]))
    assert result == _H110I_GT_BASELINE["PROFILE2"]
