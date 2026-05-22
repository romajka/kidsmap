#!/bin/bash
# We want to insert the @media query after line 121.
head -n 121 static/admin/css/kidsmap_admin.css > temp.css
echo '' >> temp.css
echo '@media (prefers-color-scheme: dark) {' >> temp.css
echo '  html:not([data-theme="light"]) {' >> temp.css
sed -n '73,120p' static/admin/css/kidsmap_admin.css | sed 's/^/  /' >> temp.css
echo '  }' >> temp.css
echo '}' >> temp.css
tail -n +122 static/admin/css/kidsmap_admin.css >> temp.css
mv temp.css static/admin/css/kidsmap_admin.css
