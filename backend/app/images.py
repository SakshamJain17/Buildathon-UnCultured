import base64
import io
import warnings
from PIL import Image,ImageOps,UnidentifiedImageError
from fastapi import UploadFile
from .providers import ProviderError

MAX_BYTES=8*1024*1024
Image.MAX_IMAGE_PIXELS=20_000_000

async def image_bytes(file:UploadFile):
    raw=await file.read(MAX_BYTES+1)
    if len(raw)>MAX_BYTES:
        raise ProviderError('IMAGE_TOO_LARGE','Each image must be at most 8 MB.',413)
    try:
        with warnings.catch_warnings():
            warnings.simplefilter('error',Image.DecompressionBombWarning)
            im=Image.open(io.BytesIO(raw))
            if im.format not in {'JPEG','PNG','WEBP'}:
                raise ValueError()
            if min(im.size)<128 or max(im.size)>8000:
                raise ValueError()
            im.load()
            im=ImageOps.exif_transpose(im).convert('RGB')
            im.thumbnail((1600,1600))
            out=io.BytesIO()
            im.save(out,format='JPEG',quality=90)
            return out.getvalue()
    except (UnidentifiedImageError,OSError,ValueError,Image.DecompressionBombError,Image.DecompressionBombWarning):
        raise ProviderError('INVALID_IMAGE','Upload a decodable JPEG, PNG, or WebP between 128 and 8000 pixels per side.',422)

def inline(raw):
    return {'inlineData':{'mimeType':'image/jpeg','data':base64.b64encode(raw).decode()}}

def data_uri(raw):
    return 'data:image/jpeg;base64,'+base64.b64encode(raw).decode()
