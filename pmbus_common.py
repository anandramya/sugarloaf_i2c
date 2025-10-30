#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMBus Common Functions Library
Shared data conversion and parsing functions for PMBus devices.
Used by both serial (powertool.py) and PCIe (powertool_pcie.py) versions.
"""

import math

# PMBus register definitions - shared across all implementations
PMBusDict = {
    # Standard PMBus Commands
    "PAGE": 0x00,
    "OPERATION": 0x01,
    "CLEAR_FAULTS": 0x03,
    "VOUT_MODE": 0x20,
    "VOUT_COMMAND": 0x21,
    "STATUS_BYTE": 0x78,
    "STATUS_WORD": 0x79,
    "STATUS_VOUT": 0x7A,
    "STATUS_IOUT": 0x7B,
    "STATUS_INPUT": 0x7C,
    "STATUS_TEMPERATURE": 0x7D,
    "STATUS_MFR_SPECIFIC": 0x80,
    "READ_VOUT": 0x8B,
    "READ_IOUT": 0x8C,
    "READ_TEMP": 0x8D,
    "READ_DIE_TEMP": 0x8E,
    "READ_DUTY": 0x94,
    "READ_PIN": 0x97,
    "READ_POUT": 0x96,
    "READ_IIN": 0x89,
    "FREQUENCY_SWITCH": 0x33,
    "VOUT_DROOP": 0x28,

    # Limit Commands
    "IOUT_OC_WARN_LIMIT": 0x4A,

    # MFR Specific Commands
    "MFR_VR_CONFIG": 0x67,
    "MFR_VID_RES_R1": 0x29,
    "MFR_TEMP_PEAK": 0xD1,
    "MFR_IOUT_PEAK": 0xD7,
    "MFR_REG_ACCESS": 0xD8,
    "REG_ACCESS": 0xD8,

    # Phase current registers
    "PHASE1_Current": 0x0C00,
    "PHASE2_Current": 0x0C01,
    "PHASE3_Current": 0x0C02,
    "PHASE4_Current": 0x0C03,
    "PHASE5_Current": 0x0C04,
    "PHASE6_Current": 0x0C05,
    "PHASE7_Current": 0x0C06,
    "PHASE8_Current": 0x0C07,
    "PHASE9_Current": 0x0C08,
    "PHASE10_Current": 0x0C09,
    "PHASE11_Current": 0x0C0A,
    "PHASE12_Current": 0x0C0B,
    "PHASE13_Current": 0x0C0C,
    "PHASE14_Current": 0x0C0D,
    "PHASE15_Current": 0x0C0E,
    "PHASE16_Current": 0x0C0F,

    # Other registers
    "VOUT_OFFSET": 0x0023,
    "Loop1_active": 0x0E00,
    "Phase_active": 0x0E00
}


def parse_vout_mode(vout_mode_byte):
    """
    Parse VOUT_MODE register to extract exponent.

    Args:
        vout_mode_byte: 8-bit VOUT_MODE register value

    Returns:
        Exponent as signed integer (5-bit two's complement)
    """
    # Extract the exponent (5-bit two's complement in bits 0-4)
    exponent = vout_mode_byte & 0x1F

    # Convert from two's complement if negative
    if exponent & 0x10:  # If bit 4 is set, it's negative
        exponent = exponent - 32

    return exponent


def parse_linear11(data):
    """
    Parse Linear11 format data.

    Format: [15:11] 5-bit exponent, [10:0] 11-bit mantissa
    Both in two's complement.

    Args:
        data: 16-bit raw value

    Returns:
        Converted float value
    """
    # Extract exponent (bits 15:11) - 5-bit two's complement
    exponent = (data >> 11) & 0x1F
    if exponent & 0x10:  # If bit 4 is set, it's negative
        exponent = exponent - 32

    # Extract mantissa (bits 10:0) - 11-bit two's complement
    mantissa = data & 0x7FF
    if mantissa & 0x400:  # If bit 10 is set, it's negative
        mantissa = mantissa - 2048

    # Calculate: mantissa × 2^exponent
    value = mantissa * math.pow(2, exponent)

    return value


def parse_linear16(data, exponent):
    """
    Parse Linear16 format data.

    Format: 16-bit mantissa with separate exponent.

    Args:
        data: 16-bit mantissa value
        exponent: Signed exponent value

    Returns:
        Converted float value
    """
    # Linear16 format: mantissa × 2^exponent
    value = data * math.pow(2, exponent)
    return value


def parse_die_temp(data):
    """
    Parse die temperature from voltage-based reading.

    Format: Unsigned binary
    Step 1: Convert to mV: voltage_mv = raw × 1.5625
    Step 2: Convert to temperature: temp = (voltage_mv - 747) / -1.9

    Args:
        data: 16-bit raw value

    Returns:
        Temperature in degrees Celsius
    """
    # Convert raw value to millivolts
    voltage_mv = data * 1.5625

    # Convert voltage to temperature using calibration formula
    die_temp = (voltage_mv - 747.0) / -1.9

    return die_temp


def calculate_vout_command(voltage, exponent):
    """
    Calculate VOUT_COMMAND register value from desired voltage.

    Args:
        voltage: Desired voltage in volts
        exponent: VOUT_MODE exponent

    Returns:
        16-bit mantissa value to write to VOUT_COMMAND
    """
    # Linear16 format: voltage / 2^exponent = mantissa
    mantissa = int(voltage / math.pow(2, exponent))
    return mantissa


class PMBusCommands:
    """
    Mixin class providing common PMBus command implementations.

    Classes using this mixin must implement:
    - i2c_read8PMBus(page, reg_addr) -> int
    - i2c_read16PMBus(page, reg_addr) -> int
    - i2c_write8PMBus(reg_addr, value)
    - i2c_write16PMBus(page, reg_addr, value)
    """

    def Read_VOUT_MODE(self, page):
        """
        Read VOUT_MODE register to determine the data format.

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Exponent as signed integer
        """
        # Read VOUT_MODE as a byte
        mode = self.i2c_read16PMBus(page, PMBusDict["VOUT_MODE"]) & 0xFF

        # Parse and return exponent
        return parse_vout_mode(mode)

    def Read_Vout(self, page):
        """
        Read output voltage from PMBus device.

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Voltage in volts
        """
        data = self.i2c_read16PMBus(page, PMBusDict["READ_VOUT"])

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(page)
            # If VOUT_MODE returns 0, use default exponent
            if exponent == 0:
                exponent = -10  # Default for VR controllers
        except:
            exponent = -10  # Default for many VR controllers

        # Use common Linear16 parsing function
        vout = parse_linear16(data, exponent)

        return vout

    def Read_Iout(self, page):
        """
        Read output current from PMBus device (Linear11 format).

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Current in amperes
        """
        data = self.i2c_read16PMBus(page, PMBusDict["READ_IOUT"])

        # Use common Linear11 parsing function
        iout = parse_linear11(data)

        return iout

    def Read_Temp(self, page):
        """
        Read temperature from PMBus device (Linear11 format).

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Temperature in degrees Celsius
        """
        data = self.i2c_read16PMBus(page, PMBusDict["READ_TEMP"])

        # Use common Linear11 parsing function
        temp = parse_linear11(data)

        return temp

    def Read_Die_Temp(self, page):
        """
        Read die temperature (voltage-based conversion).

        Format: Unsigned binary
        Die temp in mV: 1.5625mV/LSB
        Then convert: die_temp = (value*1.5625 - 747) / -1.9

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Die temperature in degrees Celsius
        """
        data = self.i2c_read16PMBus(page, PMBusDict["READ_DIE_TEMP"])

        # Use common die temp parsing function
        die_temp = parse_die_temp(data)

        return die_temp

    def Read_Status_Word(self, page):
        """
        Read STATUS_WORD register.

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Status word as integer
        """
        return self.i2c_read16PMBus(page, PMBusDict["STATUS_WORD"])

    def Write_Vout_Command(self, page, voltage):
        """
        Set output voltage.

        Args:
            page: PMBus page (0 or 1)
            voltage: Target voltage in volts
        """
        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(page)
            # If VOUT_MODE returns 0, use default exponent
            if exponent == 0:
                exponent = -10  # Default for VR controllers
        except:
            exponent = -10  # Default for many VR controllers

        # Calculate mantissa using common function
        mantissa = calculate_vout_command(voltage, exponent)

        # Write to VOUT_COMMAND register
        self.i2c_write16PMBus(page, PMBusDict["VOUT_COMMAND"], mantissa)

        print(f"✓ Set voltage to {voltage:.4f}V (mantissa=0x{mantissa:04X}, exponent={exponent})")

    def Read_IOUT_Scale(self, page):
        """
        Read IOUT_SCALE_BIT_A from MFR_VR_CONFIG register.

        The IOUT_SCALE_BIT_A is in bits [2:0] of MFR_VR_CONFIG (0x67).
        This scale factor is used for IOUT_OC_WARN_LIMIT calculations.

        Args:
            page: PMBus page (0 or 1)

        Returns:
            IOUT_SCALE_BIT_A value (0-7)
        """
        mfr_vr_config = self.i2c_read16PMBus(page, PMBusDict["MFR_VR_CONFIG"])

        # Extract IOUT_SCALE_BIT_A from bits [2:0]
        iout_scale = mfr_vr_config & 0x07

        return iout_scale

    def Read_IOUT_OC_WARN_LIMIT(self, page):
        """
        Read IOUT overcurrent warning limit.

        Format: Unsigned binary
        Bits [15:8]: Reserved (always 0)
        Bits [7:0]: IOUT_OC_WARN_LIMIT value
        Scaling: OCP_Warn_Level = 8 * IOUT_SCALE_BIT_A (A)
        LSB = 8 * IOUT_SCALE_BIT_A

        Args:
            page: PMBus page (0 or 1)

        Returns:
            Warning limit in amperes
        """
        # Read the register value
        raw_value = self.i2c_read16PMBus(page, PMBusDict["IOUT_OC_WARN_LIMIT"])

        # Extract the limit value from bits [7:0]
        limit_raw = raw_value & 0xFF

        # Read IOUT scale factor
        iout_scale = self.Read_IOUT_Scale(page)

        # Calculate the actual current limit
        # OCP_Warn_Level = limit_raw * LSB
        # where LSB = 8 * IOUT_SCALE_BIT_A
        lsb = 8 * iout_scale
        warn_limit = limit_raw * lsb

        return warn_limit

    def Write_IOUT_OC_WARN_LIMIT(self, page, limit_amps):
        """
        Set IOUT overcurrent warning limit.

        Format: Unsigned binary
        Bits [15:8]: Reserved (set to 0)
        Bits [7:0]: IOUT_OC_WARN_LIMIT value
        Scaling: OCP_Warn_Level = 8 * IOUT_SCALE_BIT_A (A)

        Args:
            page: PMBus page (0 or 1)
            limit_amps: Warning limit in amperes
        """
        # Read IOUT scale factor
        iout_scale = self.Read_IOUT_Scale(page)

        # Calculate LSB
        lsb = 8 * iout_scale

        if lsb == 0:
            raise ValueError("IOUT_SCALE_BIT_A is 0, cannot calculate limit")

        # Calculate raw value
        # limit_raw = limit_amps / LSB
        limit_raw = int(limit_amps / lsb)

        # Ensure it fits in 8 bits
        if limit_raw > 255:
            raise ValueError(f"Limit {limit_amps}A exceeds maximum (255 * {lsb}A = {255 * lsb}A)")

        # Write to register (bits [15:8] are reserved and set to 0)
        self.i2c_write16PMBus(page, PMBusDict["IOUT_OC_WARN_LIMIT"], limit_raw)

        print(f"✓ Set IOUT_OC_WARN_LIMIT to {limit_amps}A (raw=0x{limit_raw:02X}, scale={iout_scale}, LSB={lsb}A)")


# Convenience functions for standalone use
def convert_vout(raw_value, vout_mode_byte):
    """
    Convenience function to convert READ_VOUT raw value.

    Args:
        raw_value: 16-bit raw VOUT reading
        vout_mode_byte: 8-bit VOUT_MODE register value

    Returns:
        Voltage in volts
    """
    exponent = parse_vout_mode(vout_mode_byte)
    if exponent == 0:
        exponent = -10
    return parse_linear16(raw_value, exponent)


def convert_iout(raw_value):
    """
    Convenience function to convert READ_IOUT raw value.

    Args:
        raw_value: 16-bit raw IOUT reading

    Returns:
        Current in amperes
    """
    return parse_linear11(raw_value)


def convert_temp(raw_value):
    """
    Convenience function to convert READ_TEMP raw value.

    Args:
        raw_value: 16-bit raw TEMP reading

    Returns:
        Temperature in degrees Celsius
    """
    return parse_linear11(raw_value)


def convert_die_temp(raw_value):
    """
    Convenience function to convert READ_DIE_TEMP raw value.

    Args:
        raw_value: 16-bit raw DIE_TEMP reading

    Returns:
        Temperature in degrees Celsius
    """
    return parse_die_temp(raw_value)


def decode_status_word(status_word):
    """
    Decode STATUS_WORD register bits into human-readable information.

    Args:
        status_word: 16-bit STATUS_WORD value

    Returns:
        Dictionary with bit names and their meanings
    """
    decoded = {
        'raw_value': status_word,
        'bits': {}
    }

    # Bit definitions according to PMBus specification
    bit_defs = [
        (15, 'VOUT', 'VOUT fault/warning'),
        (14, 'IOUT', 'IOUT fault/warning'),
        (13, 'INPUT', 'Input voltage/current fault/warning'),
        (12, 'MFR_SPECIFIC', 'Manufacturer specific fault'),
        (11, 'POWER_GOOD_N', 'Power Good not active'),
        (10, 'RESERVED_10', 'Reserved'),
        (9, 'RESERVED_9', 'Reserved'),
        (8, 'WATCH_DOG_OVF', 'Watchdog timer overflow'),
        (7, 'NVM_BUSY', 'NVM busy'),
        (6, 'OFF', 'Output is off'),
        (5, 'VOUT_OV_FAULT', 'VOUT overvoltage fault'),
        (4, 'IOUT_OC_FAULT', 'IOUT overcurrent fault'),
        (3, 'VIN_UV_FAULT', 'VIN undervoltage fault'),
        (2, 'TEMPERATURE', 'Over-temperature fault/warning'),
        (1, 'CML', 'Communication fault'),
        (0, 'OTHER_FAULT', 'Other fault')
    ]

    for bit_num, bit_name, description in bit_defs:
        bit_value = (status_word >> bit_num) & 1
        decoded['bits'][bit_name] = {
            'value': bit_value,
            'description': description,
            'active': bit_value == 1
        }

    return decoded


def format_status_word(status_word, show_all=False):
    """
    Format STATUS_WORD into a human-readable string.

    Args:
        status_word: 16-bit STATUS_WORD value
        show_all: If True, show all bits. If False, only show active faults.

    Returns:
        Formatted string with status information
    """
    decoded = decode_status_word(status_word)

    lines = [f"STATUS_WORD: 0x{status_word:04X}"]

    # Check if any faults are active
    active_faults = [name for name, info in decoded['bits'].items()
                     if info['active'] and name not in ['RESERVED_9', 'RESERVED_10']]

    if not active_faults:
        lines.append("  ✓ No faults detected")
        return '\n'.join(lines)

    # Show active faults
    lines.append("  ⚠ Active faults/warnings:")

    for bit_name, bit_info in decoded['bits'].items():
        if show_all or bit_info['active']:
            if bit_name in ['RESERVED_9', 'RESERVED_10']:
                continue

            status_char = '✗' if bit_info['active'] else '✓'
            status_text = 'FAULT' if bit_info['active'] else 'OK'
            lines.append(f"    [{status_char}] {bit_name:16s} : {status_text:5s} - {bit_info['description']}")

    return '\n'.join(lines)


def decode_status_vout(status_vout):
    """
    Decode STATUS_VOUT register bits into human-readable information.

    Args:
        status_vout: 8-bit STATUS_VOUT value

    Returns:
        Dictionary with bit names and their meanings
    """
    decoded = {
        'raw_value': status_vout,
        'bits': {}
    }

    # Bit definitions according to PMBus specification
    bit_defs = [
        (7, 'RESERVED_7', 'Reserved'),
        (6, 'RESERVED_6', 'Reserved'),
        (5, 'RESERVED_5', 'Reserved'),
        (4, 'RESERVED_4', 'Reserved'),
        (3, 'RESERVED_3', 'Reserved'),
        (2, 'RESERVED_2', 'Reserved'),
        (1, 'LINE_FLOAT', 'Line float protection fault'),
        (0, 'VOUT_SHORT', 'VOUT short fault'),
    ]

    for bit_num, bit_name, description in bit_defs:
        bit_value = (status_vout >> bit_num) & 1
        decoded['bits'][bit_name] = {
            'value': bit_value,
            'description': description,
            'active': bit_value == 1
        }

    return decoded


def format_status_vout(status_vout, show_all=False):
    """
    Format STATUS_VOUT into a human-readable string.

    Args:
        status_vout: 8-bit STATUS_VOUT value
        show_all: If True, show all bits. If False, only show active faults.

    Returns:
        Formatted string with status information
    """
    decoded = decode_status_vout(status_vout)

    lines = [f"STATUS_VOUT: 0x{status_vout:02X}"]

    # Check if any faults are active
    active_faults = [name for name, info in decoded['bits'].items()
                     if info['active'] and not name.startswith('RESERVED')]

    if not active_faults:
        lines.append("  ✓ No VOUT faults detected")
        return '\n'.join(lines)

    # Show active faults
    lines.append("  ⚠ Active VOUT faults:")

    for bit_name, bit_info in decoded['bits'].items():
        if show_all or bit_info['active']:
            if bit_name.startswith('RESERVED'):
                continue

            status_char = '✗' if bit_info['active'] else '✓'
            status_text = 'FAULT' if bit_info['active'] else 'OK'
            lines.append(f"    [{status_char}] {bit_name:16s} : {status_text:5s} - {bit_info['description']}")

    return '\n'.join(lines)


def decode_status_iout(status_iout):
    """
    Decode STATUS_IOUT register bits into human-readable information.

    Args:
        status_iout: 8-bit STATUS_IOUT value

    Returns:
        Dictionary with bit names and their meanings
    """
    decoded = {
        'raw_value': status_iout,
        'bits': {}
    }

    # Bit definitions according to PMBus specification
    bit_defs = [
        (7, 'IOUT_OC_FAULT', 'Output overcurrent fault'),
        (6, 'OCP_UV_FAULT', 'Overcurrent and undervoltage dual fault'),
        (5, 'IOUT_OC_WARN', 'Output overcurrent warning'),
        (4, 'RESERVED_4', 'Reserved'),
        (3, 'RESERVED_3', 'Reserved'),
        (2, 'RESERVED_2', 'Reserved'),
        (1, 'RESERVED_1', 'Reserved'),
        (0, 'RESERVED_0', 'Reserved'),
    ]

    for bit_num, bit_name, description in bit_defs:
        bit_value = (status_iout >> bit_num) & 1
        decoded['bits'][bit_name] = {
            'value': bit_value,
            'description': description,
            'active': bit_value == 1
        }

    return decoded


def format_status_iout(status_iout, show_all=False):
    """
    Format STATUS_IOUT into a human-readable string.

    Args:
        status_iout: 8-bit STATUS_IOUT value
        show_all: If True, show all bits. If False, only show active faults.

    Returns:
        Formatted string with status information
    """
    decoded = decode_status_iout(status_iout)

    lines = [f"STATUS_IOUT: 0x{status_iout:02X}"]

    # Check if any faults are active
    active_faults = [name for name, info in decoded['bits'].items()
                     if info['active'] and not name.startswith('RESERVED')]

    if not active_faults:
        lines.append("  ✓ No IOUT faults detected")
        return '\n'.join(lines)

    # Show active faults
    lines.append("  ⚠ Active IOUT faults/warnings:")

    for bit_name, bit_info in decoded['bits'].items():
        if show_all or bit_info['active']:
            if bit_name.startswith('RESERVED'):
                continue

            status_char = '✗' if bit_info['active'] else '✓'
            # OC_WARN is a warning, not a fault
            status_text = 'WARN' if bit_name == 'IOUT_OC_WARN' and bit_info['active'] else ('FAULT' if bit_info['active'] else 'OK')
            lines.append(f"    [{status_char}] {bit_name:16s} : {status_text:5s} - {bit_info['description']}")

    return '\n'.join(lines)
