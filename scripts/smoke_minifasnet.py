import os, sys, torch
import torch.nn.functional as F

sys.path.insert(0, "repositories/Silent-Face-Anti-Spoofing")
from src.model_lib.MiniFASNet import MiniFASNetV2, MiniFASNetV1SE
from src.utility import get_kernel, parse_model_name

MAP = {"MiniFASNetV2": MiniFASNetV2, "MiniFASNetV1SE": MiniFASNetV1SE}
d = "repositories/Silent-Face-Anti-Spoofing/resources/anti_spoof_models"
print("torch:", torch.__version__)
total = torch.zeros(1, 3)
for name in sorted(os.listdir(d)):
    h, w, mtype, scale = parse_model_name(name)
    k = get_kernel(h, w)
    model = MAP[mtype](conv6_kernel=k)
    sd = torch.load(os.path.join(d, name), map_location="cpu", weights_only=True)
    if next(iter(sd)).startswith("module."):
        sd = {key[7:]: v for key, v in sd.items()}
    model.load_state_dict(sd)
    model.eval()
    n_params = sum(p.numel() for p in model.parameters())
    x = torch.rand(1, 3, h, w) * 255
    with torch.no_grad():
        out = F.softmax(model(x), dim=1)
    total += out
    print(name, "| tipe:", mtype, "| skala:", scale, "| input:", (h, w),
          "| kernel:", k, "| param:", n_params, "| output:", tuple(out.shape),
          "| jumlah probabilitas:", float(out.sum()))
print("jumlah dua model, shape:", tuple(total.shape))
