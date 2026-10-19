from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'extra-readback.py';t=p.read_text();t=t.replace('OrganizationGrant,EmailOutbox','OrganizationGrant,EmailOutbox,WorkflowNotification')
t=t.replace("rows.append(dict(key=item['key'],status=status,grants=count,passed=status=='ACCEPTED' and count==1))", "decision=WorkflowNotification.objects.filter(event_kind='team_invitation_decision',entity_type=kind+'_team_invitation',entity_id=item['invitation_id'],entity_version=2)\n  decisions=decision.count();mails=EmailOutbox.objects.filter(notification__in=decision).count()\n  rows.append(dict(key=item['key'],status=status,grants=count,decision_count=decisions,decision_outbox_count=mails,passed=status=='ACCEPTED' and count==1 and decisions==1 and mails==1))")
t=t.replace("no_duplicate_outbox=count==cases['outbox_before']", "no_duplicate_outbox=count==cases['outbox_before']+len(cases['cases'])")
t=t.replace("extra-readback.json","extra-readback-v2.json").replace("Six invitation/grant and outbox readbacks PASS","Six invitation/grant/one-decision-each and exact+6outbox readbacks PASS")
(Q/'extra-readback-v2.py').write_text(t)
