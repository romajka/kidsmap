"""Render a single inert JPEG outside the web worker; never serve uploaded bytes inline."""
import io
import resource
import subprocess
import sys


def pdf_command(args, data):
    return subprocess.run(args, input=data, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          check=True, timeout=4).stdout


def render_pdf(data, page, edge):
    details = pdf_command(['pdfinfo', '-'], data).decode('ascii', 'replace')
    fields = dict(line.split(':', 1) for line in details.splitlines() if ':' in line)
    if not fields.get('Encrypted', '').strip().startswith('no'):
        raise ValueError
    count = int(fields['Pages'])
    if not 1 <= page <= count:
        raise IndexError
    jpeg = pdf_command([
        'pdftoppm', '-f', str(page), '-l', str(page), '-singlefile',
        '-scale-to', str(edge), '-jpeg', '-',
    ], data)
    return count, jpeg


def render_photo(data, page, edge):
    from PIL import Image, ImageOps

    if page != 1:
        raise IndexError
    with Image.open(io.BytesIO(data), formats=['JPEG', 'PNG']) as photo:
        if photo.width * photo.height > 50_000_000 or max(photo.size) > 12000:
            raise ValueError
        photo.thumbnail((edge, edge), Image.Resampling.LANCZOS)
        upright = ImageOps.exif_transpose(photo).convert('RGBA')
        # A new canvas drops EXIF/GPS, ICC and text metadata and flattens transparency.
        clean = Image.new('RGB', upright.size, 'white')
        clean.paste(upright, mask=upright.getchannel('A'))
        stream = io.BytesIO()
        clean.save(stream, 'JPEG', quality=86)
        return 1, stream.getvalue()


def main():
    resource.setrlimit(resource.RLIMIT_AS, (512 * 1024 * 1024,) * 2)
    resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
    data = sys.stdin.buffer.read(10 * 1024 * 1024 + 1)
    if not 0 < len(data) <= 10 * 1024 * 1024:
        return
    page, edge = map(int, sys.argv[1:])
    try:
        renderer = render_pdf if data.startswith(b'%PDF-') else render_photo
        count, jpeg = renderer(data, page, edge)
    except IndexError:
        sys.stdout.buffer.write(b'no-page\n')
    else:
        sys.stdout.buffer.write(f'{count}\n'.encode('ascii'))
        sys.stdout.buffer.write(jpeg)


if __name__ == '__main__':
    main()
