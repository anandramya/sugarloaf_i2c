#!/usr/bin/env python3
"""
Calculate correct VID_STEP interpretation
"""

print("VID_STEP Interpretation Analysis")
print("="*50)

# The register shows 0xFFFF with bits [12:10] = 111 (7)
vid_code_tspc_core = 0x0AEF  # 2799
vid_code_tspc_c2c = 0x0300   # 768
actual_vout_core = 0.746      # V
actual_vout_c2c = 0.750       # V

print("\nPossible interpretations for code 111 (7):")
print("-"*50)

# Interpretation 1: 1/1024 mV means step = 1mV/1024
step1 = 1.0 / 1024  # mV
step1_v = step1 / 1000  # Convert to V
calc1_core = vid_code_tspc_core * step1_v
calc1_c2c = vid_code_tspc_c2c * step1_v
print(f"1. If 1/1024mV means 1mV/1024 = {step1:.6f}mV = {step1_v:.9f}V per step")
print(f"   TSP_CORE: {vid_code_tspc_core} × {step1_v:.9f}V = {calc1_core:.6f}V (actual: {actual_vout_core}V)")
print(f"   TSP_C2C:  {vid_code_tspc_c2c} × {step1_v:.9f}V = {calc1_c2c:.6f}V (actual: {actual_vout_c2c}V)")

# Interpretation 2: 1/1024 V means step = 1V/1024
step2 = 1.0 / 1024  # V
step2_mv = step2 * 1000  # Convert to mV
calc2_core = vid_code_tspc_core * step2
calc2_c2c = vid_code_tspc_c2c * step2
print(f"\n2. If 1/1024V means 1V/1024 = {step2_mv:.6f}mV = {step2:.9f}V per step")
print(f"   TSP_CORE: {vid_code_tspc_core} × {step2:.9f}V = {calc2_core:.6f}V (actual: {actual_vout_core}V)")
print(f"   TSP_C2C:  {vid_code_tspc_c2c} × {step2:.9f}V = {calc2_c2c:.6f}V (actual: {actual_vout_c2c}V)")

# Interpretation 3: Maybe the register is wrong and it's actually using different values
# Calculate what VID_STEP would need to be to match actual voltages
implied_step_core = actual_vout_core / vid_code_tspc_core
implied_step_c2c = actual_vout_c2c / vid_code_tspc_c2c
print(f"\n3. Implied VID_STEP from actual values:")
print(f"   TSP_CORE: {actual_vout_core}V / {vid_code_tspc_core} = {implied_step_core:.9f}V = {implied_step_core*1000:.6f}mV per step")
print(f"   TSP_C2C:  {actual_vout_c2c}V / {vid_code_tspc_c2c} = {implied_step_c2c:.9f}V = {implied_step_c2c*1000:.6f}mV per step")

# Check if it matches any standard values
print(f"\n4. Checking against standard VID_STEP values:")
standard_steps = {
    "6.25mV": 6.25/1000,
    "5mV": 5.0/1000,
    "2.5mV": 2.5/1000,
    "2mV": 2.0/1000,
    "1mV": 1.0/1000,
    "0.25mV": 0.25/1000,
    "0.5mV": 0.5/1000
}

for name, step_v in standard_steps.items():
    calc_core = vid_code_tspc_core * step_v
    calc_c2c = vid_code_tspc_c2c * step_v
    error_core = abs(calc_core - actual_vout_core)
    error_c2c = abs(calc_c2c - actual_vout_c2c)

    if error_core < 0.05:  # Within 50mV
        print(f"   ✓ TSP_CORE matches {name}: {calc_core:.4f}V (error: {error_core*1000:.2f}mV)")
    if error_c2c < 0.05:  # Within 50mV
        print(f"   ✓ TSP_C2C matches {name}: {calc_c2c:.4f}V (error: {error_c2c*1000:.2f}mV)")

print("\n" + "="*50)
print("Calculating VOUT_COMMAND for 0.6V target:")
print("-"*50)

# Using the most likely interpretations
for step_name, step_v in [("1/1024mV", 0.0009765625/1000), ("1/1024V", 1.0/1024), ("0.25mV", 0.25/1000), ("1mV", 1.0/1000)]:
    vid_code_600mv = int(0.6 / step_v)
    if vid_code_600mv <= 0xFFF:  # Check if it fits in 12 bits
        print(f"With {step_name} step ({step_v*1000000:.3f}µV):")
        print(f"  VID code = 0.6V / {step_v:.9f}V = {vid_code_600mv} (0x{vid_code_600mv:03X})")
        print(f"  Verification: {vid_code_600mv} × {step_v:.9f}V = {vid_code_600mv * step_v:.6f}V")
    else:
        print(f"With {step_name} step: VID code {vid_code_600mv} exceeds 12-bit limit (0xFFF)")
    print()