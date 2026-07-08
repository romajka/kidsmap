from django.apps import AppConfig


class CatalogConfig(AppConfig):
    name = 'catalog'
    verbose_name = 'Каталог'

    def ready(self):
        self._patch_jazzmin_paginator()
        
    def _patch_jazzmin_paginator(self):
        """
        Monkeypatch Jazzmin's paginator to work with Django 5+.
        format_html without arguments is not allowed in Django 5+.
        """
        try:
            import jazzmin.templatetags.jazzmin as jazzmin_tags
            from django.contrib.admin.views.main import PAGE_VAR
            from django.utils.safestring import mark_safe
            
            def patched_paginator_number(change_list, i):
                html_str = ""
                start = i == 1
                end = i == change_list.paginator.num_pages
                spacer = i in (".", "…")
                current_page = i == change_list.page_num

                if start:
                    link = change_list.get_query_string({PAGE_VAR: change_list.page_num - 1}) if change_list.page_num > 1 else "#"
                    html_str += """
                    <li class="page-item previous {disabled}">
                        <a class="page-link" href="{link}" data-dt-idx="0" tabindex="0">«</a>
                    </li>
                    """.format(link=link, disabled="disabled" if link == "#" else "")

                if current_page:
                    html_str += """
                    <li class="page-item active">
                        <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">{num}</a>
                    </li>
                    """.format(num=i)
                elif spacer:
                    html_str += """
                    <li class="page-item">
                        <a class="page-link" href="javascript:void(0);" data-dt-idx="3" tabindex="0">… </a>
                    </li>
                    """
                else:
                    query_string = change_list.get_query_string({PAGE_VAR: i})
                    end_class = "end" if end else ""
                    html_str += """
                        <li class="page-item">
                        <a href="{query_string}" class="page-link {end_class}" data-dt-idx="3" tabindex="0">{num}</a>
                        </li>
                    """.format(num=i, query_string=query_string, end_class=end_class)

                if end:
                    link = change_list.get_query_string({PAGE_VAR: change_list.page_num + 1}) if change_list.page_num < i else "#"
                    html_str += """
                    <li class="page-item next {disabled}">
                        <a class="page-link" href="{link}" data-dt-idx="7" tabindex="0">»</a>
                    </li>
                    """.format(link=link, disabled="disabled" if link == "#" else "")

                return mark_safe(html_str)
            
            jazzmin_tags.jazzmin_paginator_number = patched_paginator_number
            jazzmin_tags.register.simple_tag(
                patched_paginator_number,
                name="jazzmin_paginator_number",
            )
        except ImportError:
            pass
