import torch
import torchvision.models as models
import time
import subprocess
import statistics

def run_inference_batch(model, input_tensor, num_inferences=100):
    """Run multiple inferences and measure time."""
    start_time = time.time()
    
    with torch.no_grad():
        for _ in range(num_inferences):
            _ = model(input_tensor)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / num_inferences
    
    return total_time, avg_time

# Load model
print("Loading MobileNetV2...")
model = models.mobilenet_v2(weights='DEFAULT')
model.eval()

dummy_input = torch.randn(1, 3, 224, 224)

# Warmup
print("Warming up...")
with torch.no_grad():
    for _ in range(10):
        _ = model(dummy_input)

# Benchmark: High Performance Mode
print("\n=== HIGH PERFORMANCE MODE ===")
print("Running 100 inferences...")
hp_total_time, hp_avg_time = run_inference_batch(model, dummy_input, 100)

print(f"Total time: {hp_total_time:.4f}s")
print(f"Average time per inference: {hp_avg_time*1000:.2f}ms")
print(f"Throughput: {1/hp_avg_time:.2f} inferences/sec")

# TODO: Add low power mode benchmark
# TODO: Calculate energy estimates

print("\n✅ Benchmark complete!")