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


def bindings_of(node):
    result = []
    for binding in node:
        if local(binding.tag) not in {'attributeBinding','informationBinding','featureBinding','subAttributeBinding'}:
            continue
        refs = [{'type':local(c.tag),'ref':v} for c in binding
                for k,v in c.attrib.items() if local(k)=='ref']
        # Support legacy inline refs and the actual S-100 FC nested reference layout.
        if binding.get('ref'):
            refs.append({'type':'attribute','ref':binding.get('ref')})
        permitted = [c.text for p in children(binding,'permittedValues') for c in p if local(c.tag)=='value']
        multiplicity = next(iter(children(binding,'multiplicity')),None)
        for ref in refs:
            result.append({'kind':local(binding.tag), **ref, 'permitted_values':permitted,
                           'lower':text_of(multiplicity,'lower') if multiplicity is not None else None,
                           'upper':text_of(multiplicity,'upper') if multiplicity is not None else None,
                           'unbounded':any(c.get('infinite')=='true' for c in multiplicity) if multiplicity is not None else False})
    return result


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
                        "value": text_of(listed, "value") or text_of(listed, "code"),
                    })
            attrs.append({
                "code": code or re.sub(r"[^A-Za-z0-9]+", "_", name or "").strip("_"),
                "name": name,
                "definition": text_of(node, "definition"),
                "alias": [" ".join("".join(x.itertext()).split()) for x in node.iter() if local(x.tag) == "alias"],
                "value_type": text_of(node, "valueType"),
                "uom": text_of(node, "uom"),
                "listed_values": values,
                "bindings": bindings_of(node),
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
        bindings = bindings_of(node)
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
    other_types = {'S100_FC_InformationType','S100_FC_FeatureAssociation','S100_FC_InformationAssociation','S100_FC_Role'}
    other = [{'code':text_of(n,'code'),'kind':local(n.tag),'bindings':bindings_of(n)}
             for n in root.iter() if local(n.tag) in other_types]
    return {"metadata": metadata, "features": features, "attributes": attrs, 'other_types':other}


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
