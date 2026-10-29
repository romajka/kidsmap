# Locale-independent place map links

Scope: Fix the shared public/detail-preview template's numeric coordinates in data attributes, coordinate text and Google/2GIS/Yandex links. No change to map destination, stored coordinates, publication or content workflow.

Root cause: raw numeric template variables are automatically localized. In Russian40.377842 becomes40,377842, creating ambiguous provider coordinate tuples. The backend directions URL already uses decimal points.

Plan executed inline under ongoing user-authorized corrections:
- Add a regression rendering actual public and unpublished staff preview pages inAZ/RU/EN; parse machine data and all three provider URLs, preserving longitude/latitude order and full precision.
- Confirm failures before the fix.
- Load Django l10n and apply unlocalize to numeric coordinates in the shared template.
- Run focused regressions plus existing preview/map coverage in isolated settings.
- Apply the narrow template release; reopen saved396/397previews in all languages, inspecting actualDOM hrefs without publishing or editing either card.
