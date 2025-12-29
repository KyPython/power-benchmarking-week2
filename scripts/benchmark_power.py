import coremltools as ct
import time
import numpy as np

# 1. Load the model we just created
print("Loading model onto the Neural Engine...")
# 'all' allows the system to use CPU, GPU, and ANE
model = ct.models.MLModel("MobileNetV2.mlpackage", compute_units=ct.ComputeUnit.ALL)

# 2. Prepare a dummy input for inference
# MobileNetV2 expects (1, 3, 224, 224)
input_data = np.random.rand(1, 3, 224, 224).astype(np.float32)


def run_benchmark(iterations=500):
    print(f"Starting {iterations} inferences...")
    start_time = time.time()

    for i in range(iterations):
        # This is where the actual 'work' happens on the M2
        model.predict({"x_1": input_data})

    end_time = time.time()
    total_time = end_time - start_time
    avg_latency = (total_time / iterations) * 1000

    print("-" * 30)
    print(f"Total Time: {total_time:.2f} seconds")
    print(f"Avg Latency per Inference: {avg_latency:.2f} ms")
    print("-" * 30)


if __name__ == "__main__":
    # Warm up to ensure the model is loaded into silicon memory
    model.predict({"x_1": input_data})
    run_benchmark()
