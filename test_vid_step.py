#!/usr/bin/env python3
"""
Test VID_STEP = 0.9765625mV for both loops
"""

from powertool import PowerToolI2C, PMBusDict
import time

def test_vid_step():
    """Test VID_STEP with 0.9765625mV (1V/1024) for both loops"""

    print("="*70)
    print("VID_STEP Test with 0.9765625mV (1V/1024)")
    print("="*70)

    # Define the correct VID_STEP
    VID_STEP = 0.9765625 / 1000  # Convert mV to V = 0.0009765625V

    print(f"\nVID_STEP = 0.9765625mV = {VID_STEP:.10f}V")
    print(f"This is 1V/1024 = {1.0/1024:.10f}V\n")

    try:
        # Initialize I2C
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
            print(f"{name} (Page {page})")
            print(f"{'='*50}")

            # Read current VOUT_COMMAND
            try:
                vout_cmd_raw = i2c.i2c_read16PMBus(page, PMBusDict["VOUT_COMMAND"])
                vid_code = vout_cmd_raw & 0xFFF  # 12-bit VID code

                # Calculate voltage with correct VID_STEP
                calculated_voltage = vid_code * VID_STEP

                print(f"Current VOUT_COMMAND:")
                print(f"  Raw value: 0x{vout_cmd_raw:04X}")
                print(f"  VID code: {vid_code} (0x{vid_code:03X})")
                print(f"  Calculated voltage: {calculated_voltage:.6f}V")

                # Read actual voltage
                vout_actual = i2c.Read_Vout_Rail1() if page == 0 else i2c.Read_Vout_Rail2()
                print(f"  Actual READ_VOUT: {vout_actual:.6f}V")

                # Calculate difference
                diff = abs(vout_actual - calculated_voltage)
                print(f"  Difference: {diff*1000:.3f}mV")

                if diff < 0.050:  # Within 50mV
                    print(f"  ✓ Good match!")
                else:
                    print(f"  ⚠️ Large difference - may need adjustment")

            except Exception as e:
                print(f"  Error reading values: {e}")

        # Calculate for 0.6V target
        print(f"\n{'='*50}")
        print("Calculating VOUT_COMMAND for 0.6V target")
        print(f"{'='*50}")

        target_voltage = 0.6
        vid_code_600mv = int(target_voltage / VID_STEP)

        print(f"Target voltage: {target_voltage}V")
        print(f"VID_STEP: {VID_STEP:.10f}V")
        print(f"VID code = {target_voltage}V / {VID_STEP:.10f}V = {vid_code_600mv}")
        print(f"VID code hex: 0x{vid_code_600mv:03X}")
        print(f"VOUT_COMMAND value: 0x{vid_code_600mv:04X}")
        print(f"Verification: {vid_code_600mv} × {VID_STEP:.10f}V = {vid_code_600mv * VID_STEP:.6f}V")

        # Ask user if they want to test writing
        print(f"\n{'='*50}")
        response = input("Do you want to write 0.6V to TSP_CORE? (y/n): ")

        if response.lower() == 'y':
            print("\nWriting 0.6V to TSP_CORE...")

            # Use the Write_Vout_Command function which now uses correct VID_STEP
            success = i2c.Write_Vout_Command(0, 0.6)

            if success:
                print("✓ VOUT_COMMAND written")

                # Wait for voltage to settle
                time.sleep(0.5)

                # Read back
                vout_cmd_new = i2c.i2c_read16PMBus(0, PMBusDict["VOUT_COMMAND"])
                vid_code_new = vout_cmd_new & 0xFFF
                vout_actual_new = i2c.Read_Vout_Rail1()

                print(f"\nReadback after write:")
                print(f"  VOUT_COMMAND: 0x{vout_cmd_new:04X} (VID code: {vid_code_new})")
                print(f"  Calculated: {vid_code_new * VID_STEP:.6f}V")
                print(f"  Actual READ_VOUT: {vout_actual_new:.6f}V")

                if abs(vout_actual_new - 0.6) < 0.020:  # Within 20mV
                    print("  ✓ Successfully set to 0.6V!")
                else:
                    print(f"  ⚠️ Voltage is {vout_actual_new:.3f}V, expected ~0.6V")
            else:
                print("✗ Failed to write VOUT_COMMAND")

    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the Aardvark adapter is connected.")

    print("\n" + "="*70)
    print("Test complete")
    print("="*70)

if __name__ == "__main__":
    test_vid_step()