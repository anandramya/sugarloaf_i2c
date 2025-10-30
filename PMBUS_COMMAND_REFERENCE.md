# PMBus Command Reference - MP29816-C

## Complete Command List

### Standard PMBus Commands (Built-in)

| Address | Command Name | Type | Description |
|---------|-------------|------|-------------|
| 0x00 | PAGE | R/W | Select rail (0=TSP_CORE, 1=TSP_C2C) |
| 0x01 | OPERATION | R/W | Operation mode control |
| 0x03 | CLEAR_FAULTS | W | Clear all fault registers |
| 0x20 | VOUT_MODE | R | Voltage output mode (Linear16 exponent) |
| 0x21 | VOUT_COMMAND | R/W | Voltage setpoint command |
| 0x23 | VOUT_OFFSET | R/W | Voltage offset adjustment |
| 0x28 | VOUT_DROOP | R/W | Voltage droop configuration |
| 0x33 | FREQUENCY_SWITCH | R/W | Switching frequency |
| 0x46 | IOUT_OC_FAULT_LIMIT | R/W* | Overcurrent fault threshold |
| 0x4A | IOUT_OC_WARN_LIMIT | R/W* | Overcurrent warning threshold |

*Note: OC limit registers may not support runtime writes (see notes below)

### Telemetry Commands (Read-Only)

| Address | Command Name | Format | Description |
|---------|-------------|--------|-------------|
| 0x89 | READ_IIN | Linear11 | Input current |
| 0x8B | READ_VOUT | Linear16 | Output voltage |
| 0x8C | READ_IOUT | Linear11 | Output current |
| 0x8D | READ_TEMP | Linear11 | Temperature (external sensor) |
| 0x8E | READ_DIE_TEMP | Voltage-based | Die temperature |
| 0x94 | READ_DUTY | Linear11 | PWM duty cycle |
| 0x96 | READ_POUT | Linear11 | Output power |
| 0x97 | READ_PIN | Linear11 | Input power |

### Status Registers (Read-Only)

| Address | Command Name | Bits | Description |
|---------|-------------|------|-------------|
| 0x78 | STATUS_BYTE | 8-bit | Summary status byte |
| 0x79 | STATUS_WORD | 16-bit | Comprehensive status word |
| 0x7A | STATUS_VOUT | 8-bit | Output voltage status |
| 0x7B | STATUS_IOUT | 8-bit | Output current status |
| 0x7C | STATUS_INPUT | 8-bit | Input voltage/current status |
| 0x7D | STATUS_TEMPERATURE | 8-bit | Temperature status |
| 0x7E | STATUS_CML | 8-bit | Communication status |
| 0x80 | STATUS_MFR_SPECIFIC | 8-bit | Manufacturer-specific status |

### Manufacturer-Specific Commands

| Address | Command Name | Type | Description |
|---------|-------------|------|-------------|
| 0x29 | MFR_VID_RES_R1 | R/W | VID resolution settings |
| 0x67 | MFR_VR_CONFIG | R/W | VR configuration |
| 0xD1 | MFR_TEMP_PEAK | R | Peak temperature reading |
| 0xD7 | MFR_IOUT_PEAK | R | Peak output current |
| 0xD8 | MFR_REG_ACCESS | R/W | Extended register access (for phase currents) |

### Phase Current Registers (via 0xD8)

| Address | Command Name | Description |
|---------|-------------|-------------|
| 0x0C00 | PHASE1_Current | Phase 1 current |
| 0x0C01 | PHASE2_Current | Phase 2 current |
| 0x0C02 | PHASE3_Current | Phase 3 current |
| 0x0C03 | PHASE4_Current | Phase 4 current |
| 0x0C04 | PHASE5_Current | Phase 5 current |
| 0x0C05 | PHASE6_Current | Phase 6 current |
| 0x0C06 | PHASE7_Current | Phase 7 current |
| 0x0C07 | PHASE8_Current | Phase 8 current |
| 0x0C08 | PHASE9_Current | Phase 9 current |
| 0x0C09 | PHASE10_Current | Phase 10 current |
| 0x0C0A | PHASE11_Current | Phase 11 current |
| 0x0C0B | PHASE12_Current | Phase 12 current |
| 0x0C0C | PHASE13_Current | Phase 13 current |
| 0x0C0D | PHASE14_Current | Phase 14 current |
| 0x0C0E | PHASE15_Current | Phase 15 current |
| 0x0C0F | PHASE16_Current | Phase 16 current |

