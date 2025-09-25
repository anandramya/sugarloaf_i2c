

import time
import sys
import math
import csv
import datetime
import os

from aardvark_py import *

# PMBus register definitions (previously in Sugarloaf_Reg_Map)
PMBusDict = {
    # Standard PMBus Commands
    "PAGE": 0x00,
    "CLEAR_FAULTS": 0x03,
    "VOUT_MODE": 0x20,
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


class AardvarkI2C (object) :

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


    def Sugarloaf_Telemetry(self, page):

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

    def Sugarloaf_Telemetry_wo_phases(self,page):

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


def main():
    print("PMBus Rail Monitor - MP29816-C Controller")
    print(f"Target slave address: 0x{SLAVE_ADDR:02X}")
    print("=" * 60)

    # Check command line arguments
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "log":
        # Continuous logging mode
        try:
            print("Initializing I2C connection...")
            Sugarloaf = AardvarkI2C()
            print("I2C connection successful")
            print()

            # Start continuous logging (2 minutes, 100ms sampling)
            # For quick test, use shorter duration
            test_duration = 0.2 if len(sys.argv) > 2 and sys.argv[2] == "test" else 2.0
            Sugarloaf.continuous_logging(duration_minutes=test_duration, sample_rate_ms=100)

        except Exception as e:
            print(f"Error: {e}")
            print("Note: This script requires an Aardvark I2C adapter to be connected.")

    else:
        # Single readback test mode
        print("Single readback test mode (use 'python script.py log' for continuous logging)")
        print()

        try:
            # Initialize I2C connection
            Sugarloaf = AardvarkI2C()
            print("I2C connection successful\n")

            # Test Rail1 (Page 0) readback
            print("="*50)
            print("Testing Rail1 (Page 0) Readback:")
            print("-"*50)

            try:
                vout_rail1 = Sugarloaf.Read_Vout_Rail1()
                print(f"Rail1 VOUT: {vout_rail1:.4f} V")
            except Exception as e:
                print(f"Error reading Rail1 VOUT: {e}")

            try:
                iout_rail1 = Sugarloaf.Read_Iout_Rail1()
                print(f"Rail1 IOUT: {iout_rail1:.2f} A")
            except Exception as e:
                print(f"Error reading Rail1 IOUT: {e}")

            print()

            # Test Rail2 (Page 1) readback
            print("="*50)
            print("Testing Rail2 (Page 1) Readback:")
            print("-"*50)

            try:
                vout_rail2 = Sugarloaf.Read_Vout_Rail2()
                print(f"Rail2 VOUT: {vout_rail2:.4f} V")
            except Exception as e:
                print(f"Error reading Rail2 VOUT: {e}")

            try:
                iout_rail2 = Sugarloaf.Read_Iout_Rail2()
                print(f"Rail2 IOUT: {iout_rail2:.2f} A")
            except Exception as e:
                print(f"Error reading Rail2 IOUT: {e}")

            print()

            # Read status for both rails
            print("="*50)
            print("Reading Status Registers:")
            print("-"*50)

            try:
                # Rail1 status
                Sugarloaf.i2c_write8PMBus(PMBusDict["PAGE"], 0)
                status_word_r1 = Sugarloaf.i2c_read16PMBus(0, PMBusDict["STATUS_WORD"])
                print(f"Rail1 STATUS_WORD: 0x{status_word_r1:04X}")

                # Rail2 status
                Sugarloaf.i2c_write8PMBus(PMBusDict["PAGE"], 1)
                status_word_r2 = Sugarloaf.i2c_read16PMBus(1, PMBusDict["STATUS_WORD"])
                print(f"Rail2 STATUS_WORD: 0x{status_word_r2:04X}")
            except Exception as e:
                print(f"Error reading status: {e}")

            print()
            print("="*50)
            print("Test completed successfully!")
            print("\nTo start continuous logging, run:")
            print("python3 Sugarloaf_I2C_ver2.py log")

        except Exception as e:
            print(f"Error: {e}")
            print("Note: This script requires an Aardvark I2C adapter to be connected.")
            print("Make sure the target device is powered and connected to address 0x5C")


if __name__ == "__main__": main()

