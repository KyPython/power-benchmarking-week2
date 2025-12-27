import torch
import torchvision
import coremltools as ct

# 1. Load a pre-trained MobileNetV2 from TorchVision
torch_model = torchvision.models.mobilenet_v2(weights="MobileNet_V2_Weights.DEFAULT")
torch_model.eval()

# 2. Create dummy input (1 image, 3 color channels, 224x224 pixels)
example_input = torch.rand(1, 3, 224, 224)

# 3. Trace the model (captures the math operations)
traced_model = torch.jit.trace(torch_model, example_input)

# 4. Convert to CoreML
# We'll use 'mlprogram' which is the modern format for M2 chips
model = ct.convert(
    traced_model,
    inputs=[ct.TensorType(shape=example_input.shape)],
    convert_to="mlprogram" 
)

# 5. Save it
model.save("MobileNetV2.mlpackage")
print("✅ Success! Model saved as MobileNetV2.mlpackage")