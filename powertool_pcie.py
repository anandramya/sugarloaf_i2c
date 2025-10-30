#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMBus Tool for PCIe I2C Access
Uses i2c tool binary to access PMBus devices via PCIe address
Example PCIe address: c1:00.0
"""

import subprocess
import json
import sys
import os
import time
import argparse
import csv
import datetime

# Import common PMBus functions and register definitions
from pmbus_common import (PMBusDict, PMBusCommands,
                          format_status_word, decode_status_word,
                          format_status_vout, decode_status_vout,
                          format_status_iout, decode_status_iout)

# Default configuration
PCIE_DEVICE = "0000:c1:00.0"  # Default PCIe address (full format with domain)
SLAVE_ADDR = 0x5C             # Default PMBus device I2C address
I2C_BUS_NUM = 1               # I2C bus number (use 1 for this hardware)
I2C_TOOL_PATH = "./i2ctool"   # Path to i2c tool binary

# Ensure data directory exists
DATA_DIR = "data"
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
    print(f"✓ Created {DATA_DIR}/ directory for CSV logging")


class PowerToolPCIe(PMBusCommands):
    """PMBus tool using PCIe-based I2C access via i2c tool binary"""

    def __init__(self, pcie_device=PCIE_DEVICE, i2c_addr=SLAVE_ADDR,
                 bus_num=I2C_BUS_NUM, i2c_tool_path=I2C_TOOL_PATH):
        """
        Initialize PCIe I2C tool

        Args:
            pcie_device: PCIe address (e.g., "0000:c1:00.0")
            i2c_addr: I2C slave address (e.g., 0x5C)
            bus_num: I2C bus number (None to omit parameter)
            i2c_tool_path: Path to i2c tool binary
        """
        self.pcie_device = pcie_device
        self.i2c_addr = i2c_addr
        self.bus_num = bus_num
        self.i2c_tool_path = i2c_tool_path

        # Verify i2c tool exists
        if not os.path.exists(self.i2c_tool_path):
            raise FileNotFoundError(
                f"i2c tool binary not found at: {self.i2c_tool_path}\n"
                f"Please ensure the binary is in the current directory or update I2C_TOOL_PATH"
            )

        print(f"✓ Initialized PCIe I2C tool")
        print(f"  PCIe Device: {self.pcie_device}")
        print(f"  I2C Address: 0x{self.i2c_addr:02X}")
        print(f"  I2C Bus: {self.bus_num}")

    def _run_i2c_command(self, cmd_args, verbose=False):
        """
        Run i2c tool binary with given arguments

        Args:
            cmd_args: List of command arguments
            verbose: Print command being run

        Returns:
            Command output as string
        """
        cmd = [self.i2c_tool_path] + cmd_args

        if verbose:
            print(f"Running: {' '.join(cmd)}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5.0
            )

            if result.returncode != 0:
                raise RuntimeError(
                    f"i2c tool command failed:\n"
                    f"Command: {' '.join(cmd)}\n"
                    f"Error: {result.stderr}"
                )

            return result.stdout

        except subprocess.TimeoutExpired:
            raise RuntimeError(f"i2c tool command timed out: {' '.join(cmd)}")
        except FileNotFoundError:
            raise RuntimeError(f"i2c tool binary not found: {self.i2c_tool_path}")

    def i2c_read_bytes(self, reg_addr, length=2, page=None, reg_addr_len=1):
        """
        Read bytes from I2C register

        Args:
            reg_addr: Register address
            length: Number of bytes to read (1 or 2)
            page: PMBus page (0 or 1), if None no page setting
            reg_addr_len: Byte size of register address (1 or 2)

        Returns:
            Integer value read from register
        """
        # Set page if specified
        if page is not None:
            self.i2c_write_bytes(PMBusDict["PAGE"], page, length=1)
            time.sleep(0.01)  # Small delay after page write

        # Build command arguments
        cmd_args = [
            "-d", self.pcie_device,
            "-a", str(self.i2c_addr),
            "-r", str(reg_addr),
            "-t", "pmbus",
            "-l", str(length),
            "--reg-addr-len", str(reg_addr_len),
            "-b", str(self.bus_num),
            "-j", "/tmp/i2c_read.json"  # Save to JSON for parsing
        ]

        output = self._run_i2c_command(cmd_args)

        # Parse JSON output
        try:
            with open("/tmp/i2c_read.json", "r") as f:
                data = json.load(f)

            # Extract value from JSON
            # The structure may vary, adjust as needed based on actual tool output
            if isinstance(data, dict) and "value" in data:
                value = data["value"]
            elif isinstance(data, list) and len(data) > 0:
                # If it's a list of bytes, combine them
                value = 0
                for i, byte_val in enumerate(data):
                    value |= (byte_val << (i * 8))
            else:
                # Try to parse the output directly
                value = int(output.strip(), 0)

            return value

        except (FileNotFoundError, json.JSONDecodeError, ValueError) as e:
            # Fallback: try to parse output directly
            try:
                # Look for hex value in output
                import re
                hex_match = re.search(r'0x[0-9a-fA-F]+', output)
                if hex_match:
                    return int(hex_match.group(), 16)
                # Look for decimal value
                dec_match = re.search(r'\d+', output)
                if dec_match:
                    return int(dec_match.group())
            except:
                pass

            raise RuntimeError(f"Failed to parse i2c tool output: {output}\nError: {e}")

    def i2c_write_bytes(self, reg_addr, value, length=2, page=None, reg_addr_len=1):
        """
        Write bytes to I2C register

        Args:
            reg_addr: Register address
            value: Value to write
            length: Number of bytes to write (1 or 2)
            page: PMBus page (0 or 1), if None no page setting
            reg_addr_len: Byte size of register address (1 or 2)
        """
        # For page writes, don't set page recursively
        if page is not None and reg_addr != PMBusDict["PAGE"]:
            self.i2c_write_bytes(PMBusDict["PAGE"], page, length=1)
            time.sleep(0.01)

        # Build command arguments
        cmd_args = [
            "-d", self.pcie_device,
            "-a", str(self.i2c_addr),
            "-r", str(reg_addr),
            "-t", "pmbus",
            "-b", str(self.bus_num),
            "-w", str(value),
            "--write-len", str(length),
            "--reg-addr-len", str(reg_addr_len)
        ]

        self._run_i2c_command(cmd_args)
        time.sleep(0.01)  # Small delay after write

    def i2c_read8PMBus(self, page, reg_addr):
        """Read single byte from PMBus register"""
        return self.i2c_read_bytes(reg_addr, length=1, page=page)

    def i2c_read16PMBus(self, page, reg_addr):
        """Read 16-bit word from PMBus register"""
        return self.i2c_read_bytes(reg_addr, length=2, page=page)

    def i2c_write8PMBus(self, reg_addr, value):
        """Write single byte to PMBus register"""
        self.i2c_write_bytes(reg_addr, value, length=1)

    def i2c_write16PMBus(self, page, reg_addr, value):
        """Write 16-bit word to PMBus register"""
        self.i2c_write_bytes(reg_addr, value, length=2, page=page)

    # All PMBus command methods (Read_Vout, Read_Iout, Read_Temp, Read_Die_Temp,
    # Read_Status_Word, Write_Vout_Command, etc.) are inherited from PMBusCommands mixin


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="PMBus Tool for PCIe I2C Access",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simple format (like serial tool)
  %(prog)s 0x5C TSP_CORE VOUT IOUT TEMP DIE_TEMP STATUS_WORD
  %(prog)s 0x5C TSP_CORE VOUT IOUT TEMP DIE_TEMP STATUS_WORD log
  %(prog)s 0x5C TSP_C2C VOUT IOUT log

  # Original format
  %(prog)s --rail TSP_CORE --cmd READ_VOUT
  %(prog)s --rail TSP_C2C --cmd READ_IOUT
  %(prog)s --test
        """
    )

    # Positional arguments (optional, for simple command format)
    parser.add_argument("positional", nargs='*',
                       help="[I2C_ADDR] RAIL COMMAND1 [COMMAND2 ...] [log]")

    # Optional named arguments
    parser.add_argument("-d", "--device", default=PCIE_DEVICE,
                       help=f"PCIe device address (default: {PCIE_DEVICE})")
    parser.add_argument("-a", "--addr", type=lambda x: int(x, 0), default=None,
                       help=f"I2C slave address (default: 0x{SLAVE_ADDR:02X})")
    parser.add_argument("-b", "--bus", type=int, default=I2C_BUS_NUM,
                       help=f"I2C bus number (default: {I2C_BUS_NUM})")
    parser.add_argument("--i2c-tool", default=I2C_TOOL_PATH,
                       help=f"Path to i2c tool binary (default: {I2C_TOOL_PATH})")
    parser.add_argument("--rail", choices=["TSP_CORE", "TSP_C2C"],
                       help="PMBus rail to access")
    parser.add_argument("--cmd",
                       help="PMBus command (e.g., READ_VOUT, READ_IOUT, VOUT_COMMAND)")
    parser.add_argument("--value", type=float,
                       help="Value for write commands (e.g., voltage setpoint)")
    parser.add_argument("--test", action="store_true",
                       help="Run test mode - read both rails")
    parser.add_argument("--samples", type=int, default=0,
                       help="Number of samples to log (0 = infinite, Ctrl+C to stop)")
    parser.add_argument("--interval", type=float, default=1.0,
                       help="Logging interval in seconds (default: 1.0)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")

    args = parser.parse_args()

    # Parse positional arguments (simple format: [PCIE_ADDR] [I2C_ADDR] RAIL CMD1 [CMD2 ...] [log])
    rail_name = None
    commands = []
    enable_log = False
    i2c_addr = args.addr if args.addr is not None else SLAVE_ADDR
    pcie_addr = args.device

    if args.positional:
        pos_args = args.positional[:]

        # Check if first argument is PCIe address (format: 0000:c1:00.0 or c1:00.0)
        if pos_args and ':' in pos_args[0]:
            pcie_addr = pos_args[0]
            if not pcie_addr.startswith('0000:'):
                pcie_addr = '0000:' + pcie_addr
            pos_args = pos_args[1:]

        # Check if next argument is I2C address (starts with 0x)
        if pos_args and pos_args[0].lower().startswith('0x'):
            i2c_addr = int(pos_args[0], 16)
            pos_args = pos_args[1:]

        # Next should be rail name
        if pos_args and pos_args[0].upper() in ['TSP_CORE', 'TSP_C2C']:
            rail_name = pos_args[0].upper()
            pos_args = pos_args[1:]

        # Check if last argument is 'log'
        if pos_args and pos_args[-1].lower() == 'log':
            enable_log = True
            pos_args = pos_args[:-1]

        # Remaining arguments are commands
        commands = [cmd.upper() for cmd in pos_args]

        # Normalize command names (add READ_ prefix if needed)
        normalized_commands = []
        for cmd in commands:
            if cmd in ['VOUT', 'IOUT', 'TEMP']:
                normalized_commands.append(f'READ_{cmd}')
            elif cmd == 'DIE_TEMP':
                normalized_commands.append('READ_DIE_TEMP')
            elif cmd == 'STATUS' or cmd == 'WORD' or cmd == 'STATUS_WORD':
                normalized_commands.append('STATUS_WORD')
            else:
                normalized_commands.append(cmd)
        commands = normalized_commands

    # Use named arguments if provided
    if args.rail:
        rail_name = args.rail
    if args.cmd:
        commands = [args.cmd.upper()]

    # Update device and addr from positional parsing
    args.device = pcie_addr
    if i2c_addr != SLAVE_ADDR:
        args.addr = i2c_addr
    elif args.addr is None:
        args.addr = SLAVE_ADDR

    # Initialize tool
    try:
        pt = PowerToolPCIe(
            pcie_device=args.device,
            i2c_addr=args.addr,
            bus_num=args.bus,
            i2c_tool_path=args.i2c_tool
        )
    except Exception as e:
        print(f"Error initializing PCIe I2C tool: {e}", file=sys.stderr)
        return 1

    # Test mode
    if args.test:
        print("\n" + "="*60)
        print("PMBus Test Mode - Reading Both Rails")
        print("="*60)

        for rail_name, page in [("TSP_CORE", 0), ("TSP_C2C", 1)]:
            print(f"\n{rail_name} (Page {page}):")
            print("-"*60)

            try:
                vout = pt.Read_Vout(page)
                print(f"  VOUT:        {vout:.4f} V")
            except Exception as e:
                print(f"  VOUT:        Error - {e}")

            try:
                iout = pt.Read_Iout(page)
                print(f"  IOUT:        {iout:.2f} A")
            except Exception as e:
                print(f"  IOUT:        Error - {e}")

            try:
                temp = pt.Read_Temp(page)
                print(f"  TEMP:        {temp:.1f} °C")
            except Exception as e:
                print(f"  TEMP:        Error - {e}")

            try:
                status = pt.Read_Status_Word(page)
                print(f"  STATUS_WORD: 0x{status:04X}")
                # Decode and show status bits
                decoded = decode_status_word(status)
                active_faults = [name for name, info in decoded['bits'].items()
                                if info['active'] and name not in ['RESERVED_9', 'RESERVED_10']]
                if active_faults:
                    print(f"    Active: {', '.join(active_faults)}")
            except Exception as e:
                print(f"  STATUS_WORD: Error - {e}")

        print("\n" + "="*60)
        print("✓ Test completed")
        return 0

    # Multi-command mode (positional arguments)
    if commands and rail_name:
        page = 0 if rail_name == "TSP_CORE" else 1

        # Logging mode
        if enable_log:
            # Generate CSV filename
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            cmd_names = '_'.join(commands[:3])  # Use first 3 commands in filename
            if len(commands) > 3:
                cmd_names += '_etc'
            csv_file = f"{DATA_DIR}/{rail_name}_{cmd_names}_{timestamp}.csv"

            print(f"\n{'='*70}")
            print(f"PMBus Logging - {rail_name}")
            print(f"{'='*70}")
            print(f"Commands: {', '.join(commands)}")
            print(f"Samples: {'Infinite (Ctrl+C to stop)' if args.samples == 0 else args.samples}")
            print(f"Interval: {args.interval}s")
            print(f"Output: {csv_file}")
            print(f"{'='*70}\n")

            # Create CSV file with headers
            with open(csv_file, 'w', newline='') as f:
                writer = csv.writer(f)
                headers = ['timestamp', 'sample_num'] + commands
                writer.writerow(headers)

            sample_num = 0
            start_time = time.time()

            try:
                while True:
                    sample_num += 1
                    elapsed = time.time() - start_time

                    # Read data
                    row = [f"{elapsed:.3f}", sample_num]

                    for cmd in commands:
                        try:
                            if cmd == 'READ_VOUT':
                                value = pt.Read_Vout(page)
                            elif cmd == 'READ_IOUT':
                                value = pt.Read_Iout(page)
                            elif cmd == 'READ_TEMP':
                                value = pt.Read_Temp(page)
                            elif cmd == 'READ_DIE_TEMP':
                                value = pt.Read_Die_Temp(page)
                            elif cmd == 'STATUS_WORD':
                                value = f"0x{pt.Read_Status_Word(page):04X}"
                            else:
                                value = "N/A"
                            row.append(value)
                        except Exception as e:
                            row.append(f"Error: {e}")

                    # Write to CSV
                    with open(csv_file, 'a', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(row)

                    # Print progress
                    values_str = ' | '.join([f"{row[i+2]}" if isinstance(row[i+2], str) else f"{row[i+2]:.4f}"
                                              for i in range(len(commands))])
                    print(f"Sample {sample_num:4d} | Time: {elapsed:7.2f}s | {values_str}")

                    # Check if we've reached the sample limit
                    if args.samples > 0 and sample_num >= args.samples:
                        break

                    # Wait for next sample
                    time.sleep(args.interval)

            except KeyboardInterrupt:
                print(f"\n\n{'='*70}")
                print(f"Logging stopped by user (Ctrl+C)")
                print(f"{'='*70}")

            print(f"\nLogged {sample_num} samples to: {csv_file}")
            print(f"Total time: {time.time() - start_time:.2f}s")
            return 0

        # Single read mode (no logging)
        else:
            print(f"\n{rail_name} (Page {page}):")
            print("-" * 60)

            for cmd in commands:
                try:
                    if cmd == 'READ_VOUT':
                        vout = pt.Read_Vout(page)
                        print(f"  VOUT:     {vout:.4f} V")
                    elif cmd == 'READ_IOUT':
                        iout = pt.Read_Iout(page)
                        print(f"  IOUT:     {iout:.2f} A")
                    elif cmd == 'READ_TEMP':
                        temp = pt.Read_Temp(page)
                        print(f"  TEMP:     {temp:.1f} °C")
                    elif cmd == 'READ_DIE_TEMP':
                        die_temp = pt.Read_Die_Temp(page)
                        print(f"  DIE_TEMP: {die_temp:.1f} °C")
                    elif cmd == 'STATUS_WORD':
                        status = pt.Read_Status_Word(page)
                        print(f"  STATUS:   0x{status:04X}")
                except Exception as e:
                    print(f"  {cmd}: Error - {e}")

            return 0

    # Old-style command mode (--rail and --cmd) - maintain backward compatibility
    if args.rail and args.cmd:
        page = 0 if args.rail == "TSP_CORE" else 1
        cmd = args.cmd.upper()

    try:
        # Read commands
        if cmd == "READ_VOUT":
            vout = pt.Read_Vout(page)
            print(f"{args.rail} VOUT: {vout:.4f} V")

        elif cmd == "READ_IOUT":
            iout = pt.Read_Iout(page)
            print(f"{args.rail} IOUT: {iout:.2f} A")

        elif cmd == "READ_TEMP":
            temp = pt.Read_Temp(page)
            print(f"{args.rail} TEMP: {temp:.1f} °C")

        elif cmd == "READ_DIE_TEMP":
            die_temp = pt.Read_Die_Temp(page)
            print(f"{args.rail} DIE_TEMP: {die_temp:.1f} °C")

        elif cmd == "STATUS_WORD" or cmd == "READ_STATUS":
            status = pt.Read_Status_Word(page)
            print(format_status_word(status, show_all=True))

        elif cmd == "STATUS_VOUT":
            status_vout = pt.i2c_read8PMBus(page, PMBusDict["STATUS_VOUT"])
            print(format_status_vout(status_vout, show_all=True))

        elif cmd == "STATUS_IOUT":
            status_iout = pt.i2c_read8PMBus(page, PMBusDict["STATUS_IOUT"])
            print(format_status_iout(status_iout, show_all=True))

        elif cmd == "IOUT_OC_WARN_LIMIT":
            if args.value is not None:
                # Write mode
                pt.Write_IOUT_OC_WARN_LIMIT(page, args.value)
            else:
                # Read mode
                warn_limit = pt.Read_IOUT_OC_WARN_LIMIT(page)
                iout_scale = pt.Read_IOUT_Scale(page)
                print(f"IOUT_OC_WARN_LIMIT: {warn_limit:.1f} A")
                print(f"  IOUT_SCALE: {iout_scale}")
                print(f"  LSB: {8 * iout_scale} A")

        # Write commands
        elif cmd == "VOUT_COMMAND":
            if args.value is None:
                print("Error: --value required for VOUT_COMMAND", file=sys.stderr)
                return 1
            pt.Write_Vout_Command(page, args.value)

        else:
            print(f"Error: Unknown command '{cmd}'", file=sys.stderr)
            print("Supported commands: READ_VOUT, READ_IOUT, READ_TEMP, READ_DIE_TEMP")
            print("                    STATUS_WORD, STATUS_VOUT, STATUS_IOUT")
            print("                    IOUT_OC_WARN_LIMIT, VOUT_COMMAND")
            return 1

    except Exception as e:
        print(f"Error executing command: {e}", file=sys.stderr)
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