---

## PowerTool PCIe CLI Commands

### Implemented High-Level Commands

These commands are supported via `--rail` and `--cmd` or simple positional format:

**Telemetry (Read):**
- `READ_VOUT` - Output voltage
- `READ_IOUT` - Output current
- `READ_TEMP` - External temperature
- `READ_DIE_TEMP` - Die temperature
- `STATUS_WORD` (alias: `READ_STATUS`) - Status word **with automatic fault decoding**
- `STATUS_VOUT` - Output voltage status **with automatic fault decoding**
- `STATUS_IOUT` - Output current status **with automatic fault decoding**

**Configuration (Read/Write):**
- `VOUT_COMMAND` - Set voltage (requires `--value`)
- `IOUT_OC_WARN_LIMIT` - Read/write overcurrent warning limit*
- `IOUT_OC_FAULT_LIMIT` - Read/write overcurrent fault limit*
- `CLEAR_FAULTS` (alias: `CLEAR`) - Clear all fault status registers

**Direct Register Access:**
- `REG_READ` - Read any register (requires `--reg-addr`, `--bytes`)
- `REG_WRITE` - Write any register (requires `--reg-addr`, `--value`, `--bytes`)

**Test Mode:**
- `--test` - Read all telemetry from both rails

### Command Aliases (Simple Format Only)

When using positional arguments, these aliases are available:
- `VOUT` → `READ_VOUT`
- `IOUT` → `READ_IOUT`
- `TEMP` → `READ_TEMP`
- `DIE_TEMP` → `READ_DIE_TEMP`
- `STATUS` or `WORD` → `STATUS_WORD`
- `CLEAR` → `CLEAR_FAULTS`

### Status Register Decoding

All status register commands (`STATUS_WORD`, `STATUS_VOUT`, `STATUS_IOUT`) now include **automatic fault decoding** in both command formats:

**Simple Format** - Shows hex value + compact list of active faults:
```bash
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
# Output:
#   STATUS:   0x0002
#     Active faults: CML
```

**Named Format** - Shows hex value + detailed bit-by-bit decoding:
```bash
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD
# Output:
#   STATUS_WORD: 0x0002
#     ⚠ Active faults/warnings:
#       [✓] VOUT             : OK    - VOUT fault/warning
#       [✗] CML              : FAULT - Communication fault
#       ...
```

**Features:**
- Only shows "Active faults" line when faults are present
- Skips reserved bits in the output
- Works in both single-read and multi-command modes
- CSV logging stores raw hex values for post-processing

---

## Usage Examples

### Simple Format (Recommended)
```bash
# Single telemetry read
./powertool_pcie.py 0x5C TSP_CORE VOUT
./powertool_pcie.py 0x5C TSP_C2C IOUT TEMP

# Multiple telemetry reads
./powertool_pcie.py 0x5C TSP_CORE VOUT IOUT TEMP DIE_TEMP STATUS_WORD

# Read all status registers with decoding
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD STATUS_VOUT STATUS_IOUT

# Clear faults
./powertool_pcie.py 0x5C TSP_CORE CLEAR_FAULTS
./powertool_pcie.py 0x5C TSP_CORE CLEAR  # Alias

# Clear faults and check status in one command
./powertool_pcie.py 0x5C TSP_CORE CLEAR_FAULTS STATUS_WORD

# Logging mode
./powertool_pcie.py 0x5C TSP_CORE VOUT IOUT log --samples 100
```

### Named Argument Format
```bash
# Read commands
./powertool_pcie.py --rail TSP_CORE --cmd READ_VOUT
./powertool_pcie.py --rail TSP_C2C --cmd READ_IOUT
./powertool_pcie.py --rail TSP_CORE --cmd STATUS_WORD

# Write voltage
./powertool_pcie.py --rail TSP_CORE --cmd VOUT_COMMAND --value 0.8

# Read/write OC limits
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 720

# Clear faults
./powertool_pcie.py --rail TSP_CORE --cmd CLEAR_FAULTS
./powertool_pcie.py --rail TSP_C2C --cmd CLEAR_FAULTS

# Direct register access
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x8B --bytes 2
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0x21 --value 3200 --bytes 2
```

### Test Mode
```bash
./powertool_pcie.py --test
```

---

## Data Format Reference

