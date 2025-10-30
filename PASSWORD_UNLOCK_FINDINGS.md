# MP29816-C Password Unlock - Investigation Findings

## Summary

Successfully identified the MP29816-C password mechanism, but IOUT_OC_WARN_LIMIT and IOUT_OC_FAULT_LIMIT registers still do not persist writes even after password unlock attempt.

## Key Findings

### 1. Password Discovery
**MFR_USER_PWD (0xD7) = 0x0192 (402 decimal)**

Despite datasheet claiming "always reads as 0", reading register 0xD7 on page 0 returned:
```bash
$ ./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0xD7 --bytes 2
Register 0xD7: 0x0192 (402 decimal)
  Byte[0] (LSB): 0x92
  Byte[1] (MSB): 0x01
```

### 2. Write Protection Status
```bash
$ ./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x10 --bytes 1
Register 0x10: 0x00 (0 decimal)
```
**Result:** WRITE_PROTECT is disabled (0x00 = no write protection)

### 3. Password Unlock Attempt
```bash
# Send password 0x0192 to CMD_SEND_PWD (0xF7) on page 1
$ ./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 402 --bytes 2
✓ Wrote 0x0192 to register 0xF7
```

### 4. Write Attempt After Unlock
```bash
$ ./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 500
✓ Set IOUT_OC_WARN_LIMIT to 500.0A (raw=0x3E, scale=1.0, LSB=8.0A)
```
Write command accepted without error.

### 5. Readback Result
```bash
$ ./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT
IOUT_OC_WARN_LIMIT: 0.0 A

$ ./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x4A --bytes 2
Register 0x4A: 0x0000 (0 decimal)
```
**Result:** Value did not persist (still reads 0x0000)

### 6. Password Match Status
```bash
$ ./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x7E --bytes 2
Register 0x7E: 0xF6A2 (63138 decimal)
```
STATUS_CML = 0xF6A2 = 0b1111011010100010
- **Bit 11 (PWD_MATCH): 0** - Password not matched or unlock not active

## Possible Reasons for Persistent Failure

### 1. NVM-Stored Registers
IOUT_OC_WARN_LIMIT and IOUT_OC_FAULT_LIMIT might be stored in non-volatile memory and require:
- A STORE command after writing (e.g., STORE_USER_ALL at 0x15)
- Power cycle to activate new values
- Special manufacturer command sequence

### 2. Password Session Expiration
Password unlock might:
- Only last for a single I2C transaction
- Need to be sent immediately before each write
- Require specific timing or sequence

### 3. Additional Protection Mechanism
There might be:
- Hidden protection bits not documented
- Manufacturer-specific lock mechanism
- Hardware pin configuration preventing writes

### 4. Register Access Method
The registers might require:
- Extended register access via MFR_REG_ACCESS (0xD8)
- Different page setting
- Special command format

### 5. Factory Locked
Registers might be:
- Permanently locked at factory
- Only modifiable during manufacturing
- Configured via external resistors/pins

## Test Sequence Performed

```bash
# 1. Check write protection
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x10 --bytes 1
# Result: 0x00 (disabled)

# 2. Read password
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0xD7 --bytes 2
# Result: 0x0192

# 3. Clear faults
./powertool_pcie.py --rail TSP_CORE --cmd CLEAR_FAULTS

# 4. Send password
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 402 --bytes 2

# 5. Clear faults again
./powertool_pcie.py --rail TSP_CORE --cmd CLEAR_FAULTS

# 6. Attempt write
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 500
# Write accepted

# 7. Verify write
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT
# Result: 0.0A (write did not persist)
```

## Next Steps to Try

### Option 1: STORE Command
Try storing to NVM after write:
```bash
# Write value
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 402 --bytes 2
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 500

# Store to NVM (STORE_USER_ALL)
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0x15 --value 0 --bytes 1
```

### Option 2: Immediate Password + Write
Send password and write in rapid succession:
```bash
# Send password and immediately write (single script)
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 402 --bytes 2 && \
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0x4A --value 62 --bytes 2
```

### Option 3: Check for Hardware Lock
Verify no hardware pin lock:
- Check device schematics
- Look for LOCK pin configuration
- Verify no external pull-up/down on protection pins

### Option 4: Try Different Pages
Password might need to be sent on page 0 instead of page 1:
```bash
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0xF7 --value 402 --bytes 2
```

### Option 5: Contact MPS Support
Since the registers are:
- Not responding to password unlock
- Not respecting WRITE_PROTECT = 0x00
- Consistently clearing to 0x0000

This suggests manufacturer-specific behavior requiring MPS technical support.

## Register Access Summary

| Register | Address | Page | Read | Write | Password Needed | Persists |
|----------|---------|------|------|-------|----------------|----------|
| WRITE_PROTECT | 0x10 | 0 | ✓ (0x00) | ? | No | ? |
| MFR_USER_PWD | 0xD7 | 0 | ✓ (0x0192) | ? | No | ? |
| CMD_SEND_PWD | 0xF7 | 1 | - | ✓ | No | - |
| IOUT_OC_WARN_LIMIT | 0x4A | 0 | ✓ (0x0000) | ✗ | Yes? | ✗ |
| IOUT_OC_FAULT_LIMIT | 0x46 | 0 | ✓ (0x0000) | ✗ | Yes? | ✗ |

## Conclusion

The password mechanism is partially understood:
- ✓ Password identified: 0x0192
- ✓ Password can be written to CMD_SEND_PWD
- ✗ Writes to IOUT_OC registers still don't persist
- ✗ PWD_MATCH status bit not setting

**Likely cause:** These registers require additional manufacturer-specific commands or are intentionally locked to prevent runtime modification for safety reasons.

**Recommendation:** Contact MPS technical support with:
- Device part number: MP29816-C
- Register addresses: 0x4A (IOUT_OC_WARN_LIMIT), 0x46 (IOUT_OC_FAULT_LIMIT)
- Observed behavior: Writes accepted but don't persist
- Request: Proper procedure to modify overcurrent limits via PMBus

## Documentation Created

1. `PASSWORD_UNLOCK_GUIDE.md` - Complete guide to password mechanism
2. `PASSWORD_UNLOCK_FINDINGS.md` - This document with test results
3. `MPS2.txt` - Manufacturer datasheet with password details (450KB)

## Known Password

**For future reference:**
- Device Password: 0x0192 (402 decimal)
- Send to: CMD_SEND_PWD (0xF7) on Page 1
- Format: 16-bit value (2 bytes, little endian)
