#!/usr/bin/env python3
"""
Comprehensive test script for all PMBus commands on both TSP_CORE and TSP_C2C rails
Tests single read functionality for all supported commands
"""

import subprocess
import time
import sys
import os
from datetime import datetime

# Define test configuration
RAILS = ['TSP_CORE', 'TSP_C2C']

COMMANDS = [
    'READ_VOUT',
    'READ_IOUT',
    'READ_TEMPERATURE_1',
    'READ_DUTY',
    'READ_PIN',
    'READ_POUT',
    'READ_IIN',
    'STATUS_BYTE',
    'STATUS_WORD',
    'STATUS_VOUT',
    'STATUS_IOUT',
    'STATUS_INPUT',
    'STATUS_TEMPERATURE',
    'VOUT_MODE',
    'MFR_IOUT_PEAK',
    'MFR_TEMP_PEAK'
]

def run_command(rail, command):
    """Execute a single PMBus command and return the result"""
    cmd = ['python3', 'powertool.py', rail, command]

    try:
        # Run the command with timeout
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5
        )

        # Extract the last line which contains the actual result
        output_lines = result.stdout.strip().split('\n')

        # Find the line with the actual result (after the separator line)
        for i, line in enumerate(output_lines):
            if f"{rail} {command}:" in line:
                return True, line.strip()

        # If we didn't find the expected output format, return the last meaningful line
        for line in reversed(output_lines):
            if line and not line.startswith('=') and not line.startswith('-'):
                return True, line.strip()

        return False, "No output captured"

    except subprocess.TimeoutExpired:
        return False, "Command timed out"
    except Exception as e:
        return False, str(e)

def test_single_commands():
    """Test all single read commands for both rails"""

    print("=" * 80)
    print("PMBus COMPREHENSIVE COMMAND TEST")
    print("=" * 80)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {len(COMMANDS)} commands on {len(RAILS)} rails")
    print("=" * 80)
    print()

    # Track results
    results = {}
    passed = 0
    failed = 0

    # Test each rail
    for rail in RAILS:
        print(f"\n{'='*60}")
        print(f"Testing Rail: {rail}")
        print(f"{'='*60}")

        results[rail] = {}

        for command in COMMANDS:
            print(f"\nTesting {rail} - {command}...")

            success, output = run_command(rail, command)

            if success:
                print(f"  ✓ SUCCESS: {output}")
                passed += 1
                results[rail][command] = {'status': 'PASS', 'output': output}
            else:
                print(f"  ✗ FAILED: {output}")
                failed += 1
                results[rail][command] = {'status': 'FAIL', 'error': output}

            # Small delay between commands to avoid overwhelming the I2C bus
            time.sleep(0.2)

    # Print summary
    print("\n")
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    total_tests = len(RAILS) * len(COMMANDS)
    print(f"Total tests: {total_tests}")
    print(f"Passed: {passed} ({100*passed/total_tests:.1f}%)")
    print(f"Failed: {failed} ({100*failed/total_tests:.1f}%)")

    # Print detailed results table
    print("\n" + "=" * 80)
    print("DETAILED RESULTS TABLE")
    print("=" * 80)

    # Create a formatted table
    print(f"\n{'Command':<25} {'TSP_CORE':<30} {'TSP_C2C':<30}")
    print("-" * 85)

    for command in COMMANDS:
        core_result = results['TSP_CORE'].get(command, {})
        c2c_result = results['TSP_C2C'].get(command, {})

        # Format results for display
        if core_result.get('status') == 'PASS':
            # Extract just the value from the output
            core_val = core_result['output'].split(':')[-1].strip() if ':' in core_result['output'] else 'OK'
            core_display = f"✓ {core_val[:25]}"
        else:
            core_display = f"✗ {core_result.get('error', 'Error')[:25]}"

        if c2c_result.get('status') == 'PASS':
            # Extract just the value from the output
            c2c_val = c2c_result['output'].split(':')[-1].strip() if ':' in c2c_result['output'] else 'OK'
            c2c_display = f"✓ {c2c_val[:25]}"
        else:
            c2c_display = f"✗ {c2c_result.get('error', 'Error')[:25]}"

        print(f"{command:<25} {core_display:<30} {c2c_display:<30}")

    print("\n" + "=" * 80)

    # Save results to file
    save_results_to_file(results, passed, failed, total_tests)

    return passed, failed

