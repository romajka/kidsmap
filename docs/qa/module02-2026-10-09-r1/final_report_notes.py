from pathlib import Path
h=Path(__file__).parent
p=h/'REPORT.md';s=p.read_text(encoding='utf-8')
s=s.replace('[published edit / return / resubmit](published-roundtrip.result.txt)', '[published edit / return](published-roundtrip.result.txt), [correction / resubmit / approve](continue-published.result.txt)')
s=s.replace('[final access](final-access.result.txt); доступ по прямому grant сохранён.', '[revoke result](final-access.result.txt), [corrected supported-route proof](access-proof.result.txt), [informational scope / accept / revoke](informational-access.result.txt); доступ по прямому grant сохранён.')
s=s.replace('Полная свежая матрица rendered browser с языком', '288 свежих rendered states (261 PASS / 27 FAIL), 308 PNG. Матрица с языком')
s=s.replace('Новая ветка', 'Новая ветка')
s=s.replace('Визуальные подтверждённые findings и ограничения указаны', 'Подтверждённые визуальные findings и ограничения указаны')
s=s.replace('invalid fixture model fields;', 'invalid fixture model fields; singular вместо поддержанного plural edit URL; невидимое description_en поле вместо реально поддержанного description_az;')
s=s.replace('Предварительные попытки сохранены;', 'Предварительные попытки сохранены; обнаруженные hidden CSRF/recovery values в собственном первоначальном test failure log заменены [REDACTED], [redaction-log.json](redaction-log.json);')
p.write_text(s,encoding='utf-8')
p=h/'findings/ORG-QA-02.md';s=p.read_text(encoding='utf-8').replace('[revoke/access verification](../final-access.result.txt)', '[native revoke](../final-access.result.txt), [supported-route access proof](../access-proof.result.txt), [active informational scope / revoke](../informational-access.result.txt)').replace('API revoke и последующий запрет edit — PASS, независимый прямой доступ остаётся.', 'API revoke — PASS; первоначальные URL-only checks использовали ошибочный singular route и не засчитываются. Последующие проверки настоящего plural route доказывают прекращение сетевого и сохранность прямого доступа.')
p.write_text(s,encoding='utf-8')
