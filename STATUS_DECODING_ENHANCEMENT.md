# STATUS Register Decoding Enhancement

## Overview
Enhanced `powertool_pcie.py` to automatically decode STATUS registers (STATUS_WORD, STATUS_VOUT, STATUS_IOUT) in all command formats, making fault diagnosis faster and easier.

## Changes Made

### 1. STATUS_WORD Decoding in Simple Format
**Before:**
```bash
$ ./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
STATUS:   0x0002
```

**After:**
```bash
$ ./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
STATUS:   0x0002
  Active faults: CML
```

### 2. Added STATUS_VOUT and STATUS_IOUT Support
**New capability in simple format:**
```bash
$ ./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD STATUS_VOUT STATUS_IOUT
TSP_CORE (Page 0):
------------------------------------------------------------
  STATUS:   0x0002
    Active faults: CML
  STATUS_VOUT: 0x00
  STATUS_IOUT: 0x00
```

### 3. Multi-Command Support with Status Decoding
**Comprehensive telemetry + status read:**
```bash
$ ./powertool_pcie.py 0x5C TSP_CORE VOUT IOUT TEMP DIE_TEMP STATUS_WORD
TSP_CORE (Page 0):
------------------------------------------------------------
  VOUT:     0.7305 V
  IOUT:     38.00 A
  TEMP:     45.0 °C
  DIE_TEMP: 37.9 °C
  STATUS:   0x0002
    Active faults: CML
```

## Implementation Details

### Code Changes

**File:** `powertool_pcie.py`

**Location 1:** Command normalization (lines 347-350)
```python
elif cmd == 'STATUS_VOUT':
    normalized_commands.append('STATUS_VOUT')
elif cmd == 'STATUS_IOUT':
    normalized_commands.append('STATUS_IOUT')
```

**Location 2:** Single read mode with decoding (lines 541-567)
```python
elif cmd == 'STATUS_WORD':
    status = pt.Read_Status_Word(page)
    print(f"  STATUS:   0x{status:04X}")
    # Decode and show status bits
    decoded = decode_status_word(status)
    active_faults = [name for name, info in decoded['bits'].items()
                    if info['active'] and name not in ['RESERVED_9', 'RESERVED_10']]
    if active_faults:
        print(f"    Active faults: {', '.join(active_faults)}")

elif cmd == 'STATUS_VOUT':
    status_vout = pt.i2c_read8PMBus(page, PMBusDict["STATUS_VOUT"])
    print(f"  STATUS_VOUT: 0x{status_vout:02X}")
    # Decode and show active bits
    decoded = decode_status_vout(status_vout)
    active_faults = [name for name, info in decoded['bits'].items()
                    if info['active'] and name != 'RESERVED_0']
    if active_faults:
        print(f"    Active faults: {', '.join(active_faults)}")

elif cmd == 'STATUS_IOUT':
    status_iout = pt.i2c_read8PMBus(page, PMBusDict["STATUS_IOUT"])
    print(f"  STATUS_IOUT: 0x{status_iout:02X}")
    # Decode and show active bits
    decoded = decode_status_iout(status_iout)
    active_faults = [name for name, info in decoded['bits'].items()
                    if info['active'] and name != 'RESERVED_0']
    if active_faults:
        print(f"    Active faults: {', '.join(active_faults)}")
```

### Decoding Functions Used

From `pmbus_common.py`:
- `decode_status_word()` - Decodes 16-bit STATUS_WORD register
- `decode_status_vout()` - Decodes 8-bit STATUS_VOUT register
- `decode_status_iout()` - Decodes 8-bit STATUS_IOUT register
- `format_status_word()` - Full detailed formatting (used in named format)
- `format_status_vout()` - Full detailed formatting (used in named format)
- `format_status_iout()` - Full detailed formatting (used in named format)

## Features

### Intelligent Display
- **Only shows faults when present**: "Active faults" line only appears if faults exist
- **Skips reserved bits**: Reserved bits are filtered out from the compact display
- **Compact format**: Simple comma-separated list of fault names

### Two Output Styles