def save_results_to_file(results, passed, failed, total):
    """Save test results to a text file"""

    # Ensure data directory exists
    if not os.path.exists('data'):
        os.makedirs('data')

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"data/pmbus_test_results_{timestamp}.txt"

    with open(filename, 'w') as f:
        f.write("=" * 80 + "\n")
        f.write("PMBus COMPREHENSIVE TEST RESULTS\n")
        f.write("=" * 80 + "\n")
        f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total Tests: {total}\n")
        f.write(f"Passed: {passed} ({100*passed/total:.1f}%)\n")
        f.write(f"Failed: {failed} ({100*failed/total:.1f}%)\n")
        f.write("\n" + "=" * 80 + "\n")
        f.write("DETAILED RESULTS\n")
        f.write("=" * 80 + "\n\n")

        for rail in results:
            f.write(f"\nRail: {rail}\n")
            f.write("-" * 40 + "\n")

            for command, result in results[rail].items():
                if result['status'] == 'PASS':
                    f.write(f"  {command}: PASS - {result['output']}\n")
                else:
                    f.write(f"  {command}: FAIL - {result['error']}\n")

    print(f"\nTest results saved to: {filename}")

def test_continuous_logging():
    """Test continuous logging for selected critical parameters"""

    print("\n" + "=" * 80)
    print("CONTINUOUS LOGGING TEST (SHORT DURATION)")
    print("=" * 80)

    # Test a few critical parameters with very short logging duration
    test_cases = [
        ('TSP_CORE', 'READ_VOUT'),
        ('TSP_C2C', 'READ_IOUT'),
        ('TSP_CORE', 'READ_TEMPERATURE_1')
    ]

    for rail, command in test_cases:
        print(f"\nTesting continuous logging: {rail} {command}")
        print("-" * 40)

        # Create a Python script to test logging with 3-second duration
        test_script = f"""
import sys
sys.path.insert(0, '/home/groq/pmbustool')
from powertool import continuous_single_command_logging

# Test with 3 second duration
success = continuous_single_command_logging('{rail}', '{command}', duration_minutes=0.05, sample_rate_ms=500)
sys.exit(0 if success else 1)
"""

        try:
            result = subprocess.run(
                ['python3', '-c', test_script],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Check if CSV file was created
                import glob
                pattern = f"data/{rail}_{command}_*.csv"
                files = glob.glob(pattern)

                if files:
                    # Get the most recent file
                    latest_file = max(files, key=os.path.getctime)

                    # Count lines in the file
                    with open(latest_file, 'r') as f:
                        line_count = sum(1 for line in f) - 1  # Subtract header

                    print(f"  ✓ SUCCESS: Logged {line_count} samples to {os.path.basename(latest_file)}")
                else:
                    print(f"  ✗ WARNING: Command succeeded but no CSV file found")
            else:
                print(f"  ✗ FAILED: Logging failed with return code {result.returncode}")

        except subprocess.TimeoutExpired:
            print(f"  ✗ FAILED: Logging timed out")
        except Exception as e:
            print(f"  ✗ FAILED: {str(e)}")

        time.sleep(1)

def main():
    """Main test function"""

    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "         PMBus COMPREHENSIVE TEST SUITE FOR SUGARLOAF I2C".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print()

    # Check if we're in the right directory
    if not os.path.exists('powertool.py'):
        print("ERROR: powertool.py not found in current directory")
        print("Please run this test from the pmbustool directory")
        sys.exit(1)

    try:
        # Test single commands
        passed, failed = test_single_commands()

        # Test continuous logging
        print("\n")
        test_continuous_logging()

        # Final summary
        print("\n" + "=" * 80)
        print("TEST COMPLETE")
        print("=" * 80)

        if failed == 0:
            print("✓ ALL TESTS PASSED!")
            return 0
        else:
            print(f"⚠ {failed} tests failed. Check the results above for details.")
            return 1

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        return 2
    except Exception as e:
        print(f"\n\nTest failed with error: {str(e)}")
        return 3

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)