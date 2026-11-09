# Corsair CoolIT USB HID coolers
_Driver API and source code available in [`liquidctl.driver.coolit`](../liquidctl/driver/coolit.py)._

This driver supports the following devices, which share the USB ID
`1b1c:0c04` and are told apart by a device ID that the driver reads at probe
time:

- Corsair Commander Mini (fan and temperature controller)
- Corsair Hydro H110i GT AIO liquid cooler

## Initialization
[Initialization]: #initialization

### Corsair Commander Mini

The controller does not need to be initialized prior to use.

```
# liquidctl initialize
Corsair Commander Mini
└── Firmware version    1.1.6
```

### Corsair Hydro H110i GT

The AIO does not need to be initialized prior to use, but it will set the pump
mode to `quiet`.

```
# liquidctl initialize
Corsair Hydro H110i GT
└── Firmware version    2.0.0
```

When (re)initializing the device, it is possible to select the pump mode:

```
# liquidctl initialize --pump-mode extreme
Corsair Hydro H110i GT
└── Firmware version    2.0.0
```

Allowed pump modes are:
- `quiet`
- `extreme`

## Device monitoring

### Corsair Commander Mini

The controller reports the temperature of up to four external temperature
sensors and the speed of up to six fans.

```
# liquidctl status
Corsair Commander Mini
├── Temperature 1     25.0  °C
├── Temperature 2     25.5  °C
├── Temperature 3     30.0  °C
├── Temperature 4     35.3  °C
├── Fan 1 speed       1000  rpm
├── Fan 2 speed       1100  rpm
├── Fan 3 speed       1200  rpm
├── Fan 4 speed       1300  rpm
├── Fan 5 speed       1400  rpm
└── Fan 6 speed       1500  rpm
```

_Note: the controller does not report whether an external temperature sensor
is connected; unconnected inputs may report implausible values._

### Corsair Hydro H110i GT

Similarly to other AIOs, the cooler can report fan and pump speeds as well as
the liquid temperature.

```
# liquidctl status
Corsair Hydro H110i GT
├── Liquid temperature    32.6  °C
├── Fan 1 speed           1130  rpm
├── Fan 2 speed           1130  rpm
└── Pump speed            2831  rpm
```

## Fan speed control

Fan speeds can be configured either to fixed duty values or profiles. The
profiles accept up to seven (temperature, duty) points, and are interpolated by
the device.

```
# liquidctl set fan speed 50
# liquidctl set fan speed 20 0 40 100
```

The Commander Mini exposes six fan channels (`fan1` to `fan6`), while the
H110i GT exposes two (`fan1` and `fan2`).

## Lighting

Not supported by this driver.
