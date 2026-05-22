import re

file_path = "src/catalog/templates/pages/home.html"

with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Extract the search panel
search_panel_match = re.search(r'(<div class="home-hero-search-panel">.*?</form>\s*</div>)', content, re.DOTALL)
search_panel_html = search_panel_match.group(1) if search_panel_match else ""

# 2. Extract the stats
stats_match = re.search(r'(<div class="home-hero-stats"[^>]*>.*?</div>\s*</div>)', content, re.DOTALL)
stats_html = stats_match.group(1) if stats_match else ""

# 3. Restructure the hero copy
# Replace the original home-hero-grid div start
content = re.sub(
    r'<div class="home-hero-grid">.*?<p class="home-hero-eyebrow">',
    r'<div class="home-hero-content-centered">\n      <div class="home-hero-copy">\n        <p class="home-hero-eyebrow">',
    content,
    flags=re.DOTALL,
    count=1
)

# Remove the original stats and search panel from their old locations
content = content.replace(stats_html, "")
content = content.replace(search_panel_html, "")

# Insert the search panel and stats right after the subtitle
content = re.sub(
    r'(<p>{{ hero_subtitle }}</p>)',
    r'\1\n\n        ' + search_panel_html + '\n\n        ' + stats_html,
    content,
    count=1
)

# Fix the closing tags for home-hero-copy
content = re.sub(
    r'(<div class="home-hero-stats".*?</div>\s*</div>)',
    r'\1\n      </div>\n    </div>',
    content,
    flags=re.DOTALL,
    count=1
)

# Let's just wrap the visual part
content = re.sub(
    r'(\{% if hero_gallery_slides %\})',
    r'\1',
    content,
    count=1
)

# 4. Insert the new Bento Categories section right after the hero section
bento_html = """
  <section class="panel home-bento-categories animate-on-scroll">
    <div class="home-bento-head">
      <h2>{% trans "Выберите направление" %}</h2>
    </div>
    <div class="bento-grid">
      {% for item in home_categories %}
        <a href="{% url 'place_list' %}?category={{ item.code }}" class="bento-card bento-category-{{ item.code }}">
          <div class="bento-icon">
            {% include "catalog/includes/category_icon.html" with category=item.code %}
          </div>
          <span class="bento-title">{% trans item.title %}</span>
          <span class="bento-arrow" aria-hidden="true">→</span>
        </a>
      {% endfor %}
    </div>
  </section>
"""

content = re.sub(
    r'(</section>\s*)\{% if map_places %\}',
    r'\1' + bento_html + '\n  {% if map_places %}',
    content,
    count=1
)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Successfully rewrote home.html")
