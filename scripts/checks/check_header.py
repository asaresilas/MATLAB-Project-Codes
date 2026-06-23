
file_path = r"d:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/Induction_Motor_Fault_Data/x1z/x1.np"

with open(file_path, 'rb') as f:
    header = f.read(16)
    print(f"Header bytes: {header}")
    print(f"Hex: {header.hex()}")
