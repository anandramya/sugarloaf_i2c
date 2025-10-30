# STATUS Register Decoders

## Overview

The PMBus tools include comprehensive decoders for all major STATUS registers:
- **STATUS_WORD** (0x79) - 16-bit comprehensive status
- **STATUS_VOUT** (0x7A) - 8-bit output voltage status
- **STATUS_IOUT** (0x7B) - 8-bit output current status

## STATUS_WORD Decoder (0x79)

### Bit Definitions

| Bit | Name | Type | Description |
|-----|------|------|-------------|
| 15 | VOUT | Latched | VOUT fault/warning indicator |
| 14 | IOUT | Latched | IOUT fault/warning indicator |
| 13 | INPUT | Latched | Input voltage/current fault/warning |
| 12 | MFR_SPECIFIC | Latched | Manufacturer specific fault |
| 11 | POWER_GOOD_N | Latched | Power Good not active |
| 10 | RESERVED | - | Reserved |
| 9 | RESERVED | - | Reserved |
| 8 | WATCH_DOG_OVF | Latched | Watchdog timer overflow |
| 7 | NVM_BUSY | Live | NVM busy (live status) |
| 6 | OFF | Live | Output is off (live status) |
| 5 | VOUT_OV_FAULT | Latched | VOUT overvoltage fault |
| 4 | IOUT_OC_FAULT | Latched | IOUT overcurrent fault |
| 3 | VIN_UV_FAULT | Latched | VIN undervoltage fault |
| 2 | TEMPERATURE | Latched | Over-temperature fault/warning |
| 1 | CML | Latched | PMBus communication fault |
| 0 | OTHER_FAULT | Latched | Any other fault occurred |

### Usage

```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
```

**Output:**
```
STATUS_WORD: 0x0002
  ⚠ Active faults/warnings:
    [✗] CML              : FAULT - Communication fault
```

## STATUS_VOUT Decoder (0x7A)

### Bit Definitions

| Bit | Name | Type | Description |
|-----|------|------|-------------|
| 7-2 | RESERVED | - | Reserved (always 0) |
| 1 | LINE_FLOAT | Latched | Line float protection fault |
| 0 | VOUT_SHORT | Latched | VOUT short fault |

### Details

**LINE_FLOAT (Bit 1):**
- Set when line float fault is detected
- Device shuts down associated rail when triggered
- Latched mode - requires CLEAR_FAULTS (0x03) to reset

**VOUT_SHORT (Bit 0):**
- Set when VOUT short circuit is detected
- Latched mode - requires CLEAR_FAULTS (0x03) to reset

### Usage

```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_VOUT
```

**Output (No faults):**
```
STATUS_VOUT: 0x00
  ✓ No VOUT faults detected
```

**Output (With faults):**
```
STATUS_VOUT: 0x03
  ⚠ Active VOUT faults:
    [✗] LINE_FLOAT       : FAULT - Line float protection fault
    [✗] VOUT_SHORT       : FAULT - VOUT short fault
```

## STATUS_IOUT Decoder (0x7B)

### Bit Definitions

| Bit | Name | Type | Description |
|-----|------|------|-------------|
| 7 | IOUT_OC_FAULT | Latched | Output overcurrent fault |
| 6 | OCP_UV_FAULT | Latched | Overcurrent and undervoltage dual fault |
| 5 | IOUT_OC_WARN | Latched | Output overcurrent warning |
| 4-0 | RESERVED | - | Reserved |

### Details

**IOUT_OC_FAULT (Bit 7):**
- Set when output overcurrent protection triggers
- Latched mode - requires CLEAR_FAULTS (0x03) to reset
- 0 = No overcurrent fault
- 1 = Overcurrent fault occurred

**OCP_UV_FAULT (Bit 6):**
- Set when both overcurrent AND undervoltage occur simultaneously
- Dual fault condition
- Latched mode - requires CLEAR_FAULTS (0x03) to reset
- 0 = No dual fault
- 1 = OCP + UV fault occurred

**IOUT_OC_WARN (Bit 5):**
- Set when output current exceeds warning threshold
- Warning level (not a fault)
- Latched mode - requires CLEAR_FAULTS (0x03) to reset
- 0 = No overcurrent warning
- 1 = Overcurrent warning occurred

### Usage

```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_IOUT
```

**Output (No faults):**
```
STATUS_IOUT: 0x00
  ✓ No IOUT faults detected
```

**Output (With warning only):**
```
STATUS_IOUT: 0x20
  ⚠ Active IOUT faults/warnings:
    [✗] IOUT_OC_WARN     : WARN  - Output overcurrent warning
```

**Output (With multiple faults):**
```
STATUS_IOUT: 0xE0
  ⚠ Active IOUT faults/warnings:
    [✗] IOUT_OC_FAULT    : FAULT - Output overcurrent fault
    [✗] OCP_UV_FAULT     : FAULT - Overcurrent and undervoltage dual fault
    [✗] IOUT_OC_WARN     : WARN  - Output overcurrent warning
```

