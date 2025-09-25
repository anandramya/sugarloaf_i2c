#!/usr/bin/env python3
"""
Test TSP_CORE with 0.25mV VID_STEP for 0.7V target
"""

from powertool import PowerToolI2C, PMBusDict
import time

def test_tspcore_07v():
    """Test TSP_CORE with 0.25mV step for 0.7V target"""

    print("="*70)
    print("TSP_CORE Test: 0.7V with VID_STEP = 0.25mV")
    print("="*70)

    # Define VID_STEP for TSP_CORE
    VID_STEP_TSPCORE = 0.25 / 1000  # 0.25mV = 0.00025V

    print(f"\nTSP_CORE VID_STEP = 0.25mV = {VID_STEP_TSPCORE:.10f}V")

    try:
        # Initialize I2C
        i2c = PowerToolI2C()
        print("✓ I2C connection established\n")

        # Set to page 0 (TSP_CORE)
        i2c.i2c_write8PMBus(PMBusDict["PAGE"], 0)

        print("="*50)
        print("Current TSP_CORE Status")
        print("="*50)

        # Read current VOUT_COMMAND
        vout_cmd_current = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
        vid_code_current = vout_cmd_current & 0xFFF
        calc_voltage_current = vid_code_current * VID_STEP_TSPCORE

        print(f"Current VOUT_COMMAND:")
        print(f"  Raw value: 0x{vout_cmd_current:04X}")
        print(f"  VID code: {vid_code_current} (0x{vid_code_current:03X})")
        print(f"  Calculated voltage: {calc_voltage_current:.6f}V")

        # Read actual voltage
        actual_voltage_current = i2c.Read_Vout_Rail1()
        print(f"  Actual READ_VOUT: {actual_voltage_current:.6f}V")

        diff_current = abs(actual_voltage_current - calc_voltage_current)
        print(f"  Difference: {diff_current*1000:.3f}mV")

        if diff_current < 0.020:
            print(f"  ✓ Good match with 0.25mV step!")
        else:
            print(f"  ⚠️ Mismatch - VID_STEP may need adjustment")

        print("\n" + "="*50)
        print("Calculating VOUT_COMMAND for 0.7V Target")
        print("="*50)

        target_voltage = 0.7
        vid_code_700mv = int(target_voltage / VID_STEP_TSPCORE)

        print(f"Target voltage: {target_voltage}V")
        print(f"VID_STEP: {VID_STEP_TSPCORE:.10f}V (0.25mV)")
        print(f"VID code = {target_voltage}V / {VID_STEP_TSPCORE:.10f}V = {vid_code_700mv}")
        print(f"VID code hex: 0x{vid_code_700mv:03X}")
        print(f"VOUT_COMMAND value: 0x{vid_code_700mv:04X}")

        # Verify calculation
        verify_voltage = vid_code_700mv * VID_STEP_TSPCORE
        print(f"Verification: {vid_code_700mv} × {VID_STEP_TSPCORE:.10f}V = {verify_voltage:.6f}V")

        print("\n" + "="*50)
        print("Writing 0.7V to TSP_CORE")
        print("="*50)

        # Method 1: Direct write with calculated value
        print("\nMethod 1: Direct VOUT_COMMAND write")
        print(f"Writing 0x{vid_code_700mv:04X} to VOUT_COMMAND register...")

        i2c.i2c_write16PMBus(0, PMBusDict["VOUT_COMMAND"], vid_code_700mv)
        print("✓ Written")

        # Wait for voltage to settle
        print("Waiting for voltage to settle...")
        time.sleep(0.5)

        # Read back values
        vout_cmd_new = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
        vid_code_new = vout_cmd_new & 0xFFF
        calc_voltage_new = vid_code_new * VID_STEP_TSPCORE
        actual_voltage_new = i2c.Read_Vout_Rail1()

        print("\nReadback after write:")
        print(f"  VOUT_COMMAND: 0x{vout_cmd_new:04X}")
        print(f"  VID code: {vid_code_new} (0x{vid_code_new:03X})")
        print(f"  Expected VID code: {vid_code_700mv} (0x{vid_code_700mv:03X})")

        if vid_code_new == vid_code_700mv:
            print(f"  ✓ VID code matches expected value")
        else:
            print(f"  ⚠️ VID code mismatch!")

        print(f"  Calculated voltage: {calc_voltage_new:.6f}V")
        print(f"  Actual READ_VOUT: {actual_voltage_new:.6f}V")
        print(f"  Target voltage: {target_voltage}V")

        # Check if voltage is close to target
        error = abs(actual_voltage_new - target_voltage)
        print(f"  Error from target: {error*1000:.3f}mV")

        if error < 0.020:  # Within 20mV
            print(f"  ✓ Successfully set to {target_voltage}V!")
        else:
            print(f"  ⚠️ Voltage is {actual_voltage_new:.3f}V, expected ~{target_voltage}V")

        # Method 2: Using Write_Vout_Command function
        print("\n" + "-"*50)
        print("Method 2: Using Write_Vout_Command function")
        print("-"*50)

        success = i2c.Write_Vout_Command(0, 0.7)

        if success:
            print("✓ Write_Vout_Command executed")

            # Wait and read back
            time.sleep(0.5)

            vout_cmd_func = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
            vid_code_func = vout_cmd_func & 0xFFF
            actual_voltage_func = i2c.Read_Vout_Rail1()

            print(f"\nReadback after Write_Vout_Command:")
            print(f"  VOUT_COMMAND: 0x{vout_cmd_func:04X}")
            print(f"  VID code: {vid_code_func} (0x{vid_code_func:03X})")
            print(f"  Actual READ_VOUT: {actual_voltage_func:.6f}V")

            error_func = abs(actual_voltage_func - 0.7)
            if error_func < 0.020:
                print(f"  ✓ Successfully set to 0.7V using function!")
            else:
                print(f"  ⚠️ Voltage mismatch using function")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Aardvark adapter is connected.")

    print("\n" + "="*70)
    print("Test Summary")
    print("="*70)
    print(f"VID_STEP for TSP_CORE: 0.25mV")
    print(f"For 0.7V target:")
    print(f"  VID code: {vid_code_700mv} (0x{vid_code_700mv:03X})")
    print(f"  VOUT_COMMAND: 0x{vid_code_700mv:04X}")
    print("="*70)

if __name__ == "__main__":
    test_tspcore_07v()