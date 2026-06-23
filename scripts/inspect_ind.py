import scipy.io
import os

path = 'd:/Silas Document/UMaT/Year 4/Project work/Matlab_Project codes/datasets/Induction_Motor/struct_rs_R1.mat'
print(f"Inspecting {path}...")
try:
    mat = scipy.io.loadmat(path, variable_names=['struct_rs_R1']) # Try to load just the main struct if known
    print("Keys found in mat file:", mat.keys())
    
    # Let's try to find the variable
    for key in mat.keys():
        if not key.startswith('__'):
            data = mat[key]
            print(f"\nStructure for key '{key}':")
            print(f"Type: {type(data)}")
            if hasattr(data, 'dtype'):
                print(f"Dtype names: {data.dtype.names}")
            break
except Exception as e:
    print(f"Error: {e}")
    # If it fails, maybe it's a v7.3 mat file (HDF5)
    print("Trying h5py...")
    import h5py
    try:
        with h5py.File(path, 'r') as f:
            print("H5 Keys:", list(f.keys()))
            for key in f.keys():
                print(f"Dataset {key} shape: {f[key].shape}")
    except Exception as e2:
        print(f"H5 Error: {e2}")
