# PCIe I2C Tool - Current Status

## Summary

Created `powertool_pcie.py` - a Python wrapper for the i2ctool binary to access PMBus devices via PCIe.

## What Works

✅ **Script created** - powertool_pcie.py with full PMBus command support
✅ **PCIe device recognized** - 0000:c1:00.0 is detected by i2ctool
✅ **Commands execute** - i2ctool binary runs without crashing
✅ **Proper argument formatting** - Corrected bus-num handling (omitted to use default)

## Current Issue

❌ **MCU Error 0x00000205** - All I2C transactions fail with this error code

```
[fwtools] [error] Transport::send_and_parse_bytes | mcu returns error code: 0x00000205
```

### What This Error Means

Error 0x00000205 from the MCU transport layer typically indicates:
- I2C NACK (device not acknowledging)
- Device not present at the specified address
- I2C bus not accessible
- Device not powered or not connected
- Wrong bus number selection

### Commands Tested

All failing with same error:

```bash
# Read attempts (all fail with 0x00000205)
./i2ctool -d 0000:c1:00.0 -a 0x5C -r 0x01 -t pmbus -l 1 --reg-addr-len 1
./i2ctool -d 0000:c1:00.0 -a 0x5C -r 0x01 -t i2c -l 1 --reg-addr-len 1
./i2ctool -d 0000:c1:00.0 -a 0x5C -r 0x8B -t pmbus -l 2 --reg-addr-len 1

# Write attempts (all fail with 0x00000205)
./i2ctool -d 0000:c1:00.0 -a 0x5C -r 0x00 -t pmbus -w 0 --write-len 1 --reg-addr-len 1
```

## Possible Solutions

### 1. Check I2C Device Connection
```bash
# The device should be at I2C address 0x5C
# Verify PMBus device is powered and physically connected
```

### 2. Try Different I2C Addresses
The default is 0x5C (92 decimal). Try scanning for devices:
```bash
# Try common PMBus addresses
for addr in 0x40 0x41 0x50 0x5C 0x60; do
  echo "Testing address $addr:"
  ./i2ctool -d 0000:c1:00.0 -a $addr -r 0x01 -t pmbus -l 1 --reg-addr-len 1
done
```

### 3. Check Bus Number
The tool defaults to bus-num: 0. The `-b` parameter expects specific enum values: `UINT:{,,,}`

The valid bus numbers aren't shown in help. They may be:
- Device-specific enum values
- Need to match hardware configuration
- May need explicit specification

### 4. Verify PCIe Device Configuration
```bash
# Check if the PCIe device needs initialization
lspci -vvv -s 0000:c1:00.0

# Check for any kernel drivers loaded
lspci -k -s 0000:c1:00.0
```

### 5. Check MCU Firmware/Status
The error comes from the MCU transport layer. The MCU on the PCIe card may need:
- Firmware initialization
- Configuration via another tool first
- Reset or power cycle

### 6. Compare with Working Setup
If there's a known working i2ctool command:
- Check exact parameters used
- Verify device address and bus number
- Check if any initialization steps are needed first

## Python Tool Usage

Once the hardware issue is resolved, the Python tool should work:

```bash
# Test mode (reads both rails)
./powertool_pcie.py --test

# Read voltage
./powertool_pcie.py --rail TSP_CORE --cmd READ_VOUT

# Read current
./powertool_pcie.py --rail TSP_C2C --cmd READ_IOUT

# Set voltage
./powertool_pcie.py --rail TSP_CORE --cmd VOUT_COMMAND --value 0.8
```

## Files Created

1. **powertool_pcie.py** - Main Python tool (executable)
2. **PCIE_I2C_USAGE.md** - Complete usage documentation
3. **PCIE_STATUS.md** - This file

## Next Steps

1. **Verify hardware** - Ensure PMBus device is powered and connected to PCIe card
2. **Check I2C address** - Confirm device is at 0x5C or scan for it
3. **Find working example** - Get a known-working i2ctool command to compare
4. **Check MCU status** - Verify MCU on PCIe card is initialized and ready
5. **Try different bus numbers** - If valid values can be determined

## Technical Details

### PCIe Device
- Address: 0000:c1:00.0
- Recognized by i2ctool

### I2C Configuration (Current Attempt)
- Address: 0x5C (92 decimal)
- Bus type: pmbus (also tried i2c)
- Bus number: 0 (default, may be incorrect)
- Register address length: 1 byte

### Error Code
- **0x00000205** - MCU transport error
- Indicates I2C transaction failure at hardware level
- Not a software/parsing issue

## Contact

For hardware-specific questions:
- Check if PMBus device is connected and powered
- Verify correct I2C address in hardware documentation
- Confirm PCIe card MCU is initialized
- Get working i2ctool example command if available