**Simple Format (Compact):**
- Hex value + comma-separated list of active faults
- Perfect for quick diagnostics and scripts
- Example: `Active faults: CML, VOUT_OV_FAULT`

**Named Format (Detailed):**
- Hex value + full bit-by-bit breakdown
- Shows all bits with ✓/✗ indicators
- Includes descriptions for each bit
- Example:
  ```
  STATUS_WORD: 0x0002
    ⚠ Active faults/warnings:
      [✓] VOUT             : OK    - VOUT fault/warning
      [✗] CML              : FAULT - Communication fault
      [✓] OTHER_FAULT      : OK    - Other fault
  ```

### Backward Compatible
- Named argument format (`--rail --cmd`) unchanged
- Logging mode still stores raw hex values in CSV
- All existing functionality preserved

## Usage Examples

### Quick Fault Check
```bash
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
```

### Comprehensive Status Check
```bash
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD STATUS_VOUT STATUS_IOUT
```

### Both Rails Status
```bash
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
./powertool_pcie.py 0x5C TSP_C2C STATUS_WORD
```

### Telemetry + Status in One Command
```bash
./powertool_pcie.py 0x5C TSP_CORE VOUT IOUT TEMP STATUS_WORD
```

### Detailed Decoding (Named Format)
```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_VOUT
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_IOUT
```

## Benefits

1. **Faster Diagnostics**: No need to manually decode hex values
2. **Reduced Errors**: Automatic bit decoding eliminates manual lookup
3. **Better UX**: Human-readable fault names at a glance
4. **Flexibility**: Choose compact or detailed output based on needs
5. **Consistency**: Same decoding logic across both command formats

## Status Bit Definitions

### STATUS_WORD (0x79) - 16 bits
Common faults decoded:
- **VOUT** - Output voltage fault/warning
- **IOUT** - Output current fault/warning
- **INPUT** - Input voltage/current fault/warning
- **TEMPERATURE** - Temperature fault/warning
- **CML** - Communication fault
- **POWER_GOOD_N** - Power good not active
- **VOUT_OV_FAULT** - Output overvoltage fault
- **IOUT_OC_FAULT** - Output overcurrent fault
- **VIN_UV_FAULT** - Input undervoltage fault
- **OFF** - Output is off
- **NVM_BUSY** - Non-volatile memory busy

### STATUS_VOUT (0x7A) - 8 bits
VOUT-specific faults:
- **VOUT_OV_FAULT** - Output overvoltage fault
- **VOUT_OV_WARN** - Output overvoltage warning
- **VOUT_UV_WARN** - Output undervoltage warning
- **VOUT_UV_FAULT** - Output undervoltage fault
- **VOUT_SHORT** - Output short circuit
- **LINE_FLOAT** - Line floating

### STATUS_IOUT (0x7B) - 8 bits
IOUT-specific faults:
- **IOUT_OC_FAULT** - Output overcurrent fault
- **IOUT_OC_LV_FAULT** - Overcurrent and low voltage fault
- **IOUT_OC_WARN** - Output overcurrent warning
- **IOUT_UC_FAULT** - Output undercurrent fault
- **OCP_UV_FAULT** - OCP triggered by undervoltage

## Testing

All status commands tested with both rails:
```bash
✓ STATUS_WORD decoding - TSP_CORE
✓ STATUS_WORD decoding - TSP_C2C
✓ STATUS_VOUT decoding - TSP_CORE
✓ STATUS_VOUT decoding - TSP_C2C
✓ STATUS_IOUT decoding - TSP_CORE
✓ STATUS_IOUT decoding - TSP_C2C
✓ Multi-command with status
✓ Named format (detailed decoding)
✓ Simple format (compact decoding)
```

## Documentation Updates

Updated files:
- `PMBUS_COMMAND_REFERENCE.md` - Added status decoding section with examples
- `STATUS_DECODING_ENHANCEMENT.md` - This document

## Summary

The STATUS register commands now provide immediate, human-readable fault information in both simple and detailed formats. This enhancement significantly improves the user experience for PMBus diagnostics without sacrificing any existing functionality.

**Before:** Had to manually decode hex values using datasheets
**After:** Fault names displayed automatically in plain English
