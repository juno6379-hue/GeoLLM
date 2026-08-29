"""Parse an S-101 Feature Catalogue XML without relying on namespace prefixes."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def text_of(node, name: str) -> str | None:
    for child in node.iter():
        if local(child.tag) == name and child is not node:
            value = " ".join("".join(child.itertext()).split())
            if value:
                return value
    return None


def children(node, name: str):
    return [child for child in node if local(child.tag) == name]


def parse(path: Path) -> dict:
    raw = path.read_bytes()
    root = ET.fromstring(raw)
    attrs = []
    for node in root.iter():
        if local(node.tag) in {"S100_FC_SimpleAttribute", "S100_FC_ComplexAttribute"}:
            code = text_of(node, "code")
            name = text_of(node, "name")
            if not code and not name:
                continue
            values = []
            for listed in node.iter():
                if local(listed.tag) == "listedValue":
                    values.append({
                        "label": text_of(listed, "label"),
                        "value": text_of(listed, "value"),
                    })
            attrs.append({
                "code": code or re.sub(r"[^A-Za-z0-9]+", "_", name or "").strip("_"),
                "name": name,
                "definition": text_of(node, "definition"),
                "alias": [" ".join("".join(x.itertext()).split()) for x in node.iter() if local(x.tag) == "alias"],
                "value_type": text_of(node, "valueType"),
                "uom": text_of(node, "uom"),
                "listed_values": values,
                "source": str(path),
            })

    features = []
    for node in root.iter():
        if local(node.tag) != "S100_FC_FeatureType":
            continue
        code = text_of(node, "code")
        name = text_of(node, "name")
        if not code and not name:
            continue
        bindings = []
        for binding in node.iter():
            if local(binding.tag) in {"attributeBinding", "informationBinding", "featureBinding"}:
                ref = next((v for k, v in binding.attrib.items() if local(k) == "ref"), None)
                if ref:
                    bindings.append({"kind": local(binding.tag), "ref": ref})
        primitives = [" ".join("".join(x.itertext()).split()) for x in node.iter() if local(x.tag) == "permittedPrimitives"]
        features.append({
            "code": code,
            "name": name,
            "definition": text_of(node, "definition"),
            "aliases": [" ".join("".join(x.itertext()).split()) for x in node.iter() if local(x.tag) == "alias"],
            "permitted_primitives": primitives,
            "bindings": bindings,
            "abstract": node.attrib.get("isAbstract", "false").lower() == "true",
            "source": str(path),
        })

    metadata = {key: text_of(root, key) for key in ("name", "scope", "fieldOfApplication", "versionNumber", "versionDate", "productId")}
    metadata.update({"source": str(path), "sha256": hashlib.sha256(raw).hexdigest(), "namespace_aware": True})
    return {"metadata": metadata, "features": features, "attributes": attrs}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("xml", type=Path)
    ap.add_argument("--out", type=Path, default=Path("data/s101_feature_catalogue_v2_parsed.json"))
    args = ap.parse_args()
    parsed = parse(args.xml)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"features": len(parsed["features"]), "attributes": len(parsed["attributes"]), "output": str(args.out)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
