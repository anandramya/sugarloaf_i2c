#!/usr/bin/env python3
"""
Debug script for VOUT_COMMAND and VID resolution
Tests MFR_VID_RES_R1 register reading and VOUT_COMMAND calculations
"""

from powertool import PowerToolI2C, PMBusDict
import math

def debug_vid_resolution():
    """Debug VID resolution and VOUT_COMMAND calculations"""

    print("="*70)
    print("VOUT_COMMAND Debug Tool")
    print("="*70)

    try:
        # Initialize I2C connection
        i2c = PowerToolI2C()
        print("✓ I2C connection established\n")

        # Test both rails
        rails = [
            {"page": 0, "name": "TSP_CORE"},
            {"page": 1, "name": "TSP_C2C"}
        ]

        for rail in rails:
            page = rail["page"]
            name = rail["name"]

            print(f"\n{'='*50}")
            print(f"Testing {name} (Page {page})")
            print(f"{'='*50}")

            # 1. Read MFR_VID_RES_R1 register
            print("\n1. Reading MFR_VID_RES_R1 register (0x29):")
            try:
                vid_res_raw = i2c.i2c_read16PMBus(page, PMBusDict["MFR_VID_RES_R1"])
                print(f"   Raw value: 0x{vid_res_raw:04X} (decimal: {vid_res_raw})")
                print(f"   Binary: {bin(vid_res_raw)[2:].zfill(16)}")

                # Extract bits [12:10]
                vid_step_bits = (vid_res_raw >> 10) & 0x07
                print(f"   Bits [12:10]: {bin(vid_step_bits)[2:].zfill(3)} (decimal: {vid_step_bits})")

                # VID_STEP lookup table
                vid_step_table = {
                    0: 0.05,   # 0.05mV
                    1: 0.1,    # 0.1mV
                    2: 0.125,  # 0.125mV
                    3: 0.25,   # 0.25mV
                    4: 0.5,    # 0.5mV
                    5: 1.0,    # 1.0mV
                    6: 1.25,   # 1.25mV
                    7: 0.25    # 0.25mV (default)
                }

                vid_step_mv = vid_step_table.get(vid_step_bits, 0.25)
                vid_step_v = vid_step_mv / 1000.0

                print(f"   VID_STEP: {vid_step_mv}mV ({vid_step_v}V)")

            except Exception as e:
                print(f"   Error reading MFR_VID_RES_R1: {e}")
                vid_step_v = 0.00025  # Default
                vid_step_mv = 0.25

            # 2. Read current VOUT_COMMAND
            print("\n2. Reading current VOUT_COMMAND (0x21):")
            try:
                vout_cmd_raw = i2c.i2c_read16PMBus(page, PMBusDict["VOUT_COMMAND"])
                print(f"   Raw value: 0x{vout_cmd_raw:04X} (decimal: {vout_cmd_raw})")

                # VID format uses bits [11:0]
                vid_code = vout_cmd_raw & 0xFFF
                print(f"   VID code (bits [11:0]): 0x{vid_code:03X} (decimal: {vid_code})")

                # Calculate voltage from VID code
                calculated_voltage = vid_code * vid_step_v
                print(f"   Calculated voltage: {calculated_voltage:.6f}V")

            except Exception as e:
                print(f"   Error reading VOUT_COMMAND: {e}")
                vout_cmd_raw = 0
                calculated_voltage = 0

            # 3. Read actual VOUT
            print("\n3. Reading actual READ_VOUT (0x8B):")
            try:
                vout_raw = i2c.i2c_read16PMBus(page, PMBusDict["READ_VOUT"])

                # Try to read VOUT_MODE for the exponent
                try:
                    vout_mode = i2c.i2c_read8PMBus(page, PMBusDict["VOUT_MODE"])
                    # Extract exponent from bits [4:0] as signed 5-bit
                    exponent_raw = vout_mode & 0x1F
                    if exponent_raw & 0x10:  # If bit 4 is set, it's negative
                        exponent = exponent_raw - 0x20
                    else:
                        exponent = exponent_raw
                except:
                    exponent = -10  # Default

                # Linear16 format
                actual_voltage = vout_raw * math.pow(2, exponent)

                print(f"   Raw value: 0x{vout_raw:04X} (decimal: {vout_raw})")
                print(f"   Exponent: {exponent}")
                print(f"   Actual voltage: {actual_voltage:.6f}V")

            except Exception as e:
                print(f"   Error reading READ_VOUT: {e}")
                actual_voltage = 0

            # 4. Calculate expected values for 0.6V
            print("\n4. Calculating expected VOUT_COMMAND for 0.6V:")
            target_voltage = 0.6
            expected_vid_code = int(target_voltage / vid_step_v)
            expected_raw = expected_vid_code & 0xFFF

            print(f"   Target voltage: {target_voltage}V")
            print(f"   VID_STEP: {vid_step_mv}mV")
            print(f"   Expected VID code: {expected_vid_code} (0x{expected_vid_code:03X})")
            print(f"   Expected raw value: 0x{expected_raw:04X}")
            print(f"   Verification: {expected_vid_code} * {vid_step_v}V = {expected_vid_code * vid_step_v:.6f}V")

            # 5. Compare values
            print("\n5. Comparison:")
            if calculated_voltage > 0 and actual_voltage > 0:
                difference = actual_voltage - calculated_voltage
                percent_diff = (difference / calculated_voltage) * 100 if calculated_voltage != 0 else 0

                print(f"   VOUT_COMMAND voltage: {calculated_voltage:.6f}V")
                print(f"   READ_VOUT voltage:    {actual_voltage:.6f}V")
                print(f"   Difference:           {difference:.6f}V ({percent_diff:.2f}%)")

                if abs(difference) > 0.01:  # More than 10mV difference
                    print("   ⚠️  Warning: Significant mismatch between commanded and actual voltage!")
                else:
                    print("   ✓ Values match within tolerance")

            print()

        # Test writing 0.6V to TSP_CORE
        print("\n" + "="*50)
        print("Testing VOUT_COMMAND write for 0.6V on TSP_CORE")
        print("="*50)

        response = input("\nDo you want to test writing 0.6V to TSP_CORE? (y/n): ")
        if response.lower() == 'y':
            success = i2c.Write_Vout_Command(0, 0.6)
            if success:
                print("✓ VOUT_COMMAND written successfully")

                # Wait a moment for voltage to settle
                import time
                time.sleep(0.5)

                # Read back the values
                print("\nReading back values after write:")
                vout_cmd_raw = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
                vout_raw = i2c.i2c_read16PMBus(0, PMBusDict["READ_VOUT"])

                vid_code = vout_cmd_raw & 0xFFF
                commanded_v = vid_code * vid_step_v
                actual_v = vout_raw * math.pow(2, -10)  # Assuming -10 exponent

                print(f"  VOUT_COMMAND: 0x{vout_cmd_raw:04X} = {commanded_v:.6f}V")
                print(f"  READ_VOUT:    0x{vout_raw:04X} = {actual_v:.6f}V")

                if abs(actual_v - 0.6) > 0.01:
                    print("  ⚠️  Voltage did not reach target!")
                else:
                    print("  ✓ Voltage successfully set to 0.6V")
            else:
                print("✗ Failed to write VOUT_COMMAND")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Aardvark adapter is connected and the device is powered.")

    print("\n" + "="*70)
    print("Debug complete")
    print("="*70)

if __name__ == "__main__":
    debug_vid_resolution()