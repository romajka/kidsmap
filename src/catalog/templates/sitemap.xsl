<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="1.0"
                xmlns:html="http://www.w3.org/TR/REC-html40"
                xmlns:sitemap="http://www.sitemaps.org/schemas/sitemap/0.9"
                xmlns:xhtml="http://www.w3.org/1999/xhtml"
                xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" version="1.0" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/">
    <html lang="ru">
      <head>
        <title>XML Sitemap | KidsMap.az</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background-color: #f8fafc;
            color: #0f172a;
            margin: 0;
            padding: 30px 20px;
          }
          .container {
            max-width: 1200px;
            margin: 0 auto;
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.05), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
            overflow: hidden;
            border: 1px solid #e2e8f0;
          }
          .header {
            background: linear-gradient(135deg, #059669 0%, #047857 100%);
            color: #ffffff;
            padding: 28px 32px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 16px;
          }
          .header h1 {
            margin: 0;
            font-size: 24px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
          }
          .header p {
            margin: 6px 0 0 0;
            color: #a7f3d0;
            font-size: 14px;
          }
          .stats-badge {
            background: rgba(255, 255, 255, 0.2);
            backdrop-filter: blur(8px);
            padding: 8px 16px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 14px;
            border: 1px solid rgba(255, 255, 255, 0.3);
          }
          .filter-bar {
            padding: 16px 32px;
            background: #f1f5f9;
            border-bottom: 1px solid #e2e8f0;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 16px;
          }
          .filter-input {
            width: 100%;
            max-width: 400px;
            padding: 10px 16px;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: all 0.2s;
          }
          .filter-input:focus {
            border-color: #059669;
            box-shadow: 0 0 0 3px rgba(5, 150, 105, 0.15);
          }
          .table-wrapper {
            overflow-x: auto;
          }
          table {
            width: 100%;
            border-collapse: collapse;
            text-align: left;
            font-size: 14px;
          }
          th {
            background: #f8fafc;
            color: #475569;
            font-weight: 700;
            padding: 14px 20px;
            border-bottom: 2px solid #e2e8f0;
            text-transform: uppercase;
            font-size: 12px;
            letter-spacing: 0.05em;
          }
          td {
            padding: 12px 20px;
            border-bottom: 1px solid #f1f5f9;
            color: #334155;
          }
          tr:hover td {
            background-color: #f0fdf4;
          }
          a {
            color: #059669;
            text-decoration: none;
            font-weight: 600;
          }
          a:hover {
            text-decoration: underline;
          }
          .lang-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: 700;
            background: #e2e8f0;
            color: #475569;
            margin-right: 4px;
          }
          .lang-az { background: #dbeafe; color: #1e40af; }
          .lang-ru { background: #fee2e2; color: #991b1b; }
          .lang-en { background: #fef3c7; color: #92400e; }
          .footer {
            padding: 16px 32px;
            background: #f8fafc;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 13px;
            color: #64748b;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="header">
            <div>
              <h1>🗺️ KidsMap.az — XML Sitemap</h1>
              <p>Официальная карта сайта для поисковых систем Google и Yandex</p>
            </div>
            <div class="stats-badge">
              Всего URL в карты: <xsl:value-of select="count(sitemap:urlset/sitemap:url)"/>
            </div>
          </div>

          <div class="filter-bar">
            <input type="text" id="searchInput" class="filter-input" placeholder="🔍 Быстрый поиск по URL..." onkeyup="filterUrls()"/>
            <span style="font-size: 13px; color: #64748b; font-weight: 600;">Формат: Валидный XML с XSL-стилем</span>
          </div>

          <div class="table-wrapper">
            <table id="sitemapTable">
              <thead>
                <tr>
                  <th style="width: 50px;">#</th>
                  <th>URL Страницы</th>
                  <th style="width: 150px;">Язык / Hreflang</th>
                  <th style="width: 180px;">Дата изменения (lastmod)</th>
                </tr>
              </thead>
              <tbody>
                <xsl:for-each select="sitemap:urlset/sitemap:url">
                  <tr>
                    <td style="color: #94a3b8; font-size: 12px;"><xsl:value-of select="position()"/></td>
                    <td>
                      <a href="{sitemap:loc}" target="_blank">
                        <xsl:value-of select="sitemap:loc"/>
                      </a>
                    </td>
                    <td>
                      <xsl:for-each select="xhtml:link">
                        <xsl:variable name="hreflang" select="@hreflang"/>
                        <span>
                          <xsl:attribute name="class">
                            <xsl:text>lang-badge </xsl:text>
                            <xsl:if test="$hreflang = 'az'">lang-az</xsl:if>
                            <xsl:if test="$hreflang = 'ru'">lang-ru</xsl:if>
                            <xsl:if test="$hreflang = 'en'">lang-en</xsl:if>
                          </xsl:attribute>
                          <xsl:value-of select="@hreflang"/>
                        </span>
                      </xsl:for-each>
                      <xsl:if test="count(xhtml:link) = 0">
                        <span class="lang-badge">all</span>
                      </xsl:if>
                    </td>
                    <td style="color: #64748b; font-family: monospace; font-size: 13px;">
                      <xsl:value-of select="sitemap:lastmod"/>
                    </td>
                  </tr>
                </xsl:for-each>
              </tbody>
            </table>
          </div>

          <div class="footer">
            KidsMap.az © <script>document.write(new Date().getFullYear())</script> | Генератор XML Sitemap &amp; SEO Engine
          </div>
        </div>

        <script>
          function filterUrls() {
            var input = document.getElementById("searchInput");
            var filter = input.value.toLowerCase();
            var table = document.getElementById("sitemapTable");
            var tr = table.getElementsByTagName("tr");

            for (var i = 1; i &lt; tr.length; i++) {
              var td = tr[i].getElementsByTagName("td")[1];
              if (td) {
                var txtValue = td.textContent || td.innerText;
                if (txtValue.toLowerCase().indexOf(filter) &gt; -1) {
                  tr[i].style.display = "";
                } else {
                  tr[i].style.display = "none";
                }
              }
            }
          }
        </script>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
