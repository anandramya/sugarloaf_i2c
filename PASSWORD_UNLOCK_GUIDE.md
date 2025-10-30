# MP29816-C Password Unlock Guide

## Overview
The MP29816-C uses a password protection mechanism to prevent accidental writes to critical registers like IOUT_OC_FAULT_LIMIT and IOUT_OC_WARN_LIMIT.

## Key Registers

| Register | Address | Page | Description |
|----------|---------|------|-------------|
| WRITE_PROTECT | 0x10 | Both | Controls write protection level |
| MFR_USER_PWD | 0xD7 | 0 or 1 | Stores the system password (16-bit) |
| CMD_SEND_PWD | 0xF7 | 1 | Send password to unlock (16-bit) |
| CMD_PWD_LOCK | 0xFA | 1 | Force device to lock (send-byte) |

## Password Protection Mechanism

### MFR_USER_PWD (0xD7)
- **Format:** Unsigned binary (16-bit)
- **Access:** R/W
- **Location:** Page 0 or Page 1
- **Purpose:** Stores the user-defined password
- **Important:** Always reads as 0x0000 (password is write-only for security)
- **Effective:** Only when MFR_USER_PWD != 0 (if 0, no password protection)

### CMD_SEND_PWD (0xF7)
- **Format:** Direct (16-bit)
- **Access:** Write-only
- **Location:** Page 1
- **Purpose:** Send password to unlock the device
- **Behavior:** When sent password == MFR_USER_PWD, device unlocks

### CMD_PWD_LOCK (0xFA)
- **Format:** Send-byte (no data)
- **Access:** Write-only
- **Location:** Page 1
- **Purpose:** Force device to lock immediately

## WRITE_PROTECT Levels

The WRITE_PROTECT register (0x10) controls what can be written:

| Value | Description | Needs Password |
|-------|-------------|----------------|
| 0x80 | Write protect ALL except WRITE_PROTECT itself | No |
| 0x40 | Write protect except WRITE_PROTECT, PAGE, OPERATION | No |
| 0x20 | Write protect except WRITE_PROTECT, PAGE, OPERATION, VOUT_COMMAND | No |
| 0x03 | Write protect except PAGE. Needs password unlock | Yes (0xFA) |
| 0x02 | Write protect except PAGE, VOUT_COMMAND, VMIN_AWARE, PSI/APS | Yes (0xFA) |
| 0x01 | Write protect except PAGE, VOUT_COMMAND, VMIN_AWARE, PSI/APS, OPL_SET, OPL_SR | Yes (0xFA) |
| Other | Disable write protect | No |

**Note:** Levels 0x01, 0x02, 0x03 require PMBus lock command (0xFA = CMD_PWD_LOCK)

## Unlock Procedure

### Step 1: Check WRITE_PROTECT Status
```bash
# Read current WRITE_PROTECT setting
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x10 --bytes 1
```

### Step 2: Read Password (Optional - Will Return 0)
```bash
# Page 0
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0xD7 --bytes 2

# Page 1
./powertool_pcie.py --rail TSP_C2C --cmd REG_READ --reg-addr 0xD7 --bytes 2
```
**Note:** This will always return 0x0000 for security reasons

### Step 3: Send Password to Unlock
```bash
# Send password on Page 1 (TSP_C2C)
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value <PASSWORD> --bytes 2
```

### Step 4: Verify Unlock Status
Check STATUS_CML bit 11 (PWD_MATCH):
```bash
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x7E --bytes 1
```
If bit 11 is set, password matched and device is unlocked.

### Step 5: Perform Write Operation
```bash
# Example: Set IOUT_OC_WARN_LIMIT to 500A
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 500
```

### Step 6: Lock Device (Optional)
```bash
# Force lock using CMD_PWD_LOCK on Page 1
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xFA --value 0 --bytes 1
```

## Finding the Password

### Option 1: No Password Set (Default)
If MFR_USER_PWD = 0 (factory default), there's no password protection:
```bash
# Try writing with password 0x0000
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 0 --bytes 2
```

### Option 2: Known Password
If you know the password (from device configuration or OEM documentation):
```bash
# Send the known password
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value <PASSWORD> --bytes 2
```

### Option 3: Try Common Passwords
Some manufacturers use default passwords like:
- 0x0000 (no password)
- 0xFFFF
- 0x1234
- 0x5678
- Device-specific values (check OEM docs)

### Option 4: Disable Write Protection
If WRITE_PROTECT is not set to require password (0x01/0x02/0x03):
```bash
# Disable write protection
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0x10 --value 0 --bytes 1
```

## STATUS_CML Password Indicator

**Bit 11: PWD_MATCH**
- When set (1): Password matched, device unlocked
- When clear (0): Password not matched or device locked

Check with:
```bash
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x7E --bytes 1
# If result & 0x0800 (bit 11), password is matched
```

## Warnings

### Deadlock Conditions
From the datasheet:
1. **Lock by TOG**: Will cause deadlock
2. **Lock by password error**: Will cause deadlock
3. **Lock by TOG or password error**: Will disable all writes

**Prevention:**
- Set `MFR_LOCK_DIS_ALL_WR = 0` in password mode to avoid deadlock
- Don't send incorrect passwords repeatedly

### Write Protection Behavior
- Some WRITE_PROTECT levels allow certain commands without password
- VOUT_COMMAND may be writable even when protected (levels 0x01, 0x02, 0x20)
- PAGE register is always writable for all protection levels

## Troubleshooting

### Writes Still Fail After Unlock
1. Check STATUS_CML bit 11 (PWD_MATCH) to verify unlock succeeded
2. Verify WRITE_PROTECT level allows the register you're writing
3. Check if register requires additional unlock steps
4. Verify page is set correctly

### Cannot Read Password
**This is normal!** MFR_USER_PWD always reads as 0x0000 for security.
You must either:
- Know the password from OEM/configuration
- Try common default passwords
- Disable WRITE_PROTECT if not password-protected

### CML Fault Persists
The CML fault from failed writes may persist until:
- Password is correctly entered
- CLEAR_FAULTS is sent
- Device is power cycled

## Example: Complete Unlock and Write Sequence

```bash
# 1. Check current WRITE_PROTECT level
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x10 --bytes 1

# 2. Try password 0x0000 (no password)
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xF7 --value 0 --bytes 2

# 3. Check if unlocked (STATUS_CML bit 11)
./powertool_pcie.py --rail TSP_CORE --cmd REG_READ --reg-addr 0x7E --bytes 1

# 4. Clear any existing faults
./powertool_pcie.py --rail TSP_CORE --cmd CLEAR_FAULTS

# 5. Attempt write
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT --value 500

# 6. Verify write succeeded
./powertool_pcie.py --rail TSP_CORE --cmd IOUT_OC_WARN_LIMIT

# 7. Lock device (optional)
./powertool_pcie.py --rail TSP_C2C --cmd REG_WRITE --reg-addr 0xFA --value 0 --bytes 1
```

## Summary

The MP29816-C password protection mechanism:
1. **Set Password**: MFR_USER_PWD (0xD7) on page 0/1 (16-bit)
2. **Send Password**: CMD_SEND_PWD (0xF7) on page 1 (16-bit)
3. **Check Status**: STATUS_CML bit 11 (PWD_MATCH)
4. **Lock Device**: CMD_PWD_LOCK (0xFA) on page 1 (send-byte)

If no password is set (MFR_USER_PWD = 0), try disabling WRITE_PROTECT instead:
```bash
./powertool_pcie.py --rail TSP_CORE --cmd REG_WRITE --reg-addr 0x10 --value 0 --bytes 1
```
