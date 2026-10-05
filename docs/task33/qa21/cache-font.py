"""Optional setup download of public font; runtime browser transport is local."""
import pathlib
import re
import urllib.request
root = pathlib.Path('/root/task33-browser-tools')
source = urllib.request.urlopen('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded').read().decode()
url = re.search(r'url\((https[^)]+)\)', source).group(1)
urllib.request.urlretrieve(url, root / 'material.ttf')
(root / 'material.css').write_text(source.replace(url, 'https://kidsmap.az/qa-font.ttf'))
