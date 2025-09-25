#!/usr/bin/env python3
"""
Read MFR_VOUT_SCALE_LOOP_R1 (0x29) register for Page 0 (TSP_CORE)
"""

from powertool import PowerToolI2C, PMBusDict

def read_vid_resolution_page0():
    """Read and decode MFR_VOUT_SCALE_LOOP register for page 0"""

    print("="*70)
    print("Reading MFR_VOUT_SCALE_LOOP_R1 (0x29) for Page 0 (TSP_CORE)")
    print("="*70)

    try:
        # Initialize I2C
        i2c = PowerToolI2C()
        print("✓ I2C connection established\n")

        # Set to page 0
        i2c.i2c_write8PMBus(PMBusDict["PAGE"], 0)
        print("Set to Page 0 (TSP_CORE)\n")

        # Read MFR_VOUT_SCALE_LOOP_R1 register
        raw_value = i2c.i2c_read16PMBus(0, 0x29)

        print(f"MFR_VOUT_SCALE_LOOP_R1 (0x29) Raw Value:")
        print(f"  Hex: 0x{raw_value:04X}")
        print(f"  Decimal: {raw_value}")
        print(f"  Binary: {bin(raw_value)[2:].zfill(16)}")
        print()

        # Decode the register bits
        print("Bit Field Analysis:")
        print("-" * 50)

        # Bits [15:14] - RESERVED
        bits_15_14 = (raw_value >> 14) & 0x3
        print(f"Bits [15:14] RESERVED: {bin(bits_15_14)[2:].zfill(2)} ({bits_15_14})")

        # Bit [13] - MFR_TON_ADD1_R1
        bit_13 = (raw_value >> 13) & 0x1
        print(f"Bit [13] MFR_TON_ADD1_R1: {bit_13}")
        print(f"         Ton add 1LSB: {'Yes' if bit_13 else 'No'}")

        # Bits [12:10] - MFR_VID_RES_R1 (VID_STEP)
        bits_12_10 = (raw_value >> 10) & 0x7
        print(f"Bits [12:10] MFR_VID_RES_R1: {bin(bits_12_10)[2:].zfill(3)} ({bits_12_10})")

        # VID_STEP lookup
        vid_step_map = {
            0: ("6.25mV", 6.25),
            1: ("5mV", 5.0),
            2: ("2.5mV", 2.5),
            3: ("2mV", 2.0),
            4: ("1mV", 1.0),
            5: ("1/256mV = 0.00390625mV", 1.0/256),
            6: ("1/512mV = 0.001953125mV", 1.0/512),
            7: ("1/1024mV = 0.9765625mV", 1000.0/1024)
        }

        vid_step_desc, vid_step_mv = vid_step_map.get(bits_12_10, ("Unknown", 0))
        print(f"         VID_STEP: {vid_step_desc}")
        print(f"         Value: {vid_step_mv}mV = {vid_step_mv/1000}V")

        # Bits [9:8] - MFR_SR_RES_R1 (Slew Rate Resolution)
        bits_9_8 = (raw_value >> 8) & 0x3
        print(f"Bits [9:8] MFR_SR_RES_R1: {bin(bits_9_8)[2:].zfill(2)} ({bits_9_8})")

        sr_res_map = {
            0: "0.1mV/LSB",
            1: "0.5mV/LSB",
            2: "1mV/LSB",
            3: "5mV/LSB"
        }
        sr_res = sr_res_map.get(bits_9_8, "Unknown")
        print(f"         Slew Rate Resolution: {sr_res}")

        # Lower 8 bits
        bits_7_0 = raw_value & 0xFF
        print(f"Bits [7:0]: 0x{bits_7_0:02X} ({bits_7_0})")

        print("\n" + "="*70)
        print("Testing with current VOUT_COMMAND:")
        print("-" * 50)

        # Read current VOUT_COMMAND
        vout_cmd = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
        vid_code = vout_cmd & 0xFFF

        print(f"Current VOUT_COMMAND: 0x{vout_cmd:04X}")
        print(f"VID code (bits [11:0]): {vid_code} (0x{vid_code:03X})")

        # Calculate voltage with the VID_STEP from register
        calc_voltage = vid_code * (vid_step_mv / 1000)
        print(f"Calculated voltage: {vid_code} × {vid_step_mv/1000}V = {calc_voltage:.6f}V")

        # Read actual voltage
        actual_voltage = i2c.Read_Vout_Rail1()
        print(f"Actual READ_VOUT: {actual_voltage:.6f}V")

        # Check match
        diff = abs(actual_voltage - calc_voltage)
        print(f"Difference: {diff*1000:.3f}mV")

        if diff < 0.050:
            print("✓ VID_STEP matches!")
        else:
            print("⚠️ VID_STEP mismatch - may need different value")

            # Try to find matching VID_STEP
            print("\nTrying to find matching VID_STEP:")
            implied_step = (actual_voltage / vid_code) * 1000  # in mV
            print(f"Implied VID_STEP: {actual_voltage}V / {vid_code} = {implied_step:.6f}mV")

            # Check against known values
            for code, (desc, step_mv) in vid_step_map.items():
                if abs(step_mv - implied_step) < 0.1:  # Within 0.1mV
                    print(f"  → Closest match: Code {code} = {desc}")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Aardvark adapter is connected.")

    print("\n" + "="*70)

if __name__ == "__main__":
    read_vid_resolution_page0()