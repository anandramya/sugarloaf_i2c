# STATUS_WORD Decoder

## Overview

The PMBus tools now include automatic STATUS_WORD decoding to provide human-readable fault and warning information.

## STATUS_WORD Bit Definitions

| Bit | Name | Description |
|-----|------|-------------|
| 15 | VOUT | VOUT fault/warning - Set when output over-voltage or under-voltage protection occurs |
| 14 | IOUT | IOUT fault/warning - Set when output current fault or output power warning occurs |
| 13 | INPUT | Input voltage/current fault/warning - Set when input voltage or current protection occurs |
| 12 | MFR_SPECIFIC | Manufacturer specific fault - Asserted when STATUS_MFR_SPECIFIC has faults |
| 11 | POWER_GOOD_N | Power Good not active - Set when PG signal is not active |
| 10 | RESERVED | Reserved |
| 9 | RESERVED | Reserved |
| 8 | WATCH_DOG_OVF | Watchdog timer overflow - Set when monitor block watchdog timer overflows |
| 7 | NVM_BUSY | NVM busy - Live status indicating NVM write/read operations unavailable |
| 6 | OFF | Output is off - Live status indicating VOUT is off (due to protection, EN low, or VID=0) |
| 5 | VOUT_OV_FAULT | VOUT overvoltage fault - Set when OVP happens (absolute or VID-based) |
| 4 | IOUT_OC_FAULT | IOUT overcurrent fault - Set when OCP happens (warning or fault level) |
| 3 | VIN_UV_FAULT | VIN undervoltage fault - Set when input voltage UV fault happens |
| 2 | TEMPERATURE | Over-temperature fault/warning - Set when TSENS1/2 detects OT protection or warning |
| 1 | CML | Communication fault - Set when PMBus communication fault occurs |
| 0 | OTHER_FAULT | Other fault - Set if any fault in this register occurred |

**Note**: Most bits are latched and require CLEAR_FAULTS (0x03) command to reset. Bits 7 (NVM_BUSY) and 6 (OFF) are live status bits.

## Usage

### Command Line Interface

#### Basic STATUS_WORD Read (Detailed View)
```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
```

**Output:**
```
STATUS_WORD: 0x0002
  ⚠ Active faults/warnings:
    [✓] VOUT             : OK    - VOUT fault/warning
    [✓] IOUT             : OK    - IOUT fault/warning
    [✓] INPUT            : OK    - Input voltage/current fault/warning
    [✓] MFR_SPECIFIC     : OK    - Manufacturer specific fault
    [✓] POWER_GOOD_N     : OK    - Power Good not active
    [✓] WATCH_DOG_OVF    : OK    - Watchdog timer overflow
    [✓] NVM_BUSY         : OK    - NVM busy
    [✓] OFF              : OK    - Output is off
    [✓] VOUT_OV_FAULT    : OK    - VOUT overvoltage fault
    [✓] IOUT_OC_FAULT    : OK    - IOUT overcurrent fault
    [✓] VIN_UV_FAULT     : OK    - VIN undervoltage fault
    [✓] TEMPERATURE      : OK    - Over-temperature fault/warning
    [✗] CML              : FAULT - Communication fault
    [✓] OTHER_FAULT      : OK    - Other fault
```

#### Test Mode (Compact View)
```bash
./powertool_pcie.py --test
```

**Output:**
```
TSP_CORE (Page 0):
------------------------------------------------------------
  VOUT:        0.7295 V
  IOUT:        38.00 A
  TEMP:        44.0 °C
  STATUS_WORD: 0x0002
    Active: CML
```

### Python API

#### Decode STATUS_WORD
```python
from pmbus_common import decode_status_word

status = 0x8042  # VOUT fault + OFF + CML

decoded = decode_status_word(status)
print(f"Raw value: 0x{decoded['raw_value']:04X}")

for bit_name, bit_info in decoded['bits'].items():
    if bit_info['active']:
        print(f"{bit_name}: {bit_info['description']}")
```

**Output:**
```
Raw value: 0x8042
VOUT: VOUT fault/warning
OFF: Output is off
CML: Communication fault
```

#### Format STATUS_WORD (Human Readable)
```python
from pmbus_common import format_status_word

# Show only active faults
print(format_status_word(0x8042, show_all=False))

# Show all bits
print(format_status_word(0x8042, show_all=True))
```

## Example Scenarios

### Scenario 1: No Faults (0x0000)
```
STATUS_WORD: 0x0000
  ✓ No faults detected
```

### Scenario 2: CML Fault Only (0x0002)
Common during normal operation. CML bit may be set during certain PMBus transactions.
```
STATUS_WORD: 0x0002
  ⚠ Active faults/warnings:
    [✗] CML              : FAULT - Communication fault
```

### Scenario 3: Overvoltage Fault (0x8020)
VOUT fault indicator and specific VOUT_OV_FAULT are both set.
```
STATUS_WORD: 0x8020
  ⚠ Active faults/warnings:
    [✗] VOUT             : FAULT - VOUT fault/warning
    [✗] VOUT_OV_FAULT    : FAULT - VOUT overvoltage fault
```

### Scenario 4: Multiple Faults (0xC034)
Complex fault scenario with multiple protection events.
```
STATUS_WORD: 0xC034
  ⚠ Active faults/warnings:
    [✗] VOUT             : FAULT - VOUT fault/warning
    [✗] IOUT             : FAULT - IOUT fault/warning
    [✗] VOUT_OV_FAULT    : FAULT - VOUT overvoltage fault
    [✗] IOUT_OC_FAULT    : FAULT - IOUT overcurrent fault
    [✗] TEMPERATURE      : FAULT - Over-temperature fault/warning
```

### Scenario 5: Output Off (0x0040)
Device is disabled (EN pin low, VID=0, or protection shutdown).
```
STATUS_WORD: 0x0040
  ⚠ Active faults/warnings:
    [✗] OFF              : FAULT - Output is off
```

### Scenario 6: Power Good Not Active (0x0800)
Power good signal indicates output not in regulation.
```
STATUS_WORD: 0x0800
  ⚠ Active faults/warnings:
    [✗] POWER_GOOD_N     : FAULT - Power Good not active
```

## Clearing Faults

To clear latched faults, send the CLEAR_FAULTS command:

```bash
# Using direct register write (command 0x03)
./powertool_pcie.py --rail TSP_CORE --cmd WRITE 0x03 0x00 1
```

**Note**: Live status bits (NVM_BUSY, OFF) cannot be cleared and reflect real-time hardware state.

## Integration with pmbus_common.py

The STATUS_WORD decoder is part of the shared `pmbus_common.py` library, ensuring consistent behavior across both serial and PCIe implementations.

**Functions provided:**
- `decode_status_word(status_word)` - Returns dictionary with all bit information
- `format_status_word(status_word, show_all=False)` - Returns formatted string

Both tools (powertool.py and powertool_pcie.py) automatically use these decoders when displaying STATUS_WORD.

## Testing

Test the decoder with various values:
```bash
python3 /tmp/test_status_decoder.py
```

This will show the decoder output for:
- No faults (0x0000)
- Single faults
- Multiple faults
- Complex scenarios

## References

- PMBus Specification Part II (Command Language)
- MP29816-C Datasheet - STATUS_WORD register definition
- PMBUS_TEST_RESULTS.md - Real device STATUS_WORD readings
