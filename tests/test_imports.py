import time
print("Importing time... DONE")
start = time.time()
print("Importing tensorflow...")
import tensorflow as tf
print(f"Importing tensorflow... DONE (took {time.time() - start:.2f}s)")
print(f"Tensorflow version: {tf.__version__}")
