"""WordprocessingML text with explicit textual control preservation."""
import io
import zipfile
from xml.etree import ElementTree as ET


def paragraph_text(paragraph):
    controls={'tab':'\t','br':'\n','cr':'\n','noBreakHyphen':'\u2011','softHyphen':'\u00ad'}
    values=[]
    for node in paragraph.iter():
        tag=node.tag.rsplit('}',1)[-1]
        if tag=='t':values.append(node.text or '')
        elif tag in controls:values.append(controls[tag])
    return ''.join(values)


def docx_source_text(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:root=ET.fromstring(z.read('word/document.xml'))
    texts=[paragraph_text(p) for p in root.iter() if p.tag.rsplit('}',1)[-1]=='p']
    return '\n'.join(t.strip() for t in texts if t.strip())
