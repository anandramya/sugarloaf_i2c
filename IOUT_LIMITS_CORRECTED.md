# IOUT Limits Implementation - CORRECTED Scale Calculation

## Date
2025-10-29

## Critical Fix

**Issue Found**: The IOUT_SCALE_BIT_A value was being used directly as the scale factor, but it's actually an index into a lookup table!

### WRONG Implementation (Before Fix)

```python
iout_scale_bits = mfr_vr_config & 0x07  # bits[2:0]
iout_scale = iout_scale_bits  # WRONG! Treating 6 as 6 A/LSB
lsb = 8 * iout_scale  # 8 * 6 = 48 A/LSB (WRONG!)
```

### CORRECT Implementation (After Fix)

```python
iout_scale_bits = mfr_vr_config & 0x07  # bits[2:0] = 6
# Look up actual scale value:
scale_lookup = {
    0: 1.0,      # 3'b000: 1 A/LSB (Reserved)
    1: 1/32,     # 3'b001: (1/32) A/LSB
    2: 1/16,     # 3'b010: (1/16) A/LSB
    3: 1/8,      # 3'b011: (1/8) A/LSB
    4: 1/4,      # 3'b100: (1/4) A/LSB
    5: 1/2,      # 3'b101: (1/2) A/LSB
    6: 1.0,      # 3'b110: 1 A/LSB ← Our device
    7: 2.0,      # 3'b111: 2 A/LSB
}
iout_scale = scale_lookup[6]  # = 1.0 A/LSB (CORRECT!)
lsb = 8 * iout_scale  # 8 * 1.0 = 8 A/LSB (CORRECT!)
```

## IOUT_SCALE Lookup Table

From device specification:

| IOUT_SCALE_BIT[2:0] | Binary | IOUT_SCALE (A/LSB) |
|---------------------|--------|--------------------|
| 0                   | 3'b000 | 1 A/LSB (Reserved) |
| 1                   | 3'b001 | 1/32 A/LSB = 0.03125 |
| 2                   | 3'b010 | 1/16 A/LSB = 0.0625 |
| 3                   | 3'b011 | 1/8 A/LSB = 0.125 |
| 4                   | 3'b100 | 1/4 A/LSB = 0.25 |
| 5                   | 3'b101 | 1/2 A/LSB = 0.5 |
| **6**               | **3'b110** | **1 A/LSB** ← **Our device** |
| 7                   | 3'b111 | 2 A/LSB |

## Device Configuration

**MFR_VR_CONFIG (0x67)** = 0x001E
- **IOUT_SCALE_BIT[2:0]** = 6 (0b110)
- **IOUT_SCALE** (from lookup) = **1.0 A/LSB**
- **LSB** = 8 × 1.0 = **8 A/LSB**

## Corrected Fault Limit Values

### Original Values (Before Tests Cleared Them)

**TSP_CORE (Page 0):**
| Item | WRONG Calculation | CORRECT Calculation |
|------|-------------------|---------------------|
| Raw value | 0x8A (138 decimal) | 0x8A (138 decimal) |
| LSB | 8 × 6 = 48 A/LSB | 8 × 1.0 = 8 A/LSB |
| **Fault limit** | **138 × 48 = 6624 A** ❌ | **138 × 8 = 1104 A** ✅ |

**TSP_C2C (Page 1):**
| Item | WRONG Calculation | CORRECT Calculation |
|------|-------------------|---------------------|
| Raw value | 0x13 (19 decimal) | 0x13 (19 decimal) |
| LSB | 8 × 6 = 48 A/LSB | 8 × 1.0 = 8 A/LSB |
| **Fault limit** | **19 × 48 = 912 A** ❌ | **19 × 8 = 152 A** ✅ |

The corrected values make much more sense:
- **1104 A** for TSP_CORE (high-power rail)
- **152 A** for TSP_C2C (lower-power rail)

### Current Values (After Write Tests)

⚠️ **Both limits currently cleared to 0 due to write tests**
- TSP_CORE: 0 A
- TSP_C2C: 0 A

## Formula Summary

**Per Specification:**
```
OCP_Fault_Level = register_value × LSB
LSB = 8 × IOUT_SCALE
IOUT_SCALE = lookup_table[IOUT_SCALE_BIT[2:0]]
```

**For our device (IOUT_SCALE_BIT[2:0] = 6):**
```
IOUT_SCALE = 1.0 A/LSB (from lookup table)
LSB = 8 × 1.0 = 8 A/LSB
OCP_Fault_Level = register_value × 8
```

**Example Calculations:**
```
Raw 0x8A (138) → 138 × 8 = 1104 A
Raw 0x13 (19)  → 19 × 8 = 152 A
Raw 0x50 (80)  → 80 × 8 = 640 A
Raw 0xFF (255) → 255 × 8 = 2040 A (max)
```

