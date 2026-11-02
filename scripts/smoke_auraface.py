import numpy as np
import onnxruntime as ort

path = "models/auraface/glintr100.onnx"
sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0]
out = sess.get_outputs()[0]
print("onnxruntime:", ort.__version__)
print("input :", inp.name, inp.shape, inp.type)
print("output:", out.name, out.shape, out.type)

x = np.random.default_rng(0).standard_normal((1, 3, 112, 112)).astype(np.float32)
y = sess.run(None, {inp.name: x})[0]
print("hasil run - shape:", y.shape, "| norm L2:", float(np.linalg.norm(y)))