### Linear11 Format
Used for: IOUT, TEMP, power readings
- 16-bit value: [15:11] = 5-bit exponent, [10:0] = 11-bit mantissa
- Formula: `value = mantissa × 2^exponent`
- Both exponent and mantissa are two's complement signed

### Linear16 Format
Used for: VOUT readings
- 16-bit mantissa with exponent from VOUT_MODE register
- Formula: `voltage = mantissa × 2^exponent`
- Exponent: 5-bit two's complement from VOUT_MODE[4:0]
- Mantissa: 16-bit two's complement

### Voltage-Based Temperature
Used for: READ_DIE_TEMP (0x8E)
- Direct conversion: 1°C per LSB
- No scaling required

### Unsigned Binary
Used for: IOUT_OC_FAULT_LIMIT, IOUT_OC_WARN_LIMIT
- Bits [15:8]: Reserved (0x00)
- Bits [7:0]: Limit value
- Scaling: `Current(A) = value × (8 × IOUT_SCALE)`
- IOUT_SCALE read from MFR_VID_RES_R1[12:10]

---

## Important Notes

### Overcurrent Limit Writes
**⚠️ WARNING**: The MP29816-C does **not support runtime writes** to IOUT_OC_WARN_LIMIT and IOUT_OC_FAULT_LIMIT registers.

**Observed behavior:**
- Writes appear to succeed but don't persist
- Register reads back as 0x0000 after write
- STATUS_CML shows communication fault (0xAA)
- Attempting writes may clear existing values to 0A

**Possible reasons:**
1. Limits are factory-programmed in NVM (read-only)
2. Requires manufacturer-specific unlock sequence
3. Only modifiable during manufacturing with special tools
4. Protected for safety (prevents accidental misconfiguration)

**To restore default values:**
- Power cycle the device
- Default TSP_CORE: WARN=720A, FAULT=1104A
- Default TSP_C2C: WARN=120A, FAULT=152A

### CLEAR_FAULTS Command Behavior

**Command:** CLEAR_FAULTS (0x03)
**Type:** Send-byte (no data byte)
**Effect:** Clears all fault bits in status registers

**Clears these registers:**
- STATUS_BYTE (0x78)
- STATUS_WORD (0x79)
- STATUS_VOUT (0x7A)
- STATUS_IOUT (0x7B)
- STATUS_INPUT (0x7C)
- STATUS_TEMPERATURE (0x7D)
- STATUS_CML (0x7E)
- STATUS_MFR_SPECIFIC (0x80)

**Important:**
- Clears **latched fault bits**, not the underlying fault conditions
- If fault condition persists, fault bits will **immediately re-assert**
- Use to clear historical faults after fixing the underlying issue
- Check status registers after clearing to verify faults don't re-appear

**Example workflow:**
```bash
# Check for faults
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
# Output: STATUS: 0x0002, Active faults: CML

# Clear faults
./powertool_pcie.py 0x5C TSP_CORE CLEAR_FAULTS
# Output: ✓ Cleared all faults for page 0

# Verify faults cleared (or check if they re-assert)
./powertool_pcie.py 0x5C TSP_CORE STATUS_WORD
# If fault condition fixed: STATUS: 0x0000 (no faults)
# If fault persists: STATUS: 0x0002 (fault re-asserted)
```

### Standard PMBus NVM Commands (Not Tested)
These may or may not be supported by the MP29816-C:
- 0x11 STORE_DEFAULT_ALL
- 0x12 RESTORE_DEFAULT_ALL (tested - returns MCU error 0x00000204)
- 0x13 STORE_DEFAULT_CODE
- 0x14 RESTORE_DEFAULT_CODE
- 0x15 STORE_USER_ALL
- 0x16 RESTORE_USER_ALL

---

## Summary Statistics

- **Total PMBus Registers**: 49
- **Implemented Read Functions**: 9
- **Implemented Write Functions**: 3
- **Implemented Commands**: 13 (includes CLEAR_FAULTS)
- **Phase Current Channels**: 16
- **Status Registers**: 8 (all clearable via CLEAR_FAULTS)
- **Rails**: 2 (TSP_CORE, TSP_C2C)

For detailed documentation, see:
- `CLAUDE.md` - Project overview and architecture
- `PCIE_I2C_USAGE.md` - PCIe tool usage guide
- `STATUS_DECODERS.md` - Status register decoding
- `pmbus_common.py` - Implementation details
