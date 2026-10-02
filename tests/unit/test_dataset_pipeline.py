import pytest
from scripts.dataset_pipeline import classify_coverage, sections
from scripts.dataset_spatial_pipeline import strict_srid


def test_profile_and_partial_hash_do_not_prove_extraction():
    docs=[dict(source_sha256='a',document_type='dataset_profile',chunks=1,embedded=1),
          dict(source_sha256='partial:b',document_type='law',chunks=9,embedded=9)]
    assert classify_coverage('a',docs)['status']=='PROFILE_ONLY'
    assert classify_coverage('b',docs)['status']=='MISSING'
    docs.append(dict(source_sha256='a',document_type='dataset_source_text',chunks=4,embedded=2))
    result=classify_coverage('a',docs)
    assert result['chunks']==4 and result['embedded']==2
    assert result['status']=='CONTENT_PRESENT_COMPLETENESS_UNVERIFIED'


def test_unknown_and_projected_wgs84_do_not_default_to_lonlat():
    for wkt in ['', 'PROJCS["WGS 84 / UTM zone 52N"]','unrecognized']:
        with pytest.raises(ValueError):strict_srid(wkt)


def test_korean_crs_requires_all_parameters():
    wkt='PROJCS["Korea_2000",SPHEROID["GRS_1980",6378137,298.257222101],PROJECTION["Transverse_Mercator"],PARAMETER["False_Easting",1000000],PARAMETER["False_Northing",2000000],PARAMETER["Central_Meridian",127.5],PARAMETER["Latitude_Of_Origin",38],PARAMETER["Scale_Factor",0.9996]]'
    assert strict_srid(wkt)==5179
    with pytest.raises(ValueError):strict_srid(wkt.replace('127.5','129'))


def test_hml_excludes_binary_payload_and_keeps_text_locator(tmp_path):
    path=tmp_path/'source.hml'
    path.write_text('<HWPML><BINDATA>not body base64</BINDATA><P><CHAR>항로표지 원문</CHAR></P></HWPML>',encoding='utf-8')
    rows=list(sections(path))
    assert len(rows)==1 and rows[0][1]=='항로표지 원문' and 'CHAR' in rows[0][0]
