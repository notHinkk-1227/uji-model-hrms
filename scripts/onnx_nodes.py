"""Baca nama dan jenis N node pertama graf ONNX tanpa paket `onnx` (pembaca protobuf minimal).

Dipakai untuk aturan normalisasi insightface (arcface_onnx.py, commit ffa12d3): bila 8 node pertama memuat
nama berawalan 'Sub'/'_minus' DAN 'Mul'/'_mul' -> mean 0, std 1 (model MXNet); selain itu mean = std = 127,5.

Format (onnx.proto): ModelProto.graph = field 7; GraphProto.node = field 1 (berulang);
NodeProto.name = field 3, NodeProto.op_type = field 4.
Pemakaian:  python scripts/onnx_nodes.py MODEL.onnx [N]
"""
import sys


def _varint(buf, i):
    shift = result = 0
    while True:
        b = buf[i]
        i += 1
        result |= (b & 0x7F) << shift
        if not b & 0x80:
            return result, i
        shift += 7


def _fields(buf, start, end):
    """Iterasi (nomor_field, tipe_wire, nilai_atau_(awal,akhir)) dalam buf[start:end]."""
    i = start
    while i < end:
        key, i = _varint(buf, i)
        num, wt = key >> 3, key & 7
        if wt == 0:
            v, i = _varint(buf, i)
            yield num, wt, v
        elif wt == 1:
            yield num, wt, None
            i += 8
        elif wt == 2:
            n, i = _varint(buf, i)
            yield num, wt, (i, i + n)
            i += n
        elif wt == 5:
            yield num, wt, None
            i += 4
        else:
            raise ValueError(f"tipe wire tidak didukung: {wt}")


def first_nodes(path, n=8):
    with open(path, "rb") as f:
        buf = memoryview(f.read())
    graph = next(((a, b) for num, wt, v in _fields(buf, 0, len(buf)) if num == 7 and wt == 2 for a, b in [v]), None)
    if graph is None:
        raise ValueError("graph (field 7) tidak ditemukan")
    nodes = []
    for num, wt, v in _fields(buf, *graph):
        if num == 1 and wt == 2:
            name = op = ""
            for fn, fwt, fv in _fields(buf, *v):
                if fn == 3 and fwt == 2:
                    name = bytes(buf[fv[0]:fv[1]]).decode("utf-8", "replace")
                elif fn == 4 and fwt == 2:
                    op = bytes(buf[fv[0]:fv[1]]).decode("utf-8", "replace")
            nodes.append((name, op))
            if len(nodes) >= n:
                break
    return nodes


def insightface_norm(nodes):
    """Aturan arcface_onnx.py insightface: (mean, std)."""
    sub = any(nm.startswith("Sub") or nm.startswith("_minus") for nm, _ in nodes)
    mul = any(nm.startswith("Mul") or nm.startswith("_mul") for nm, _ in nodes)
    return (0.0, 1.0) if (sub and mul) else (127.5, 127.5)


if __name__ == "__main__":
    p = sys.argv[1]
    nodes = first_nodes(p, int(sys.argv[2]) if len(sys.argv) > 2 else 8)
    for k, (nm, op) in enumerate(nodes):
        print(f"{k}: name={nm!r} op_type={op!r}")
    print("aturan insightface -> (mean, std) =", insightface_norm(nodes))