## Python API

### Import Functions

```python
from pmbus_common import (
    decode_status_word, format_status_word,
    decode_status_vout, format_status_vout,
    decode_status_iout, format_status_iout
)
```

### Decode STATUS_WORD

```python
status = 0x8020  # VOUT fault + VOUT_OV_FAULT

# Get detailed dictionary
decoded = decode_status_word(status)
for bit_name, bit_info in decoded['bits'].items():
    if bit_info['active']:
        print(f"{bit_name}: {bit_info['description']}")

# Get formatted string
print(format_status_word(status, show_all=False))  # Only active faults
print(format_status_word(status, show_all=True))   # All bits
```

### Decode STATUS_VOUT

```python
status_vout = 0x02  # Line float fault

# Get detailed dictionary
decoded = decode_status_vout(status_vout)
for bit_name, bit_info in decoded['bits'].items():
    if bit_info['active']:
        print(f"{bit_name}: {bit_info['description']}")

# Get formatted string
print(format_status_vout(status_vout, show_all=False))
```

### Decode STATUS_IOUT

```python
status_iout = 0xA0  # OC fault + warning

# Get detailed dictionary
decoded = decode_status_iout(status_iout)
for bit_name, bit_info in decoded['bits'].items():
    if bit_info['active']:
        print(f"{bit_name}: {bit_info['description']}")

# Get formatted string
print(format_status_iout(status_iout, show_all=False))
```

## Clearing Faults

Most status bits are latched and require the CLEAR_FAULTS command to reset:

```bash
# Clear all faults (both rails)
./powertool_pcie.py --rail TSP_CORE --cmd WRITE 0x03 0x00 1
./powertool_pcie.py --rail TSP_C2C --cmd WRITE 0x03 0x00 1
```

**Note:** Live status bits (NVM_BUSY, OFF) cannot be cleared and reflect real-time hardware state.

## Current Device Status

### TSP_CORE (Page 0)
- **STATUS_WORD**: 0x0002 (CML fault only - normal during PMBus operations)
- **STATUS_VOUT**: 0x00 (No VOUT faults)
- **STATUS_IOUT**: 0x00 (No IOUT faults)

### TSP_C2C (Page 1)
- **STATUS_WORD**: 0x0002 (CML fault only - normal during PMBus operations)
- **STATUS_VOUT**: 0x00 (No VOUT faults)
- **STATUS_IOUT**: 0x00 (No IOUT faults)

## Test Examples

### Example 1: No Faults
```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_VOUT
```
```
STATUS_VOUT: 0x00
  ✓ No VOUT faults detected
```

### Example 2: VOUT Short Fault
```
STATUS_VOUT: 0x01
  ⚠ Active VOUT faults:
    [✗] VOUT_SHORT       : FAULT - VOUT short fault
```

### Example 3: IOUT Warning Only
```
STATUS_IOUT: 0x20
  ⚠ Active IOUT faults/warnings:
    [✗] IOUT_OC_WARN     : WARN  - Output overcurrent warning
```

### Example 4: Multiple IOUT Faults
```
STATUS_IOUT: 0xC0
  ⚠ Active IOUT faults/warnings:
    [✗] IOUT_OC_FAULT    : FAULT - Output overcurrent fault
    [✗] OCP_UV_FAULT     : FAULT - Overcurrent and undervoltage dual fault
```

## Fault Interpretation Guide

### STATUS_VOUT Faults

**VOUT_SHORT (0x01):**
- **Cause**: Output voltage shorted to ground
- **Action**: Check load connections, inspect for shorts
- **Recovery**: Clear fault after removing short

**LINE_FLOAT (0x02):**
- **Cause**: Output line floating (disconnected load)
- **Action**: Check load connections, verify wiring
- **Recovery**: Clear fault after fixing connection

### STATUS_IOUT Faults

**IOUT_OC_WARN (0x20):**
- **Cause**: Output current exceeds warning threshold
- **Action**: Check load current, verify within specifications
- **Severity**: Warning - device still operating

**IOUT_OC_FAULT (0x80):**
- **Cause**: Output current exceeds fault threshold
- **Action**: Reduce load current, check for shorts
- **Severity**: Fault - device may shut down

**OCP_UV_FAULT (0x40):**
- **Cause**: Overcurrent occurred while output voltage is low
- **Action**: Check for output short, verify load
- **Severity**: Critical - indicates short circuit condition

## Integration with Tools

All decoders are:
- ✅ Integrated into `pmbus_common.py` shared library
- ✅ Available in both `powertool_pcie.py` and (future) `powertool.py`
- ✅ Automatically used when reading STATUS registers
- ✅ Fully tested with multiple fault scenarios

## References

- PMBus Specification Part II (Command Language)
- MP29816-C Datasheet - STATUS register definitions
- STATUS_WORD_DECODER.md - Detailed STATUS_WORD documentation
