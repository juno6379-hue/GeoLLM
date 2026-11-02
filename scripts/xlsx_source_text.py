"""Decode XLSX cells instead of indexing sharedStrings as document prose.

This is a source-cell representation, not Excel display formatting. Formulas are
never evaluated; cached values and style IDs remain explicitly labelled.
"""
import io
import posixpath
import zipfile
from xml.etree import ElementTree as ET


def local(tag):
    return tag.rsplit('}',1)[-1]


def xlsx_source_text(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        shared=[]
        if 'xl/sharedStrings.xml' in z.namelist():
            root=ET.fromstring(z.read('xl/sharedStrings.xml'))
            shared=[''.join(t.text or '' for t in si.iter() if local(t.tag)=='t') for si in root if local(si.tag)=='si']
        rels={}
        if 'xl/_rels/workbook.xml.rels' in z.namelist():
            for r in ET.fromstring(z.read('xl/_rels/workbook.xml.rels')):
                if r.get('TargetMode')=='External':continue
                target=r.get('Target','')
                path=target.lstrip('/') if target.startswith('/') else posixpath.normpath('xl/'+target)
                if not path.startswith('xl/') or '..' in path.split('/'):raise ValueError('Unsafe worksheet relationship')
                rels[r.get('Id')]=path
        sheets=[]
        if 'xl/workbook.xml' in z.namelist():
            for s in ET.fromstring(z.read('xl/workbook.xml')).iter():
                if local(s.tag)=='sheet':
                    rid=next((v for k,v in s.attrib.items() if local(k)=='id'),None)
                    if rid in rels:sheets.append((s.get('name',''),rels[rid]))
        if not sheets:raise ValueError('Workbook has no resolved worksheet relationships')
        lines=['XLSX source cells; style IDs are preserved; formulas are not evaluated.']
        for name,path in sheets:
            tree=ET.fromstring(z.read(path))
            for c in tree.iter():
                if local(c.tag)!='c':continue
                value=next((n.text or '' for n in c if local(n.tag)=='v'),'')
                formula=next((n for n in c if local(n.tag)=='f'),None)
                kind=c.get('t','n')
                if kind=='s':
                    index=int(value)
                    if not 0<=index<len(shared):raise ValueError('Invalid shared string index')
                    value=shared[index]
                elif kind=='inlineStr':value=''.join(t.text or '' for t in c.iter() if local(t.tag)=='t')
                if not value and formula is None:continue
                descriptor=f"{name}!{c.get('r','?')} [type={kind}; style={c.get('s','0')}]"
                if formula is not None:
                    lines.append(f"{descriptor} formula={formula.text or ''}; cached={value or 'MISSING'}; formula_attributes={dict(formula.attrib)}")
                else:lines.append(f'{descriptor} {value}')
            for merge in tree.iter():
                if local(merge.tag)=='mergeCell':lines.append(f"{name} merged_range={merge.get('ref')}")
        return '\n'.join(lines)
