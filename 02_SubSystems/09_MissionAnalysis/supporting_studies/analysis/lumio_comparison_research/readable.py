"""Normalize compact technical prose for the authored research deliverables."""
import re
def text(value):
    if not isinstance(value,str) or value.startswith(('https://','http://')):return value
    identifiers={v:f'ZZIDENT{chr(65+i)}ZZ' for i,v in enumerate(dict.fromkeys(re.findall(r'EC\.[AS]\.\d+(?:/\d+)?',value)))}
    for value0,token in identifiers.items():value=value.replace(value0,token)
    protected={v:f'ZZMODEL{chr(65+i)}ZZ' for i,v in enumerate(['CCD201-20','CCD201','e2v','7S2P','RWp100','RWp050','LMP-103S','R134a','CubeSat'])}
    for value0,token in protected.items():value=value.replace(value0,token)
    exponents={v:f'ZZEXP{chr(65+i)}ZZ' for i,v in enumerate(dict.fromkeys(re.findall(r'\b\d+(?:\.\d+)?[eE][+-]?\d+\b',value)))}
    for value0,token in exponents.items():value=value.replace(value0,token)
    value=re.sub(r'(?<=[a-z])(?=\d)', ' ',value)
    value=re.sub(r'(?<=\d)(?![eE][+-]?\d)(?=[A-Za-z])',' ',value)
    value=re.sub(r'(?<=[a-z])(?=[A-Z])',' ',value)
    value=re.sub(r'\b(VIS|NIR|ECAPS)(?=\d)',r'\1 ',value)
    value=re.sub(r'([,;])(?=[A-Za-z])',r'\1 ',value)
    value=re.sub(r';(?=\d)',r'; ',value)
    value=re.sub(r'([.:])(?=[A-Z])',r'\1 ',value)
    value=value.replace('aboutone','about one')
    for value0,token in exponents.items():value=value.replace(token,value0)
    for value0,token in protected.items():value=value.replace(token,value0)
    for value0,token in identifiers.items():value=value.replace(token,value0)
    return value
def markup(value):
    return ''.join(t if t.startswith('<') else text(t) for t in re.split(r'(<[^>]+>)',value))
def markdown(value):
    # Preserve link targets (including local paths) and inline code exactly.
    return ''.join(t if t.startswith(('http','`','](')) else text(t) for t in re.split(r'(\]\([^)]*\)|https?://[^\s)>]+|`[^`]*`)',value))
