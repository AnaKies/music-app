from xml.etree import ElementTree


def serialize_musicxml_document(root: ElementTree.Element) -> str:
    xml_bytes = ElementTree.tostring(root, encoding="utf-8", xml_declaration=True)
    return xml_bytes.decode("utf-8")


def ensure_xml_declaration(musicxml: str) -> str:
    stripped = musicxml.lstrip()
    if stripped.startswith("<?xml"):
        return musicxml
    return f"<?xml version='1.0' encoding='utf-8'?>\n{musicxml}"
