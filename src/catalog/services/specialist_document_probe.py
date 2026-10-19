"""Standalone parser worker: no Django, DB, file writes or content diagnostics."""
import sys


def probe(data, suffix):
    from io import BytesIO
    import math
    import warnings

    if suffix in {'.png', '.jpg', '.jpeg'}:
        from PIL import Image
        expected = 'PNG' if suffix == '.png' else 'JPEG'
        with warnings.catch_warnings():
            warnings.simplefilter('error', Image.DecompressionBombWarning)
            with Image.open(BytesIO(data)) as image:
                if (image.format != expected or image.width * image.height > 50_000_000
                        or max(image.size) > 12000):
                    return 'invalid'
                image.verify()
            with Image.open(BytesIO(data)) as image:
                image.load()
        return 'valid'
    if suffix == '.pdf':
        from pypdf import PdfReader
        from pypdf.generic import ContentStream
        reader = PdfReader(BytesIO(data), strict=True)
        if reader.is_encrypted:
            return 'encrypted'
        if not reader.pages:
            return 'invalid'
        for page in reader.pages:
            box = page.mediabox
            if (not all(math.isfinite(float(value)) for value in box)
                    or float(box.width) <= 0 or float(box.height) <= 0):
                return 'invalid'
            contents = page.get('/Contents')
            if contents is not None:
                # Parsing operators is structural validation, never execution/rendering.
                ContentStream(contents.get_object(), reader).operations
        return 'valid'
    return 'invalid'


def main():
    # Apply limits in this fresh child, never preexec_fn in threaded Django.
    try:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024, 512 * 1024 * 1024))
        resource.setrlimit(resource.RLIMIT_CPU, (3, 3))
    except (ImportError, AttributeError, OSError, ValueError):
        print('unavailable')
        return
    try:
        data = sys.stdin.buffer.read(10 * 1024 * 1024 + 1)
        result = probe(data, sys.argv[1]) if 0 < len(data) <= 10 * 1024 * 1024 else 'invalid'
    except ImportError:
        result = 'unavailable'
    except MemoryError:
        result = 'unavailable'
    except Exception:
        result = 'invalid'
    print(result)


if __name__ == '__main__':
    main()