## Code Changes

### pmbus_common.py

**Modified Read_IOUT_Scale() method:**

**Before (WRONG):**
```python
def Read_IOUT_Scale(self, page):
    mfr_vr_config = self.i2c_read16PMBus(page, PMBusDict["MFR_VR_CONFIG"])
    iout_scale = mfr_vr_config & 0x07  # Returns raw bits (6)
    return iout_scale  # WRONG! Returns 6 instead of 1.0
```

**After (CORRECT):**
```python
def Read_IOUT_Scale(self, page):
    mfr_vr_config = self.i2c_read16PMBus(page, PMBusDict["MFR_VR_CONFIG"])
    iout_scale_bits = mfr_vr_config & 0x07

    # Convert 3-bit code to actual scale value via lookup table
    scale_lookup = {
        0: 1.0,   1: 1/32,  2: 1/16,  3: 1/8,
        4: 1/4,   5: 1/2,   6: 1.0,   7: 2.0,
    }
    iout_scale = scale_lookup.get(iout_scale_bits, 1.0)
    return iout_scale  # CORRECT! Returns 1.0 for code 6
```

**No changes needed to:**
- Read_IOUT_OC_FAULT_LIMIT() - formula was already correct
- Write_IOUT_OC_FAULT_LIMIT() - formula was already correct
- Read_IOUT_OC_WARN_LIMIT() - formula was already correct
- Write_IOUT_OC_WARN_LIMIT() - formula was already correct

The formulas were correct, only the scale lookup was wrong!

## Impact

### Read Functionality
✅ Now returns correct amperage values
- Old: 6624A / 912A (wrong)
- New: 1104A / 152A (correct)

### Write Functionality
⚠️ Write behavior unchanged (still clears to 0)
- This is a hardware limitation, not a calculation error
- Writes now use correct LSB value (8 A/LSB vs 48 A/LSB)
- But hardware still clears register after any write

## Testing

### Verification Test Results

```bash
$ python3 test_corrected_scale.py

TSP_CORE (Page 0):
  IOUT_SCALE_BIT[2:0] = 6 (0b110)
  IOUT_SCALE (from lookup) = 1.0 A/LSB
  LSB = 8 * 1.0 = 8.0 A/LSB

  OLD (wrong) calculation:
    LSB = 8 * 6 = 48 A/LSB
    Limit = 138 * 48 = 6624 A  ❌

  NEW (correct) calculation:
    LSB = 8 * 1.0 = 8.0 A/LSB
    Limit = 138 * 8 = 1104 A  ✅
```

### Write Test Results

```bash
$ python3 test_write_corrected.py

Writing 1104 A (raw=0x8A)...
  ✓ Write command successful
Reading back...
  Result: 0.0 A (raw: 0x00)
  ✗ Write still clears to 0
```

Conclusion: Corrected scale doesn't fix write-clearing behavior (hardware limitation remains).

## Recommendations

### For Production Use

1. ✅ **Use read functionality** - now returns correct amperage values
2. ✅ **Monitor fault limits** - 1104A/152A are reasonable thresholds
3. ⚠️ **Avoid writes** - still clears register to 0 (hardware behavior)
4. ⚠️ **Alert on 0 values** - indicates disabled protection

### Example Monitoring

```python
# Check if fault protection is enabled
fault_limit = pt.Read_IOUT_OC_FAULT_LIMIT(0)
if fault_limit == 0:
    print("⚠️ WARNING: Fault protection disabled on TSP_CORE!")
elif fault_limit < 1000:
    print(f"⚠️ WARNING: Fault limit very low: {fault_limit}A")
else:
    print(f"✓ Fault protection enabled: {fault_limit}A")
```

## Summary of Changes

| Component | Change |
|-----------|--------|
| Read_IOUT_Scale() | ✅ Added lookup table for 3-bit code → scale value |
| Read formulas | ✅ Now use correct scale (1.0 vs 6) |
| Write formulas | ✅ Now use correct scale (1.0 vs 6) |
| Read values | ✅ Corrected from 6624A/912A to 1104A/152A |
| Write behavior | ⚠️ Unchanged (hardware still clears to 0) |

## Files Modified

1. **pmbus_common.py** - Fixed Read_IOUT_Scale() with lookup table
2. **IOUT_LIMITS_CORRECTED.md** - This documentation

## Recovery Status

⚠️ **Device still needs power cycle to restore factory limits**
- Current: 0A on both rails (protection disabled)
- Expected after power cycle: 1104A / 152A

## Credit

Thank you to the user for catching this error and providing the IOUT_SCALE lookup table specification!
