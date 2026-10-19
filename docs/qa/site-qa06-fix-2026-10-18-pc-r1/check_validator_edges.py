import io,json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','validator-edges'];from runtime import *
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from catalog.services.site_media_validation import validate_site_media_upload
rows=[];png=(QA/'valid.png').read_bytes();svg=(QA/'safe.svg').read_bytes()
def check(name,raw,filename='fixture.png',mime='image/png',target=None,accepted=False,code=None):
 f=SimpleUploadedFile(filename,raw,content_type=mime);f.seek(min(3,len(raw)));original=bytes(raw)
 try:result=validate_site_media_upload(f,**(target or {'field':'logo'}));ok=True;error=None;same=result is f
 except ValidationError as exc:ok=False;error=exc.code;same=True
 rewound=f.tell()==0;unchanged=f.read()==original
 checks={'policy':ok==accepted,'rewound':rewound,'bytesUnchanged':unchanged,'sameObject':same,'errorCode':code is None or error==code}
 rows.append({'id':name,'accepted':ok,'error':error,'bytes':len(raw),'checks':checks});assert all(checks.values()),name
check('empty',b'',code='invalid_site_media')
check('bad-png',b'bad',code='invalid_site_media')
check('empty-mime',png,mime='',accepted=True)
check('generic-mime',png,mime='application/octet-stream',accepted=True)
check('uppercase-extension',png,filename='logo.PNG',accepted=True)
check('bad-mime',png,mime='text/plain',code='invalid_site_media')
check('exact-500kib',png.ljust(512000,b' '),accepted=True)
check('over-500kib',png.ljust(512001,b' '),code='site_media_size')
check('exact-2mib',png.ljust(2097152,b' '),target={'placement':'HOME_HERO'},accepted=True)
check('over-2mib',png.ljust(2097153,b' '),target={'placement':'HOME_HERO'},code='site_media_size')
b=io.BytesIO()
with Image.new('RGB',(16,16),'green') as a,Image.new('RGB',(16,16),'blue') as z:a.save(b,'WEBP',save_all=True,append_images=[z],duration=100)
check('animated-webp',b.getvalue(),filename='animated.webp',mime='image/webp',code='invalid_site_media')
check('svg-with-valid-xml-declaration',b'<?xml version="1.0" encoding="UTF-8"?>'+svg,filename='safe.svg',mime='image/svg+xml',accepted=True)
check('svg-malformed-xml-declaration',b'<?xml bad?>'+svg,filename='bad.svg',mime='image/svg+xml',code='unsafe_site_svg')
check('svg-non-utf8-declaration',b'<?xml version="1.0" encoding="ISO-8859-1"?>'+svg,filename='bad.svg',mime='image/svg+xml',code='unsafe_site_svg')
check('svg-depth65',b'<svg xmlns="http://www.w3.org/2000/svg">'+b'<g>'*64+b'</g>'*64+b'</svg>',filename='deep.svg',mime='image/svg+xml',code='unsafe_site_svg')
check('svg-node-budget',b'<svg xmlns="http://www.w3.org/2000/svg">'+b'<g/>'*20000+b'</svg>',filename='many.svg',mime='image/svg+xml',code='unsafe_site_svg')
check('svg-attribute-budget',b'<svg xmlns="http://www.w3.org/2000/svg"><path d="'+b' '*65537+b'"/></svg>',filename='long.svg',mime='image/svg+xml',code='unsafe_site_svg')
check('svg-nonfinite-size',svg.replace(b'width="40"',b'width="NaN"'),filename='nan.svg',mime='image/svg+xml',code='invalid_site_media')
(QA/'validator-edges.json').write_text(json.dumps({'rows':rows,'unsafe_svg':'server-only; never browser-loaded','database_writes':False},indent=2));print(json.dumps({'rows':len(rows),'checks':sum(len(x['checks']) for x in rows),'all_pass':True}))
