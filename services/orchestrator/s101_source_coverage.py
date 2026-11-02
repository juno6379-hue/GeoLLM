"""Strict read-only reconstruction of a pinned S-101 DataCoverage source ring.

This small auditor supports the explicit base-cell topology used by the pinned
coverage asset. Unsupported topology, disconnected lines and unknown orientation
fail; it never substitutes an object bounding box or repairs a polygon.
"""
import hashlib
import struct

from shapely.geometry import Polygon


def source_records(raw):
    records = {}
    pos = 0
    header = None
    crs_headers = []
    while pos < len(raw):
        leader = raw[pos:pos+24]
        length, base = int(leader[:5]), int(leader[12:17])
        fl, fp, ft = (int(chr(leader[i])) for i in (20, 21, 23))
        if length < base or pos+length > len(raw) or base < 25:
            raise ValueError('Invalid ISO8211 record boundary')
        fields = {}
        directory = raw[pos+24:pos+base-1]
        if len(directory) % (fl+fp+ft):
            raise ValueError('Invalid ISO8211 directory')
        if pos and directory[:ft].decode('ascii') not in {'DSID','CSID','PRID','CRID','CCID','SRID','FRID'}:
            pos += length
            continue
        for offset in range(0, len(directory), fl+fp+ft):
            entry = directory[offset:offset+fl+fp+ft]
            tag = entry[:ft].decode('ascii')
            size, start = int(entry[ft:ft+fl]), int(entry[ft+fl:])
            field = raw[pos+base+start:pos+base+start+size]
            if not field or field[-1] != 30:
                raise ValueError('Invalid source field')
            fields[tag] = fields.get(tag, b'') + field[:-1]
            if pos and directory[:ft] == b'CSID' and tag == 'CRSH':
                crs_headers.append(field[:-1])
        if pos:
            first = next(iter(fields))
            value = fields[first]
            if first == 'DSID':
                header = fields
            elif first in {'PRID','CRID','CCID','SRID','FRID'}:
                key = (value[0], int.from_bytes(value[1:5], 'little'))
                if key in records:
                    raise ValueError('Updates/duplicate source records unsupported')
                records[key] = fields
        pos += length
    if header is None:
        raise ValueError('Missing DSID source header')
    header['_CRSH_RECORDS'] = crs_headers
    return header, records


def reconstruct_coverage(raw, feature_record_id):
    header, records = source_records(raw)
    horizontal = [item for item in header['_CRSH_RECORDS'] if item[:3] == b'\x01\x01\x01']
    if horizontal != [b'\x01\x01\x01WGS84\x1f4326\x1f\x02\x1f']:
        raise ValueError('Explicit WGS84 EPSG:4326 source CRS required')
    ftcs = header['FTCS']; offset = 0; codes = {}
    while offset < len(ftcs):
        end = ftcs.index(b'\x1f', offset)
        code = int.from_bytes(ftcs[end+1:end+3], 'little')
        codes[code] = ftcs[offset:end].decode('utf-8'); offset = end+3
    feature = records[(100, feature_record_id)]
    if codes.get(int.from_bytes(feature['FRID'][5:7], 'little')) != 'DataCoverage':
        raise ValueError('Source feature is not DataCoverage')
    dcox, dcoy, dcoz, cmfx, cmfy, cmfz = struct.unpack('<dddIII', header['DSSI'][:36])
    if not cmfx or not cmfy:
        raise ValueError('Missing coordinate multiplier')

    def coords(payload):
        if len(payload) % 8:
            raise ValueError('Unsupported coordinate encoding')
        return [(x/cmfx+dcox, y/cmfy+dcoy) for y,x in struct.iter_unpack('<ii', payload)]

    def ref(payload):
        return payload[0], int.from_bytes(payload[1:5], 'little')

    def orient(points, orientation):
        if orientation not in (1,2):
            raise ValueError('Unknown source orientation')
        return points if orientation == 1 else list(reversed(points))

    def join(parts):
        result = []
        for points in parts:
            if result and result[-1] != points[0]:
                raise ValueError('Disconnected source topology')
            result.extend(points[1:] if result else points)
        return result

    def curve(key, seen=()):
        if key in seen:
            raise ValueError('Cyclic source topology')
        record = records[key]
        if key[0] == 120:
            ptas = record['PTAS']
            if len(ptas) != 12 or ptas[5] != 1 or ptas[11] != 2:
                raise ValueError('Unsupported endpoint topology')
            start = coords(records[ref(ptas[:6])]['C2IT'])
            end = coords(records[ref(ptas[6:])]['C2IT'])
            return start + coords(record.get('C2IL', b'')) + end
        if key[0] == 125:
            links = record['CUCO']
            if len(links) % 6:
                raise ValueError('Unsupported composite encoding')
            return join([orient(curve(ref(links[i:i+6]),seen+(key,)),links[i+5])
                         for i in range(0,len(links),6)])
        raise ValueError('Unsupported coverage topology')

    spas = feature['SPAS']
    if len(spas) != 15 or spas[0] != 130 or spas[5] != 1:
        raise ValueError('Only an explicit source surface is supported')
    surface = records[ref(spas)]
    rings = surface['RIAS']
    if len(rings) != 8 or rings[6:] != b'\x01\x01':
        raise ValueError('Only the audited single exterior ring is supported')
    points = orient(curve(ref(rings)),rings[5])
    if not points or points[0] != points[-1]:
        raise ValueError('Source ring is not closed')
    polygon = Polygon(points)
    if polygon.is_empty or not polygon.is_valid:
        raise ValueError('Invalid source polygon')
    if not (-180 <= polygon.bounds[0] <= polygon.bounds[2] <= 180 and
            -90 <= polygon.bounds[1] <= polygon.bounds[3] <= 90):
        raise ValueError('Source coordinates out of geographic bounds')
    return polygon, {'source_sha256': hashlib.sha256(raw).hexdigest(),
                     'feature_record_name':100,'feature_record_id':feature_record_id,
                     'surface_record_id':ref(spas)[1],'ring_record_id':ref(rings)[1],
                     'coordinate_count':len(points),'coordinate_multiplier':[cmfx,cmfy],
                     'coordinate_offset':[dcox,dcoy], 'feature_type':'DataCoverage',
                     'horizontal_crs':'EPSG:4326',
                     'horizontal_crs_source':'CSID/CRSH WGS84 authority code 4326',
                     'horizontal_crs_raw_hex':horizontal[0].hex(),
                     'method':'ISO8211_FRID_SPAS_RIAS_CUCO_PTAS_C2IL_C2IT_no_repair'}
