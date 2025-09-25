#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PMBus Rail Monitor for MP29816-C Controller
Supports direct register access, monitoring, and voltage control
"""

import time
import sys
import math
import csv
import datetime
import os
import argparse

from aardvark_py import *

# PMBus register definitions
PMBusDict = {
    # Standard PMBus Commands
    "PAGE": 0x00,
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
    "READ_TEMPERATURE_1": 0x8D,
    "READ_DUTY": 0x94,
    "READ_PIN": 0x97,
    "READ_POUT": 0x96,
    "READ_IIN": 0x89,
    "FREQUENCY_SWITCH": 0x33,
    "VOUT_DROOP": 0x28,

    # MFR Specific Commands
    "MFR_VR_CONFIG": 0x67,  # Contains IOUT_SCALE_BIT in bits [2:0]
    "MFR_VID_RES_R1": 0x29, # VID resolution register for Rail1 (VID_STEP in bits [12:10])
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

SLAVE_ADDR 	= 0x5C
I2C_BITRATE = 400 # kHz
ENDIAN = 0 # Little endian; 1 = Big endian


class PowerToolI2C (object) :

    def __init__(self):

        self.aardvark = self.aardvark_setup()


    def aardvark_setup(self):

        # Number of aardvark devices attached
        numAardvark = aa_find_devices(1)[0]

        if numAardvark == 0:
            print('ERROR: Could not find an aardvark device.')
            sys.exit(0)
        elif numAardvark > 1:
            print(""" WARNING:  Multiple aardvark devices found. It is recommended
                                        to plug only the device you expect to use with
                                        this script """)
        handle = aa_open(0)
        aa_i2c_free_bus(handle)
        aa_i2c_bitrate(handle, I2C_BITRATE)
        aa_i2c_pullup(handle, AA_I2C_PULLUP_BOTH)
        aa_configure(handle, AA_CONFIG_SPI_I2C)

        return handle


    def i2c_write16(self, addr1,addr2, data):
        i2c_reg = [0] * 6	# 5 bytes for the address and 4 for data

        # Split the 32-bit address into 5 bytes
        address1 = self.setIndirectDataBuffer2(addr1)

        address2 = self.setIndirectDataBuffer2(addr2)
        # print 'Address buffer is %s' % addressBuf
        dataBuf = self.setIndirectDataBuffer2(data)
        # print 'Data buffer is %s' % dataBuf

        i2c_reg = address1+ address2 + dataBuf
        # print 'i2c_reg is %s' % i2c_reg

        i2c_array = array('B', i2c_reg)

        resp = 0

        # Write address to the salve
        while resp == 0:
            resp = aa_i2c_write(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_array)


    def i2c_write16PMBus(self,page, reg_addr, data):


        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        i2c_reg = [0] * 3	# 5 bytes for the address and 4 for data

        # Split the 32-bit address into 5 bytes
        addressBuf = self.setIndirectDataBuffer(reg_addr)
        # print 'Address buffer is %s' % addressBuf
        dataBuf = self.setIndirectDataBuffer2(data)
        # print 'Data buffer is %s' % dataBuf

        i2c_reg = addressBuf + dataBuf
        # print 'i2c_reg is %s' % i2c_reg

        i2c_array = array('B', i2c_reg)
        resp = 0

        # Write address to the salve
        while resp == 0:
            resp = aa_i2c_write(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_array)

    def i2c_write8PMBus(self, reg_addr, data):

        i2c_reg = [0] * 2	# 5 bytes for the address and 4 for data

        # Split the 32-bit address into 5 bytes
        addressBuf = self.setIndirectDataBuffer(reg_addr)
        # print 'Address buffer is %s' % addressBuf
        dataBuf = self.setIndirectDataBuffer(data)
        # print 'Data buffer is %s' % dataBuf

        i2c_reg = addressBuf + dataBuf
        # print 'i2c_reg is %s' % i2c_reg

        i2c_array = array('B', i2c_reg)

        resp = 0

        # Write address to the salve
        while resp == 0:
            resp = aa_i2c_write(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_array)

    def i2c_read8PMBus(self, page, reg_addr):
        """Read a single byte from PMBus register"""
        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        # Create register address buffer
        addressBuf = self.setIndirectDataBuffer(reg_addr)
        i2c_reg = array('B', addressBuf)

        # Read single byte
        (count, data1, data_read, data2) = aa_i2c_write_read(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_reg, 1)

        # Return the single byte
        if len(data_read) > 0:
            return data_read[0]
        else:
            raise Exception(f"Failed to read from register 0x{reg_addr:02X}")

    def i2c_writePMBus_cmd_only(self, page, reg_addr):


        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        i2c_reg = [0] * 2	# 5 bytes for the address and 4 for data

        # Split the 32-bit address into 5 bytes
        addressBuf = self.setIndirectDataBuffer(reg_addr)
        # print 'Address buffer is %s' % addressBuf

        i2c_reg = addressBuf
        # print 'i2c_reg is %s' % i2c_reg

        i2c_array = array('B', i2c_reg)

        resp = 0

        # Write address to the salve
        while resp == 0:
            resp = aa_i2c_write(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_array)

    def i2c_read16(self, addr1 , addr2):

        # Split the 32-bit address into 5 bytes
        address1 = self.setIndirectDataBuffer(addr1)

        address2 = self.setIndirectDataBuffer2(addr2)

        i2c_reg = address1 + address2

        i2c_reg = array('B',i2c_reg)

        count= 0

        (count, data1, data_read, data2) = aa_i2c_write_read(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_reg, 2)

        #print data1
        #print data_read
        #print data2

        # return data converted to big endian format
        return self.byteArrayToLittleEndian(data_read.tolist())

    def i2c_read16PMBus(self, page, reg_addr):

        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        # Split the 32-bit address into 5 bytes
        addressBuf = self.setIndirectDataBuffer(reg_addr)

        i2c_reg = array('B', addressBuf)

        resp = 0

        # Write address to the salve

        #while resp == 0:
            #resp = aa_i2c_write(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_reg)

        # Read data back
        count = 0

        (count,data1,data_read, data2) = aa_i2c_write_read(self.aardvark, SLAVE_ADDR, AA_I2C_NO_FLAGS, i2c_reg, 2)

        #print data1
        #print data2
        #print data_read
        # return data converted to big endian format
        return self.byteArrayToLittleEndian(data_read.tolist())

       # Assume 32-bit data
    def setIndirectDataBuffer4(self, data):
        dataBuf = [None] * 4

        # Inherently reverses the byte order
        # if data = 0x11223344, dataBuf = [44 33 22 11]
        dataBuf[0] = data & 0xFF
        dataBuf[1] = (data >> 8) & 0xFF
        dataBuf[2] = (data >> 16) & 0xFF
        dataBuf[3] = (data >> 24) & 0xFF

        return dataBuf

    def setIndirectDataBuffer2(self, data):

        dataBuf = [None] * 2

        # Inherently reverses the byte order
        # if data = 0x11223344, dataBuf = [44 33 22 11]
        dataBuf[0] = data & 0xFF
        dataBuf[1] = (data >> 8) & 0xFF

        return dataBuf
    def setIndirectDataBuffer(self, data):
        dataBuf = [None] * 1

        # Inherently reverses the byte order
        # if data = 0x11223344, dataBuf = [44 33 22 11]
        dataBuf[0] = data & 0xFF


        return dataBuf

    def byteArrayToLittleEndian(self, data_array):
        data_array.reverse()

        returnArray = ['%02x' % x for x in data_array];

        # Check if array is empty before convering!
        # Join all elements in the array and represent it as a single hex number
        dataval = int(''.join(returnArray), 16)
        # ['00', '52', '93', '05'] --> 0x5935200

        return dataval

    def SetRegister_bit(self, Regadd, bitposition):

        RegData = self.i2c_read32(Regadd)

        RegData = RegData|(1<<bitposition)

        self.i2c_write32(Regadd, RegData)

    def ResetRegister_bit(self, Regadd, bitposition):

        RegData_read = self.i2c_read32(Regadd)

        RegData = ~(RegData_read&(1<<bitposition))

        RegData = RegData&RegData_read

        self.i2c_write32(Regadd, RegData)

    def Isbitset(self, Regadd, bitposition):

        RegData = self.i2c_read32(Regadd)
        RegMask = RegData & (1<<bitposition)

        Output = RegMask >> bitposition

        return Output

    def AppendRegister(self, Regadd, data):

        Regdata = self.i2c_read32(Regadd)

        Regdata = Regdata|data

        self.i2c_write32(Regadd, Regdata)

    def ReadRegister_range(self, Regadd, startbit, stopbit):

        Regdata = self.i2c_read32(Regadd)
        Regmask_one = int(math.pow(2,(stopbit-startbit)+1)-1)
        output = (Regdata&(Regmask_one<<startbit))>>startbit
        return output

    def WriteRegister_range(self, Regadd, startbit, stopbit, data):

        self.i2c_write32(Regadd, data)


    def WriteRegister_range_PL(self, Regadd, startbit, stopbit, data):

        Regdata = self.i2c_read32(Regadd)
        # print(bin(Regdata))
        Regmask_one = int(math.pow(2, (stopbit - startbit) + 1) - 1)
        # print(bin(Regmask_one))
        Regmask_zero = ~Regmask_one
        # print(bin(Regmask_zero))
        Output1 = Regdata & Regmask_zero
        # print(bin(Output1))
        Output = Output1 | data
        # print(bin(Output))
        # print("data")
        # print(bin(data))
        self.i2c_write32(Regadd, Output)


    def WriteRegister_range_PR(self, Regadd, startbit, stopbit, data):

        Regdata = self.i2c_read32(Regadd)
        #print(bin(Regdata))
        Regmask_begin = int(math.pow(2,startbit)-1)
        #print(Regmask_begin)
        Output1 = Regdata&Regmask_begin
        #print("output1")
        #print(bin(Output1))
        Output = Output1|(data<<startbit)
        #print(bin(Output))
        #print("data")
        #print(bin(data))
        self.i2c_write32(Regadd, Output)



    def conv2hex(self, input):

        return hex(input)

    def dec2bin(self, input):

        return bin(input)

    def Read_Vout(self,page):

        data= self.i2c_read16PMBus(page, PMBusDict["READ_VOUT"])

        #print(data)
        #print(type(data))

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(page)
        except:
            exponent = -10  # Default for many VR controllers

        # Linear16 format: mantissa * 2^exponent
        vout = data * math.pow(2, exponent)

        print("Vout=" , vout)
        return vout

    def Read_VOUT_MODE(self, page):
        """Read VOUT_MODE register to determine the data format"""
        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        # Read VOUT_MODE as a byte
        mode = self.i2c_read16PMBus(page, PMBusDict["VOUT_MODE"]) & 0xFF

        # Extract the exponent (5-bit two's complement in bits 0-4)
        exponent = mode & 0x1F

        # Convert from two's complement if negative
        if exponent & 0x10:  # If bit 4 is set, it's negative
            exponent = exponent - 32

        return exponent

    def Read_Vout_Rail1(self):
        """Read VOUT for Rail1 (Page 0) at slave address 0x5C"""
        # Ensure we're on page 0 for Rail1
        self.i2c_write8PMBus(PMBusDict["PAGE"], 0)

        # Read the raw VOUT data
        data = self.i2c_read16PMBus(0, PMBusDict["READ_VOUT"])

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(0)
        except:
            exponent = -10  # Default for many VR controllers

        # Linear16 format: mantissa * 2^exponent
        vout = data * math.pow(2, exponent)

        return vout

    def Read_Vout_Rail2(self):
        """Read VOUT for Rail2 (Page 1) at slave address 0x5C"""
        # Switch to page 1 for Rail2
        self.i2c_write8PMBus(PMBusDict["PAGE"], 1)

        # Read the raw VOUT data
        data = self.i2c_read16PMBus(1, PMBusDict["READ_VOUT"])

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(1)
        except:
            exponent = -10  # Default for many VR controllers

        # Linear16 format: mantissa * 2^exponent
        vout = data * math.pow(2, exponent)

        return vout

    def Read_VID_Resolution(self, page):
        """Read VID_STEP from MFR_VID_RES_R1 register"""
        try:
            # Read MFR_VID_RES_R1 register
            vid_res_data = self.i2c_read16PMBus(page, PMBusDict["MFR_VID_RES_R1"])

            # Extract VID_STEP from bits [12:10]
            vid_step_code = (vid_res_data >> 10) & 0x07

            # VID_STEP lookup table (values in mV)
            # Based on MFR_VOUT_SCALE_LOOP_R1 register bits [12:10]
            vid_step_table = {
                0: 6.25,         # 6.25mV
                1: 5.0,          # 5mV
                2: 2.5,          # 2.5mV
                3: 2.0,          # 2mV
                4: 1.0,          # 1mV
                5: 1.0/256,      # 1/256mV = 0.00390625mV
                6: 1.0/512,      # 1/512mV = 0.001953125mV
                7: 1.0/1024      # 1/1024V = 0.9765625mV
            }

            # Special handling for TSP_CORE (page 0) which uses 0.25mV despite register showing code 7
            if page == 0 and vid_res_data == 0xFFFF:
                # TSP_CORE with uninitialized register uses 0.25mV
                vid_step_mv = 0.25
            elif vid_step_code == 7:
                # TSP_C2C uses the actual 1V/1024 = 0.9765625mV
                vid_step_mv = 1000.0 / 1024  # 0.9765625mV
            else:
                vid_step_mv = vid_step_table.get(vid_step_code, 0.9765625)  # Default to 1V/1024
            vid_step_v = vid_step_mv / 1000.0  # Convert to volts

            print(f"  VID_STEP code: {vid_step_code}, VID_STEP: {vid_step_mv}mV ({vid_step_v}V)")

            return vid_step_v

        except Exception as e:
            print(f"Warning: Could not read VID resolution, using default 0.25mV: {e}")
            return 0.0009765625  # Default to 1V/1024 = 0.9765625mV

    def Write_Vout_Command(self, page, voltage):
        """
        Set the output voltage command for a specific page/rail using VID format

        Args:
            page: PMBus page (0 for TSP_CORE, 1 for TSP_C2C)
            voltage: Target voltage in volts (e.g., 0.8 for 0.8V)

        Returns:
            True if successful, False if failed
        """
        try:
            print(f"Setting voltage for page {page}: {voltage}V")

            # Get VID_STEP resolution
            vid_step = self.Read_VID_Resolution(page)

            # Convert voltage to VID format
            # VID format: VOUT_COMMAND_R1[11:0] = voltage / VID_STEP
            vid_code = int(voltage / vid_step)

            # Ensure the value is within 12-bit range (bits [11:0])
            if vid_code < 0:
                vid_code = 0
            elif vid_code > 0xFFF:
                vid_code = 0xFFF

            # VID format: bits [15:12] are reserved (should be 0)
            # bits [11:0] contain the VID code
            raw_value = vid_code & 0xFFF

            print(f"  VID code: 0x{vid_code:03X} ({vid_code})")
            print(f"  Raw value (VID format): 0x{raw_value:04X}")
            print(f"  Expected voltage: {vid_code * vid_step:.6f}V")

            # Write the VOUT_COMMAND using VID format
            self.i2c_write16PMBus(page, PMBusDict["VOUT_COMMAND"], raw_value)

            return True

        except Exception as e:
            print(f"Error setting voltage on page {page}: {e}")
            return False

    def Set_Vout(self, offset):

        Offset_int= int(offset/6.25)

        Value= Offset_int

        self.i2c_write16(PMBusDict["REG_ACCESS"], PMBusDict["VOUT_OFFSET"], Value)

    def twos_comp(self, val, bits):
        """compute the 2's complement of int value val"""
        if (val & (1 << (bits - 1))) != 0:  # if sign bit is set e.g., 8bit: 128-255
            val = val - (1 << bits)  # compute negative value
        return val

    def Read_Iout(self,page):

        data = self.i2c_read16PMBus(page,PMBusDict["READ_IOUT"])

        #print "Return= ", data

        # Linear11 format
        exponent_raw = (data >> 11) & 0x1F
        mantissa_raw = data & 0x7FF

        # Convert 5-bit exponent to signed
        exponent = self.twos_comp(exponent_raw, 5)

        # Check if mantissa should be treated as signed (bit 10 set)
        if mantissa_raw & 0x400:
            # Convert 11-bit two's complement to signed
            mantissa = mantissa_raw - 0x800
        else:
            mantissa = mantissa_raw

        return mantissa * math.pow(2, exponent)

    def Read_IOUT_SCALE_BIT(self, page):
        """Read IOUT_SCALE_BIT from MFR_VR_CONFIG register (0x67)"""
        self.i2c_write8PMBus(PMBusDict["PAGE"], page)

        # Read MFR_VR_CONFIG register - should be a byte read, not word
        try:
            # Try byte read first
            data = self.i2c_read16PMBus(page, PMBusDict["MFR_VR_CONFIG"]) & 0xFF
        except:
            # If that fails, try word read and mask
            data = self.i2c_read16PMBus(page, PMBusDict["MFR_VR_CONFIG"]) & 0xFF

        print(f"    MFR_VR_CONFIG (0x67) = 0x{data:02X}")

        # Extract IOUT_SCALE_BIT from bits [2:0]
        iout_scale_bit = data & 0x07

        print(f"    IOUT_SCALE_BIT value: {iout_scale_bit}")

        # Calculate scaling factor based on IOUT_SCALE_BIT
        # Common scaling values: 1, 2, 4, 8, 16, 32, 64, 128
        scale_factor = math.pow(2, iout_scale_bit)

        return scale_factor

    def Read_Iout_Rail1(self):
        """Read IOUT for Rail1 (Page 0) at slave address 0x5C"""
        # Ensure we're on page 0 for Rail1
        self.i2c_write8PMBus(PMBusDict["PAGE"], 0)

        data = self.i2c_read16PMBus(0, PMBusDict["READ_IOUT"])

        # Linear11 format: 5-bit exponent + 11-bit mantissa
        # Bits [15:11] = exponent (5-bit two's complement)
        # Bits [10:0] = mantissa (11-bit unsigned)
        exponent_raw = (data >> 11) & 0x1F
        mantissa = data & 0x7FF

        # Convert 5-bit exponent to signed value
        exponent = self.twos_comp(exponent_raw, 5)

        # Calculate base current using Linear11 formula: Y = mantissa * 2^exponent
        iout_base = mantissa * math.pow(2, exponent)

        # The IOUT_SCALE_BIT scaling is already applied in the device firmware
        # The Linear11 value from READ_IOUT register is the final scaled value
        iout = iout_base

        return iout

    def Read_Iout_Rail2(self):
        """Read IOUT for Rail2 (Page 1) at slave address 0x5C"""
        # Switch to page 1 for Rail2
        self.i2c_write8PMBus(PMBusDict["PAGE"], 1)

        data = self.i2c_read16PMBus(1, PMBusDict["READ_IOUT"])

        # Linear11 format: 5-bit exponent + 11-bit mantissa
        exponent_raw = (data >> 11) & 0x1F
        mantissa = data & 0x7FF

        # Convert 5-bit exponent to signed value
        exponent = self.twos_comp(exponent_raw, 5)

        # Calculate base current using Linear11 formula
        iout_base = mantissa * math.pow(2, exponent)

        # The IOUT_SCALE_BIT scaling is already applied in the device firmware
        # The Linear11 value from READ_IOUT register is the final scaled value
        iout = iout_base

        return iout

    def Read_Temp(self, page):

        data = self.i2c_read16PMBus(page, PMBusDict["READ_TEMPERATURE_1"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def Read_Phase_Currents(self):

        phase1 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE1_Current"]))&0xFF
        time.sleep(.05)
        phase2 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE2_Current"]))&0xFF
        time.sleep(.05)
        phase3 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE3_Current"]))&0xFF
        time.sleep(.05)
        phase4 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE4_Current"]))&0xFF
        time.sleep(.05)
        phase5 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE5_Current"]))&0xFF
        time.sleep(.05)
        phase6 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE6_Current"]))&0xFF
        time.sleep(.05)
        phase7 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE7_Current"]))&0xFF
        time.sleep(.05)
        phase8 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE8_Current"]))&0xFF
        time.sleep(.05)
        phase9 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE9_Current"]))&0xFF
        time.sleep(.05)
        phase10 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE10_Current"]))&0xFF
        time.sleep(.05)
        phase11 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE11_Current"]))&0xFF
        time.sleep(.05)
        phase12 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE12_Current"]))&0xFF
        time.sleep(.05)
        phase13 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE13_Current"]))&0xFF
        time.sleep(.05)
        phase14 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE14_Current"]))&0xFF
        time.sleep(.05)
        phase15 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE15_Current"]))&0xFF
        time.sleep(.05)
        phase16 = (self.i2c_read16(PMBusDict["REG_ACCESS"], PMBusDict["PHASE16_Current"]))&0xFF
        time.sleep(.05)

        return phase1,phase2, phase3, phase4, phase5, phase6, phase7, phase8, phase9, phase10, phase11, phase12, phase13, phase14, phase15, phase16



    def set_Freq(self,page, value):

        self.i2c_write16PMBus(page, PMBusDict["FREQUENCY_SWITCH"], value)



    def set_LL(self, page, value):

        res= .0195

        final_value = int(value/res)

        print(final_value)

        self.i2c_write16PMBus(page, PMBusDict["VOUT_DROOP"], final_value)

    def CLEAR_FAULTS(self, page):

        self.i2c_writePMBus_cmd_only(page, PMBusDict["CLEAR_FAULTS"])

    def set_loop1_Phases(self, value1=14, value2=0):

        final_value = (value1 << 8) + value2
        print(hex(final_value))

        self.i2c_write16(PMBusDict["REG_ACCESS"], PMBusDict["Loop1_active"], final_value)

    def Get_loop1_Phases(self):

        Loop1Phases = self.i2c_read16(PMBusDict["MFR_REG_ACCESS"], PMBusDict["Phase_active"])

        return Loop1Phases

    def Read_Duty(self, page):

        duty = self.i2c_read16PMBus(page, PMBusDict["READ_DUTY"])

        return duty*.25

    def Read_PIN(self, page):

        data = self.i2c_read16PMBus(page, PMBusDict["READ_PIN"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def Read_POUT(self, page):

        data = self.i2c_read16PMBus(page, PMBusDict["READ_POUT"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def Read_Peak_Temp(self, page):

        data = self.i2c_read16PMBus(page, PMBusDict["MFR_TEMP_PEAK"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def Read_IOUT_Peak(self, page):

        data = self.i2c_read16PMBus(page, PMBusDict["MFR_IOUT_PEAK"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def Read_IIN(self, page):

        data = self.i2c_read16PMBus(page,PMBusDict["READ_IIN"])

        exponent = data >> 11
        mantissa = data & 0x7ff

        power = self.twos_comp(exponent, 5)

        return mantissa * math.pow(2, power)

    def PMBus_ON(self, page):

        self.i2c_write16PMBus(page, PMBusDict["FREQUENCY_SWITCH"], 1)

    def Page(self, value):

        self.i2c_write8PMBus(PMBusDict["PAGE"], value)


    def get_telemetry(self, page):

        Vout= self.Read_Vout(page)
        Iout = self.Read_Iout(page)
        Temp = self.Read_Temp(page)
        Duty = self.Read_Duty(page)

        (phase1,phase2, phase3, phase4, phase5, phase6, phase7, phase8, phase9, phase10, phase11, phase12, phase13, phase14, phase15, phase16) = self.Read_Phase_Currents()

        phase_count = self.Get_loop1_Phases()

        Status_byte = self.i2c_read16PMBus(page, PMBusDict["STATUS_BYTE"])
        Status_word = self.i2c_read16PMBus(page,PMBusDict["STATUS_WORD"])
        Status_VOUT = self.i2c_read16PMBus(page,PMBusDict["STATUS_VOUT"])
        Status_IOUT = self.i2c_read16PMBus(page,PMBusDict["STATUS_IOUT"])
        Status_INP = self.i2c_read16PMBus(page,PMBusDict["STATUS_INPUT"])
        Status_Temp = self.i2c_read16PMBus(page,PMBusDict["STATUS_TEMPERATURE"])
        Status_MFR_SPECIFIC = self.i2c_read16PMBus(page,PMBusDict["STATUS_MFR_SPECIFIC"])

        Iout_peak = self.Read_IOUT_Peak(page)
        Temp_peak = self.Read_Peak_Temp(page)

        Iin_PMBus = self.Read_IIN(page)
        Pin_PMBus = self.Read_PIN(page)
        Pout_PMBus = self.Read_POUT(page)


        return Duty, Vout, Iout, Temp, Status_byte, Status_word, Status_VOUT, Status_IOUT, Status_INP, Status_Temp, Status_MFR_SPECIFIC, Iout_peak,Temp_peak, phase_count, phase1,phase2, phase3, phase4, phase5, phase6, phase7, phase8, phase9, phase10, phase11, phase12, phase13, phase14, phase15, phase16, Iin_PMBus, Pin_PMBus, Pout_PMBus

    def get_telemetry_basic(self, page):

        Vout= self.Read_Vout(page)
        Iout = self.Read_Iout(page)
        Temp = self.Read_Temp(page)
        Duty = self.Read_Duty(page)

        #(phase1,phase2, phase3, phase4, phase5, phase6, phase7, phase8, phase9, phase10, phase11, phase12, phase13, phase14, phase15, phase16) = self.Read_Phase_Currents()

        phase_count = self.Get_loop1_Phases()

        Status_byte = (self.i2c_read16PMBus(page, PMBusDict["STATUS_BYTE"]))&0x00FF
        Status_word = self.i2c_read16PMBus(page, PMBusDict["STATUS_WORD"])
        Status_VOUT = (self.i2c_read16PMBus(page, PMBusDict["STATUS_VOUT"]))&0x00FF
        Status_IOUT = (self.i2c_read16PMBus(page, PMBusDict["STATUS_IOUT"]))&0x00FF
        Status_INP = (self.i2c_read16PMBus(page, PMBusDict["STATUS_INPUT"]))&0x00FF
        Status_Temp = (self.i2c_read16PMBus(page, PMBusDict["STATUS_TEMPERATURE"]))&0x00FF
        Status_MFR_SPECIFIC = (self.i2c_read16PMBus(page, PMBusDict["STATUS_MFR_SPECIFIC"]))&0x00FF

        Iout_peak = self.Read_IOUT_Peak(page)
        Temp_peak = self.Read_Peak_Temp(page)

        Iin_PMBus = self.Read_IIN(page)
        Pin_PMBus = self.Read_PIN(page)
        Pout_PMBus = self.Read_POUT(page)

        return Duty, Vout, Iout, Temp, Status_byte, Status_word, Status_VOUT, Status_IOUT, Status_INP, Status_Temp, Status_MFR_SPECIFIC, Iout_peak,Temp_peak, phase_count, Iin_PMBus, Pin_PMBus, Pout_PMBus

    def Read_Vout_Rail1_Raw(self):
        """Read VOUT for Rail1 with raw data and conversion parameters"""
        # Ensure we're on page 0 for Rail1
        self.i2c_write8PMBus(PMBusDict["PAGE"], 0)

        # Read the raw VOUT data
        raw_data = self.i2c_read16PMBus(0, PMBusDict["READ_VOUT"])

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(0)
        except:
            exponent = -10  # Default for many VR controllers

        # Linear16 format: mantissa * 2^exponent
        vout = raw_data * math.pow(2, exponent)

        return {
            'raw_hex': f"0x{raw_data:04X}",
            'raw_dec': raw_data,
            'exponent': exponent,
            'voltage': vout
        }

    def Read_Vout_Rail2_Raw(self):
        """Read VOUT for Rail2 with raw data and conversion parameters"""
        # Switch to page 1 for Rail2
        self.i2c_write8PMBus(PMBusDict["PAGE"], 1)

        # Read the raw VOUT data
        raw_data = self.i2c_read16PMBus(1, PMBusDict["READ_VOUT"])

        # Read VOUT_MODE to get the correct exponent
        try:
            exponent = self.Read_VOUT_MODE(1)
        except:
            exponent = -10  # Default for many VR controllers

        # Linear16 format: mantissa * 2^exponent
        vout = raw_data * math.pow(2, exponent)

        return {
            'raw_hex': f"0x{raw_data:04X}",
            'raw_dec': raw_data,
            'exponent': exponent,
            'voltage': vout
        }

    def Read_Iout_Rail1_Raw(self):
        """Read IOUT for Rail1 with raw data and Linear11 breakdown"""
        # Ensure we're on page 0 for Rail1
        self.i2c_write8PMBus(PMBusDict["PAGE"], 0)

        raw_data = self.i2c_read16PMBus(0, PMBusDict["READ_IOUT"])

        # Linear11 format: 5-bit exponent + 11-bit mantissa
        # Bits [15:11] = exponent (5-bit two's complement)
        # Bits [10:0] = mantissa (11-bit unsigned)
        exponent_raw = (raw_data >> 11) & 0x1F
        mantissa = raw_data & 0x7FF

        # Convert 5-bit exponent to signed value
        exponent = self.twos_comp(exponent_raw, 5)

        # Calculate current using Linear11 formula: Y = mantissa * 2^exponent
        iout = mantissa * math.pow(2, exponent)

        return {
            'raw_hex': f"0x{raw_data:04X}",
            'raw_dec': raw_data,
            'exponent': exponent,
            'mantissa': mantissa,
            'current': iout
        }

    def Read_Iout_Rail2_Raw(self):
        """Read IOUT for Rail2 with raw data and Linear11 breakdown"""
        # Switch to page 1 for Rail2
        self.i2c_write8PMBus(PMBusDict["PAGE"], 1)

        raw_data = self.i2c_read16PMBus(1, PMBusDict["READ_IOUT"])

        # Linear11 format: 5-bit exponent + 11-bit mantissa
        exponent_raw = (raw_data >> 11) & 0x1F
        mantissa = raw_data & 0x7FF

        # Convert 5-bit exponent to signed value
        exponent = self.twos_comp(exponent_raw, 5)

        # Calculate current using Linear11 formula
        iout = mantissa * math.pow(2, exponent)

        return {
            'raw_hex': f"0x{raw_data:04X}",
            'raw_dec': raw_data,
            'exponent': exponent,
            'mantissa': mantissa,
            'current': iout
        }

    def continuous_logging(self, duration_minutes=2, sample_rate_ms=100, csv_filename=None):
        """
        Continuously log VOUT and IOUT for both rails

        Args:
            duration_minutes: Duration to log in minutes (default: 2)
            sample_rate_ms: Sample interval in milliseconds (default: 100ms)
            csv_filename: CSV file to save data (default: auto-generated)
        """

        # Generate default filename if not provided
        if csv_filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            # Ensure data directory exists
            data_dir = "data"
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            csv_filename = os.path.join(data_dir, f"pmbus_log_{timestamp}.csv")

        # Calculate timing parameters
        sample_interval = sample_rate_ms / 1000.0  # Convert to seconds
        total_duration = duration_minutes * 60.0   # Convert to seconds
        total_samples = int(total_duration / sample_interval)

        print(f"Starting continuous logging...")
        print(f"Duration: {duration_minutes} minutes ({total_duration:.1f} seconds)")
        print(f"Sample rate: {sample_rate_ms}ms ({1000/sample_rate_ms:.1f} samples/sec)")
        print(f"Expected samples: {total_samples}")
        print(f"Output file: {csv_filename}")
        print(f"Target slave address: 0x{SLAVE_ADDR:02X}")
        print("-" * 60)

        # CSV headers with raw data and conversion parameters
        headers = [
            'timestamp',
            'sample_num',
            # Rail1 VOUT data
            'rail1_vout_raw_hex',
            'rail1_vout_raw_dec',
            'rail1_vout_exponent',
            'rail1_vout_v',
            # Rail1 IOUT data
            'rail1_iout_raw_hex',
            'rail1_iout_raw_dec',
            'rail1_iout_exponent',
            'rail1_iout_mantissa',
            'rail1_iout_a',
            # Rail2 VOUT data
            'rail2_vout_raw_hex',
            'rail2_vout_raw_dec',
            'rail2_vout_exponent',
            'rail2_vout_v',
            # Rail2 IOUT data
            'rail2_iout_raw_hex',
            'rail2_iout_raw_dec',
            'rail2_iout_exponent',
            'rail2_iout_mantissa',
            'rail2_iout_a',
            # Status
            'rail1_status',
            'rail2_status'
        ]

        # Open CSV file for writing
        start_time = time.time()
        sample_count = 0
        error_count = 0

        try:
            with open(csv_filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(headers)

                print("Logging started... Press Ctrl+C to stop early")

                while True:
                    loop_start = time.time()
                    current_time = loop_start - start_time

                    # Check if duration exceeded
                    if current_time >= total_duration:
                        break

                    try:
                        # Read Rail1 (Page 0) data with raw values
                        rail1_vout_data = self.Read_Vout_Rail1_Raw()
                        rail1_iout_data = self.Read_Iout_Rail1_Raw()

                        # Read Rail1 status
                        self.i2c_write8PMBus(PMBusDict["PAGE"], 0)
                        rail1_status = self.i2c_read16PMBus(0, PMBusDict["STATUS_WORD"])

                        # Read Rail2 (Page 1) data with raw values
                        rail2_vout_data = self.Read_Vout_Rail2_Raw()
                        rail2_iout_data = self.Read_Iout_Rail2_Raw()

                        # Read Rail2 status
                        self.i2c_write8PMBus(PMBusDict["PAGE"], 1)
                        rail2_status = self.i2c_read16PMBus(1, PMBusDict["STATUS_WORD"])

                        # Write data to CSV with all raw data and conversion parameters
                        row = [
                            f"{current_time:.3f}",
                            sample_count + 1,
                            # Rail1 VOUT
                            rail1_vout_data['raw_hex'],
                            rail1_vout_data['raw_dec'],
                            rail1_vout_data['exponent'],
                            f"{rail1_vout_data['voltage']:.6f}",
                            # Rail1 IOUT
                            rail1_iout_data['raw_hex'],
                            rail1_iout_data['raw_dec'],
                            rail1_iout_data['exponent'],
                            rail1_iout_data['mantissa'],
                            f"{rail1_iout_data['current']:.3f}",
                            # Rail2 VOUT
                            rail2_vout_data['raw_hex'],
                            rail2_vout_data['raw_dec'],
                            rail2_vout_data['exponent'],
                            f"{rail2_vout_data['voltage']:.6f}",
                            # Rail2 IOUT
                            rail2_iout_data['raw_hex'],
                            rail2_iout_data['raw_dec'],
                            rail2_iout_data['exponent'],
                            rail2_iout_data['mantissa'],
                            f"{rail2_iout_data['current']:.3f}",
                            # Status
                            f"0x{rail1_status:04X}",
                            f"0x{rail2_status:04X}"
                        ]
                        writer.writerow(row)

                        sample_count += 1

                        # Progress indicator every 50 samples
                        if sample_count % 50 == 0:
                            progress = (current_time / total_duration) * 100
                            print(f"Progress: {sample_count:4d}/{total_samples} samples ({progress:5.1f}%) - "
                                  f"R1: {rail1_vout_data['voltage']:.4f}V/{rail1_iout_data['current']:.1f}A, "
                                  f"R2: {rail2_vout_data['voltage']:.4f}V/{rail2_iout_data['current']:.1f}A")

                            # Flush to ensure data is written
                            csvfile.flush()

                    except Exception as e:
                        error_count += 1
                        print(f"Error at sample {sample_count + 1}: {e}")
                        if error_count > 10:
                            print("Too many errors, stopping...")
                            break

                    # Maintain sample rate
                    loop_time = time.time() - loop_start
                    sleep_time = sample_interval - loop_time

                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    elif sleep_time < -0.001:  # Warn if we're running behind
                        print(f"Warning: Sample {sample_count} took {loop_time*1000:.1f}ms (target: {sample_rate_ms}ms)")

        except KeyboardInterrupt:
            print("\nLogging interrupted by user")
        except Exception as e:
            print(f"\nLogging error: {e}")

        finally:
            end_time = time.time()
            actual_duration = end_time - start_time
            actual_rate = sample_count / actual_duration if actual_duration > 0 else 0

            print("-" * 60)
            print(f"Logging completed!")
            print(f"Samples collected: {sample_count}")
            print(f"Actual duration: {actual_duration:.1f} seconds")
            print(f"Actual sample rate: {actual_rate:.1f} samples/sec")
            print(f"Errors: {error_count}")
            print(f"Data saved to: {csv_filename}")

            if sample_count > 0:
                print("\nFinal readings:")
                print(f"Rail1: {rail1_vout_data['voltage']:.4f}V, {rail1_iout_data['current']:.2f}A")
                print(f"Rail2: {rail2_vout_data['voltage']:.4f}V, {rail2_iout_data['current']:.2f}A")


def continuous_single_command_logging(rail, command, duration_minutes=2, sample_rate_ms=100):
    """
    Continuously log a single PMBus command from a specific rail to CSV

    Args:
        rail: Rail to monitor (TSP_CORE or TSP_C2C)
        command: PMBus command to log
        duration_minutes: Duration to log in minutes (default: 2)
        sample_rate_ms: Sample interval in milliseconds (default: 100ms)
    """

    # Rail mapping
    rail_mapping = {
        'TSP_CORE': 0,  # Rail0 - Page 0
        'TSP_C2C': 1   # Rail1 - Page 1
    }

    if rail not in rail_mapping:
        print(f"Error: Invalid rail '{rail}'. Valid options: TSP_CORE, TSP_C2C")
        return False

    page = rail_mapping[rail]

    # Command mapping to available methods
    command_mapping = {
        'READ_VOUT': lambda powertool, p: powertool.Read_Vout(p),
        'READ_IOUT': lambda powertool, p: powertool.Read_Iout(p),
        'READ_TEMPERATURE_1': lambda powertool, p: powertool.Read_Temp(p),
        'READ_DUTY': lambda powertool, p: powertool.Read_Duty(p),
        'READ_PIN': lambda powertool, p: powertool.Read_PIN(p),
        'READ_POUT': lambda powertool, p: powertool.Read_POUT(p),
        'READ_IIN': lambda powertool, p: powertool.Read_IIN(p),
        'STATUS_BYTE': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_BYTE"]) & 0xFF,
        'STATUS_WORD': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_WORD"]),
        'STATUS_VOUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_VOUT"]) & 0xFF,
        'STATUS_IOUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_IOUT"]) & 0xFF,
        'STATUS_INPUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_INPUT"]) & 0xFF,
        'STATUS_TEMPERATURE': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_TEMPERATURE"]) & 0xFF,
        'VOUT_MODE': lambda powertool, p: powertool.Read_VOUT_MODE(p),
        'MFR_IOUT_PEAK': lambda powertool, p: powertool.Read_IOUT_Peak(p),
        'MFR_TEMP_PEAK': lambda powertool, p: powertool.Read_Peak_Temp(p)
    }

    if command not in command_mapping:
        print(f"Error: Invalid command '{command}'")
        print("Available commands:")
        for cmd in sorted(command_mapping.keys()):
            print(f"  - {cmd}")
        return False

    # Determine units for the command
    units_mapping = {
        'READ_VOUT': 'V',
        'READ_IOUT': 'A',
        'READ_IIN': 'A',
        'MFR_IOUT_PEAK': 'A',
        'READ_TEMPERATURE_1': '°C',
        'MFR_TEMP_PEAK': '°C',
        'READ_PIN': 'W',
        'READ_POUT': 'W',
        'READ_DUTY': '%',
        'VOUT_MODE': '',
        'STATUS_BYTE': 'hex',
        'STATUS_WORD': 'hex',
        'STATUS_VOUT': 'hex',
        'STATUS_IOUT': 'hex',
        'STATUS_INPUT': 'hex',
        'STATUS_TEMPERATURE': 'hex'
    }

    units = units_mapping.get(command, '')

    # Generate CSV filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Ensure data directory exists
    data_dir = "data"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    csv_filename = os.path.join(data_dir, f"{rail}_{command}_{timestamp}.csv")

    # Calculate timing parameters
    sample_interval = sample_rate_ms / 1000.0  # Convert to seconds
    total_duration = duration_minutes * 60.0   # Convert to seconds
    total_samples = int(total_duration / sample_interval)

    print(f"Starting continuous logging of {command} from {rail}...")
    print(f"Duration: {duration_minutes} minutes ({total_duration:.1f} seconds)")
    print(f"Sample rate: {sample_rate_ms}ms ({1000/sample_rate_ms:.1f} samples/sec)")
    print(f"Expected samples: {total_samples}")
    print(f"Output file: {csv_filename}")
    print(f"Target rail: {rail} (Page {page})")
    print("-" * 60)

    # CSV headers
    headers = ['timestamp', 'sample_num', 'value', 'units']

    # Open CSV file for writing
    start_time = time.time()
    sample_count = 0
    error_count = 0

    try:
        # Initialize I2C connection once
        print("Initializing I2C connection...")
        powertool = PowerToolI2C()
        print("I2C connection successful")
        print()

        with open(csv_filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            print(f"Logging {command} from {rail}... Press Ctrl+C to stop early")

            while True:
                loop_start = time.time()
                current_time = loop_start - start_time

                # Check if duration exceeded
                if current_time >= total_duration:
                    break

                try:
                    # Execute the command
                    result = command_mapping[command](powertool, page)

                    # Format the value based on command type
                    if command.startswith('STATUS'):
                        if command == 'STATUS_WORD':
                            value_str = f"0x{result:04X}"
                        else:
                            value_str = f"0x{result:02X}"
                    elif command in ['READ_VOUT']:
                        value_str = f"{result:.6f}"
                    elif command in ['READ_IOUT', 'READ_IIN', 'MFR_IOUT_PEAK']:
                        value_str = f"{result:.3f}"
                    elif command in ['READ_TEMPERATURE_1', 'MFR_TEMP_PEAK']:
                        value_str = f"{result:.2f}"
                    elif command in ['READ_PIN', 'READ_POUT']:
                        value_str = f"{result:.3f}"
                    elif command == 'READ_DUTY':
                        value_str = f"{result:.2f}"
                    else:
                        value_str = str(result)

                    # Write data to CSV
                    row = [
                        f"{current_time:.3f}",
                        sample_count + 1,
                        value_str,
                        units
                    ]
                    writer.writerow(row)

                    sample_count += 1

                    # Progress indicator every 50 samples
                    if sample_count % 50 == 0:
                        progress = (current_time / total_duration) * 100
                        print(f"Progress: {sample_count:4d}/{total_samples} samples ({progress:5.1f}%) - "
                              f"{rail} {command}: {value_str} {units}")

                        # Flush to ensure data is written
                        csvfile.flush()

                except Exception as e:
                    error_count += 1
                    print(f"Error at sample {sample_count + 1}: {e}")
                    if error_count > 10:
                        print("Too many errors, stopping...")
                        break

                # Maintain sample rate
                loop_time = time.time() - loop_start
                sleep_time = sample_interval - loop_time

                if sleep_time > 0:
                    time.sleep(sleep_time)
                elif sleep_time < -0.001:  # Warn if we're running behind
                    print(f"Warning: Sample {sample_count} took {loop_time*1000:.1f}ms (target: {sample_rate_ms}ms)")

    except KeyboardInterrupt:
        print("\nLogging interrupted by user")
    except Exception as e:
        print(f"\nLogging error: {e}")

    finally:
        end_time = time.time()
        actual_duration = end_time - start_time
        actual_rate = sample_count / actual_duration if actual_duration > 0 else 0

        print("-" * 60)
        print(f"Logging completed!")
        print(f"Samples collected: {sample_count}")
        print(f"Actual duration: {actual_duration:.1f} seconds")
        print(f"Actual sample rate: {actual_rate:.1f} samples/sec")
        print(f"Errors: {error_count}")
        print(f"Data saved to: {csv_filename}")

        if sample_count > 0:
            print(f"\nFinal reading: {rail} {command} = {value_str} {units}")

    return True

def execute_single_command(rail, command):
    """Execute a single PMBus command on specified rail"""

    # Rail mapping
    rail_mapping = {
        'TSP_CORE': 0,  # Rail0 - Page 0
        'TSP_C2C': 1   # Rail1 - Page 1
    }

    if rail not in rail_mapping:
        print(f"Error: Invalid rail '{rail}'. Valid options: TSP_CORE, TSP_C2C")
        return False

    page = rail_mapping[rail]

    # Command mapping to available methods
    command_mapping = {
        'READ_VOUT': lambda powertool, p: powertool.Read_Vout(p),
        'READ_IOUT': lambda powertool, p: powertool.Read_Iout(p),
        'READ_TEMPERATURE_1': lambda powertool, p: powertool.Read_Temp(p),
        'READ_DUTY': lambda powertool, p: powertool.Read_Duty(p),
        'READ_PIN': lambda powertool, p: powertool.Read_PIN(p),
        'READ_POUT': lambda powertool, p: powertool.Read_POUT(p),
        'READ_IIN': lambda powertool, p: powertool.Read_IIN(p),
        'STATUS_BYTE': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_BYTE"]) & 0xFF,
        'STATUS_WORD': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_WORD"]),
        'STATUS_VOUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_VOUT"]) & 0xFF,
        'STATUS_IOUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_IOUT"]) & 0xFF,
        'STATUS_INPUT': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_INPUT"]) & 0xFF,
        'STATUS_TEMPERATURE': lambda powertool, p: powertool.i2c_read16PMBus(p, PMBusDict["STATUS_TEMPERATURE"]) & 0xFF,
        'VOUT_MODE': lambda powertool, p: powertool.Read_VOUT_MODE(p),
        'MFR_IOUT_PEAK': lambda powertool, p: powertool.Read_IOUT_Peak(p),
        'MFR_TEMP_PEAK': lambda powertool, p: powertool.Read_Peak_Temp(p)
    }

    if command not in command_mapping:
        print(f"Error: Invalid command '{command}'")
        print("Available commands:")
        for cmd in sorted(command_mapping.keys()):
            print(f"  - {cmd}")
        return False

    try:
        print(f"Initializing I2C connection...")
        powertool = PowerToolI2C()
        print(f"Executing {command} on {rail} (Page {page})...")

        result = command_mapping[command](powertool, page)

        # Format output based on command type
        if command.startswith('STATUS'):
            if command == 'STATUS_WORD':
                print(f"{rail} {command}: 0x{result:04X}")
            else:
                print(f"{rail} {command}: 0x{result:02X}")
        elif command in ['READ_VOUT']:
            print(f"{rail} {command}: {result:.6f} V")
        elif command in ['READ_IOUT', 'READ_IIN', 'MFR_IOUT_PEAK']:
            print(f"{rail} {command}: {result:.3f} A")
        elif command in ['READ_TEMPERATURE_1', 'MFR_TEMP_PEAK']:
            print(f"{rail} {command}: {result:.2f} °C")
        elif command in ['READ_PIN', 'READ_POUT']:
            print(f"{rail} {command}: {result:.3f} W")
        elif command == 'READ_DUTY':
            print(f"{rail} {command}: {result:.2f} %")
        elif command == 'VOUT_MODE':
            print(f"{rail} {command}: {result} (exponent)")
        else:
            print(f"{rail} {command}: {result}")

        return True

    except Exception as e:
        print(f"Error executing {command} on {rail}: {e}")
        return False

def execute_vout_command(rail, voltage):
    """Execute VOUT_COMMAND to set voltage on specified rail"""

    # Rail mapping
    rail_mapping = {
        'TSP_CORE': 0,  # Rail0 - Page 0
        'TSP_C2C': 1   # Rail1 - Page 1
    }

    if rail not in rail_mapping:
        print(f"Error: Invalid rail '{rail}'. Valid options: TSP_CORE, TSP_C2C")
        return False

    page = rail_mapping[rail]

    # Validate voltage range (reasonable limits for power supplies)
    if voltage < 0.3 or voltage > 3.3:
        print(f"Error: Voltage {voltage}V is outside safe range (0.3V to 3.3V)")
        return False

    try:
        print(f"Initializing I2C connection...")
        powertool = PowerToolI2C()
        print(f"Setting voltage on {rail} (Page {page}) to {voltage}V...")

        # Read current voltage before changing
        current_voltage = powertool.Read_Vout(page)
        print(f"Current voltage: {current_voltage:.6f}V")

        # Set new voltage
        success = powertool.Write_Vout_Command(page, voltage)

        if success:
            # Wait 2 seconds for voltage to fully settle and stabilize
            print("Waiting 2 seconds for voltage to settle...")
            time.sleep(2.0)

            # Single READ_VOUT to confirm voltage change
            final_voltage = powertool.Read_Vout(page)
            print(f"Final voltage: {final_voltage:.6f}V")

            # Check if voltage is within reasonable tolerance (±1%)
            tolerance = voltage * 0.01
            if abs(final_voltage - voltage) <= tolerance:
                print(f"✓ SUCCESS: Voltage set successfully (within ±1% tolerance)")
                return True
            else:
                print(f"⚠ WARNING: Final voltage differs from target by {abs(final_voltage - voltage):.6f}V")
                return True  # Still consider success as the command executed
        else:
            print(f"✗ FAILED: Could not set voltage")
            return False

    except Exception as e:
        print(f"Error setting voltage on {rail}: {e}")
        return False

def continuous_register_logging(page, hex_addr, addr_desc, byte_count):
    """Continuous logging of a specific register to CSV file"""
    print(f"Continuous logging from Page {page}, Address {addr_desc}, {byte_count} byte(s)")
    print("="*70)
    print("Press Ctrl+C to stop logging")
    print("="*70)

    # Initialize I2C
    powertool = PowerToolI2C()

    # Create CSV filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    if addr_desc.find('(') > 0:
        cmd_name = addr_desc.split(' (')[0]  # Extract command name before hex
    else:
        cmd_name = f"0x{hex_addr:02X}"
    csv_filename = f"data/PAGE{page}_{cmd_name}_{timestamp}.csv"

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)

    try:
        with open(csv_filename, 'w', newline='') as csvfile:
            fieldnames = ['timestamp', 'page', 'address', 'hex_addr', 'raw_value', 'decimal_value']
            if byte_count == 2:
                fieldnames.extend(['low_byte', 'high_byte', 'binary'])
            else:
                fieldnames.append('binary')

            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            csvfile.flush()

            print(f"Logging to: {csv_filename}")
            print("\nSample data (also being saved to CSV):")
            print("-" * 80)

            sample_count = 0
            while True:
                try:
                    # Set page and read data
                    powertool.i2c_write8PMBus(PMBusDict["PAGE"], page)

                    current_time = datetime.datetime.now()
                    timestamp_str = current_time.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

                    if byte_count == 1:
                        data = powertool.i2c_read8PMBus(page, hex_addr)
                        binary_str = bin(data)[2:].zfill(8)

                        row = {
                            'timestamp': timestamp_str,
                            'page': page,
                            'address': addr_desc,
                            'hex_addr': f"0x{hex_addr:02X}",
                            'raw_value': f"0x{data:02X}",
                            'decimal_value': data,
                            'binary': binary_str
                        }
                    else:
                        data = powertool.i2c_read16PMBus(page, hex_addr)
                        low_byte = data & 0xFF
                        high_byte = (data >> 8) & 0xFF
                        binary_str = bin(data)[2:].zfill(16)

                        row = {
                            'timestamp': timestamp_str,
                            'page': page,
                            'address': addr_desc,
                            'hex_addr': f"0x{hex_addr:02X}",
                            'raw_value': f"0x{data:04X}",
                            'decimal_value': data,
                            'low_byte': f"0x{low_byte:02X}",
                            'high_byte': f"0x{high_byte:02X}",
                            'binary': binary_str
                        }

                    writer.writerow(row)
                    csvfile.flush()

                    # Show sample data (first 10 samples, then every 50th)
                    if sample_count < 10 or sample_count % 50 == 0:
                        if byte_count == 1:
                            print(f"[{sample_count+1:4d}] {timestamp_str}: 0x{data:02X} ({data:3d}) {binary_str}")
                        else:
                            print(f"[{sample_count+1:4d}] {timestamp_str}: 0x{data:04X} ({data:5d}) {binary_str} (H:0x{high_byte:02X} L:0x{low_byte:02X})")

                    sample_count += 1
                    time.sleep(0.1)  # 100ms interval

                except KeyboardInterrupt:
                    print(f"\n\nLogging stopped after {sample_count} samples.")
                    print(f"Data saved to: {csv_filename}")
                    return True
                except Exception as e:
                    print(f"\nError during logging: {e}")
                    print(f"Logged {sample_count} samples before error.")
                    return False

    except Exception as e:
        print(f"Error creating CSV file: {e}")
        return False

def main():
    print("PMBus Rail Monitor - MP29816-C Controller")
    print(f"Target slave address: 0x{SLAVE_ADDR:02X}")
    print("=" * 60)

    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="PowerTool - PMBus monitoring tool for MP29816-C Controller",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Formats:
  ./powertool.py [RAIL] [COMMAND] [OPTIONS]      # Standard command execution
  ./powertool.py page [0/1] [ADDRESS|COMMAND] READ [1/2] # Direct register read
  ./powertool.py log                             # Continuous logging mode
  ./powertool.py test                            # Run readback test

Examples:
  Standard Commands:
    ./powertool.py TSP_CORE READ_VOUT              # Read voltage from TSP_CORE rail
    ./powertool.py TSP_C2C READ_IOUT               # Read current from TSP_C2C rail
    ./powertool.py TSP_CORE VOUT_COMMAND 0.8       # Set TSP_CORE voltage to 0.8V
    ./powertool.py TSP_C2C VOUT_COMMAND 0.75       # Set TSP_C2C voltage to 0.75V

  Continuous Logging:
    ./powertool.py TSP_CORE READ_VOUT log          # Continuously log voltage to CSV
    ./powertool.py TSP_C2C READ_IOUT log           # Continuously log current to CSV
    ./powertool.py log                             # Log all rails continuously

  Direct Register Access:
    ./powertool.py page 0 READ_VOUT READ 2         # Single read using English name
    ./powertool.py page 0 READ_VOUT LOG 2          # Continuous log using English name
    ./powertool.py page 1 STATUS_WORD LOG 2        # Log status word on page 1
    ./powertool.py page 0 VOUT_MODE READ 1         # Read VOUT_MODE (1 byte)
    ./powertool.py page 0 0x8B READ 2              # Single read using hex address
    ./powertool.py page 0 0x8B LOG 2               # Continuous log using hex address

  Test Mode:
    ./powertool.py test                            # Run single readback test

Available Rails: TSP_CORE, TSP_C2C
Available Commands: READ_VOUT, READ_IOUT, READ_TEMPERATURE_1, READ_DUTY, READ_PIN,
                   READ_POUT, READ_IIN, STATUS_BYTE, STATUS_WORD, STATUS_VOUT,
                   STATUS_IOUT, STATUS_INPUT, STATUS_TEMPERATURE, VOUT_MODE,
                   MFR_IOUT_PEAK, MFR_TEMP_PEAK, VOUT_COMMAND

Note: Add "log" as third argument to continuously log any command to CSV file
      For VOUT_COMMAND, use voltage value as third argument (e.g., 0.8 for 0.8V)
        """
    )

    # Add positional arguments
    parser.add_argument('rail', nargs='?',
                       help='Rail to target: TSP_CORE or TSP_C2C, or "page" for hex read (or "log"/"test" for special modes)')
    parser.add_argument('command', nargs='?',
                       help='PMBus command (e.g., READ_VOUT) or page number for hex read (e.g., 0, 1)')
    parser.add_argument('log_mode', nargs='?',
                       help='Optional: "log" for logging, voltage for VOUT_COMMAND, or hex address for direct read (e.g., 0x62)')
    parser.add_argument('extra_arg', nargs='?',
                       help='Optional: "READ" for hex read mode, or byte count (1 or 2)')
    parser.add_argument('byte_count', nargs='?',
                       help='Optional: Number of bytes to read (1 or 2) for hex address mode')

    # Parse arguments
    args = parser.parse_args()

    # Handle hex address read/log mode: page [0/1] 0xXX [READ|LOG] [1/2]
    if args.rail and args.rail.lower() == "page" and args.command is not None and args.log_mode and args.extra_arg:
        try:
            # Parse page number
            page = int(args.command)

            # Parse address - can be hex address or English command name
            if args.log_mode.upper() in PMBusDict:
                # English command name
                hex_addr = PMBusDict[args.log_mode.upper()]
                addr_desc = f"{args.log_mode.upper()} (0x{hex_addr:02X})"
            elif args.log_mode.lower().startswith('0x'):
                # Hex with 0x prefix
                hex_addr = int(args.log_mode, 16)
                addr_desc = f"0x{hex_addr:02X}"
            elif args.log_mode.lower().endswith('h'):
                # Hex with h suffix
                hex_addr = int(args.log_mode[:-1], 16)
                addr_desc = f"0x{hex_addr:02X}"
            else:
                # Plain hex or decimal
                try:
                    hex_addr = int(args.log_mode, 16)
                    addr_desc = f"0x{hex_addr:02X}"
                except ValueError:
                    hex_addr = int(args.log_mode)
                    addr_desc = f"0x{hex_addr:02X}"

            # Check for READ or LOG keyword
            if args.extra_arg.upper() not in ["READ", "LOG"]:
                # Maybe byte count is in extra_arg
                if args.extra_arg in ['1', '2']:
                    byte_count = int(args.extra_arg)
                    mode = "READ"
                else:
                    print(f"Error: Expected 'READ', 'LOG', or byte count, got '{args.extra_arg}'")
                    sys.exit(1)
            else:
                # Mode is read or log
                mode = args.extra_arg.upper()
                # Byte count should be in next argument
                byte_count = int(args.byte_count) if args.byte_count else 2

            if mode == "READ":
                # Single read mode
                print(f"Reading from Page {page}, Address {addr_desc}, {byte_count} byte(s)")
                print("="*50)

                # Initialize I2C
                powertool = PowerToolI2C()

                # Set page
                powertool.i2c_write8PMBus(PMBusDict["PAGE"], page)

                # Read data
                if byte_count == 1:
                    data = powertool.i2c_read8PMBus(page, hex_addr)
                    print(f"Raw value (byte): 0x{data:02X} (decimal: {data})")
                    print(f"Binary: {bin(data)[2:].zfill(8)}")
                else:
                    data = powertool.i2c_read16PMBus(page, hex_addr)
                    print(f"Raw value (word): 0x{data:04X} (decimal: {data})")
                    print(f"Binary: {bin(data)[2:].zfill(16)}")
                    print(f"Low byte: 0x{data & 0xFF:02X}")
                    print(f"High byte: 0x{(data >> 8) & 0xFF:02X}")

            elif mode == "LOG":
                # Continuous logging mode
                success = continuous_register_logging(page, hex_addr, addr_desc, byte_count)
                sys.exit(0 if success else 1)

            sys.exit(0)

        except (ValueError, KeyError) as e:
            print(f"Error parsing arguments: {e}")
            print("Usage: ./powertool.py page [0/1] [ADDRESS|COMMAND] [READ|LOG] [1/2]")
            print("")
            print("ADDRESS can be:")
            print("  - Hex address: 0x8B, 8Bh, or 8B")
            print("  - English command name: READ_VOUT, STATUS_WORD, etc.")
            print("")
            print("MODE can be:")
            print("  - READ: Single read and display")
            print("  - LOG: Continuous logging to CSV file")
            print("")
            print("Examples:")
            print("  ./powertool.py page 0 READ_VOUT READ 2")
            print("  ./powertool.py page 0 READ_VOUT LOG 2")
            print("  ./powertool.py page 0 0x8B READ 2")
            print("  ./powertool.py page 1 STATUS_WORD LOG 2")
            sys.exit(1)
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)

    # Handle special modes first
    if args.rail == "log":
        # Continuous logging mode
        try:
            print("Initializing I2C connection...")
            powertool = PowerToolI2C()
            print("I2C connection successful")
            print()

            # Start continuous logging (2 minutes, 100ms sampling)
            # For quick test, use shorter duration if 'test' is second argument
            test_duration = 0.2 if args.command == "test" else 2.0
            powertool.continuous_logging(duration_minutes=test_duration, sample_rate_ms=100)

        except Exception as e:
            print(f"Error: {e}")
            print("Note: This script requires an Aardvark I2C adapter to be connected.")
        return

    elif args.rail == "test" or (args.rail is None and args.command is None):
        # Single readback test mode
        print("Single readback test mode")
        print()

        try:
            # Initialize I2C connection
            powertool = PowerToolI2C()
            print("I2C connection successful\n")

            # Test Rail1 (TSP_CORE) readback
            print("="*50)
            print("Testing TSP_CORE (Page 0) Readback:")
            print("-"*50)

            try:
                vout_rail1 = powertool.Read_Vout_Rail1()
                print(f"TSP_CORE VOUT: {vout_rail1:.4f} V")
            except Exception as e:
                print(f"Error reading TSP_CORE VOUT: {e}")

            try:
                iout_rail1 = powertool.Read_Iout_Rail1()
                print(f"TSP_CORE IOUT: {iout_rail1:.2f} A")
            except Exception as e:
                print(f"Error reading TSP_CORE IOUT: {e}")

            print()

            # Test Rail2 (TSP_C2C) readback
            print("="*50)
            print("Testing TSP_C2C (Page 1) Readback:")
            print("-"*50)

            try:
                vout_rail2 = powertool.Read_Vout_Rail2()
                print(f"TSP_C2C VOUT: {vout_rail2:.4f} V")
            except Exception as e:
                print(f"Error reading TSP_C2C VOUT: {e}")

            try:
                iout_rail2 = powertool.Read_Iout_Rail2()
                print(f"TSP_C2C IOUT: {iout_rail2:.2f} A")
            except Exception as e:
                print(f"Error reading TSP_C2C IOUT: {e}")

            print()

            # Read status for both rails
            print("="*50)
            print("Reading Status Registers:")
            print("-"*50)

            try:
                # TSP_CORE status
                powertool.i2c_write8PMBus(PMBusDict["PAGE"], 0)
                status_word_r1 = powertool.i2c_read16PMBus(0, PMBusDict["STATUS_WORD"])
                print(f"TSP_CORE STATUS_WORD: 0x{status_word_r1:04X}")

                # TSP_C2C status
                powertool.i2c_write8PMBus(PMBusDict["PAGE"], 1)
                status_word_r2 = powertool.i2c_read16PMBus(1, PMBusDict["STATUS_WORD"])
                print(f"TSP_C2C STATUS_WORD: 0x{status_word_r2:04X}")
            except Exception as e:
                print(f"Error reading status: {e}")

            print()
            print("="*50)
            print("Test completed successfully!")
            print("\nUsage examples:")
            print("  python3 powertool.py TSP_CORE READ_VOUT")
            print("  python3 powertool.py TSP_C2C READ_IOUT")
            print("  python3 powertool.py log")

        except Exception as e:
            print(f"Error: {e}")
            print("Note: This script requires an Aardvark I2C adapter to be connected.")
            print("Make sure the target device is powered and connected to address 0x5C")
        return

    # Handle single command execution (with optional continuous logging or voltage setting)
    if args.rail and args.command:
        rail = args.rail.upper()
        command = args.command.upper()

        # Handle VOUT_COMMAND (voltage setting)
        if command == "VOUT_COMMAND":
            if args.log_mode:
                try:
                    voltage = float(args.log_mode)
                    success = execute_vout_command(rail, voltage)
                    sys.exit(0 if success else 1)
                except ValueError:
                    print("Error: For VOUT_COMMAND, the third argument must be a voltage value (e.g., 0.8 for 0.8V)")
                    sys.exit(1)
            else:
                print("Error: VOUT_COMMAND requires a voltage value as third argument (e.g., 0.8 for 0.8V)")
                print("Usage: python3 powertool.py TSP_CORE VOUT_COMMAND 0.8")
                sys.exit(1)

        # Check if third argument is "log" for continuous logging
        elif args.log_mode and args.log_mode.lower() == "log":
            # Continuous logging mode for specific command
            success = continuous_single_command_logging(rail, command)
            sys.exit(0 if success else 1)
        else:
            # Single command execution
            success = execute_single_command(rail, command)
            sys.exit(0 if success else 1)
    else:
        # Show help if arguments are incomplete
        print("Error: Both rail and command arguments are required for single command execution.")
        print()
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__": main()

