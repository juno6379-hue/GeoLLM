from services.orchestrator.harbour_evidence import harbour_card, photo_path


def record():
    return {'source_id':'small_harbour:abc:365','name':'인천항(북항)',
            'properties':{'ADR_KNM':'인천','INTRODU':'손상�','FLT_STTUS':'시설 원문',
                          'PPATH':'소형선용항만/무역항/인천항(북항)/','PHOTO1_PAT':'01.jpg'},
            'provenance':{'source_sha256':'abc','source_file':'Dataset/항만.shp','damaged_fields':['INTRODU']},
            'geometry':{'type':'Point','coordinates':[126.6,37.5]}}


def test_missing_photo_not_invented_and_damaged_text_not_displayed(tmp_path):
    card=harbour_card(record(),tmp_path)
    assert card['fields']==[{'field':'FLT_STTUS','label':'시설 현황','text':'시설 원문'}]
    assert card['unavailable_fields'][0]['field']=='INTRODU'
    assert card['photos'][0]['status']=='SOURCE_ASSET_UNAVAILABLE'
    assert 'url' not in card['photos'][0]
    assert card['source_id']=='small_harbour:abc:365'
    assert card['geometry_role']=='harbour_reference_point_not_entrance'


def test_existing_source_photo_only_and_digest(tmp_path):
    row=record(); path=tmp_path/'소형선용항만/무역항/인천항(북항)/01.jpg'
    path.parent.mkdir(parents=True);path.write_bytes(b'fixture')
    photo=harbour_card(row,tmp_path)['photos'][0]
    assert photo['status']=='LOCAL_SOURCE_FILE_AVAILABLE'
    assert len(photo['sha256'])==64
    assert photo['url'].startswith('/api/v1/harbour-photo?source_id=small_harbour%3A')
    assert photo['depiction_verified'] is False


def test_untrusted_photo_paths_cannot_escape_or_fetch_remote(tmp_path):
    for prefix,name in [('../','x.jpg'),('','../x.jpg'),('https://evil/','x.jpg'),('C:/Temp/','x.jpg'),('/absolute/','x.jpg'),('','x.svg')]:
        assert photo_path({'PPATH':prefix,'PHOTO1_PAT':name},1,tmp_path) is None


def test_missing_nonspatial_guide_fields_stay_missing(tmp_path):
    card=harbour_card({'source_id':'s','name':'항','properties':{},'provenance':{}},tmp_path)
    assert card['fields']==[] and card['photos']==[]
    assert card['source_year'] is None
