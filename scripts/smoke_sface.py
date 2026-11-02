import numpy as np
import onnxruntime as ort
ort.set_default_logger_severity(3)

path = "models/sface/face_recognition_sface_2021dec.onnx"
sess = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
inp = sess.get_inputs()[0]
out = sess.get_outputs()[0]
print("onnxruntime:", ort.__version__)
print("input :", inp.name, inp.shape, inp.type)
print("output:", out.name, out.shape, out.type)

shape = [d if isinstance(d, int) else 1 for d in inp.shape]
x = np.random.default_rng(0).uniform(0, 255, size=shape).astype(np.float32)
y = sess.run(None, {inp.name: x})[0]
print("hasil run - shape:", y.shape, "| norma L2:", float(np.linalg.norm(y)))
