# Editable legacy pricing notes

Scope authorized by the user's request to fix old Place cards.

Root cause: public Place uses additional_info/extra_conditions as RU-only fallbacks; the admin omits these fields. Localized fields are misleadingly placed under Location, with public additional_info described as internal notes. The price disclaimer is unconditional when pricing exists.

1. Add regression tests for form visibility, snapshot/clear behavior and translated public rendering.
2. Include both legacy fields in admin fieldsets and shared content snapshots. Preserve moderation, conflict tokens and audit behavior. Move all note controls into pricing; explain RU fallback and clearing both values. Preserve language isolation and line breaks.
3. Explain the automatic disclaimer; suppress it for the existing verified-card flag. Do not add a second verification system or infer confirmation from ownership.
4. Run focused isolated Django tests and checks; inspect local Firefox pricing/admin layouts in AZ/RU/EN. Record evidence and limitations. No automatic rewriting of historical user content or database cleanup.

Browser finding within this scope: AdminLocaleMiddleware forced `/admin/catalog/place/` to RU despite selecting AZ. Honor the existing language cookie for this path, as already done for volunteer/staff editors; retain RU default and explicit RU/EN URL priority. Remove fuzzy flags from the two reviewed AZ note-label translations.
