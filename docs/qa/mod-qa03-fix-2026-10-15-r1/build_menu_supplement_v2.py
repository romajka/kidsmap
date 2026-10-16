from pathlib import Path
import json,hashlib,difflib
H=Path(__file__).resolve().parent;ROOT=H.parents[2];FILE='static/admin/js/kidsmap_place_changelist.js';source=(ROOT/FILE).read_text()
anchor="    var csrftoken = getCookie('csrftoken')"
addition='''    // Row menus must escape table clipping and remain inside the viewport.
    function positionRowMenu(panel, trigger) {
      var margin = 12;
      var rect = trigger.getBoundingClientRect();
      panel.hidden = false;
      panel.style.setProperty('position', 'fixed', 'important');
      panel.style.setProperty('right', 'auto', 'important');
      panel.style.setProperty('max-width', (window.innerWidth - margin * 2) + 'px', 'important');
      panel.style.setProperty('max-height', (window.innerHeight - margin * 2) + 'px', 'important');
      panel.style.setProperty('overflow-y', 'auto');
      var size = panel.getBoundingClientRect();
      var top = rect.bottom + 6;
      if (top + size.height > window.innerHeight - margin) top = rect.top - size.height - 6;
      top = Math.max(margin, Math.min(top, window.innerHeight - size.height - margin));
      var left = Math.max(margin, Math.min(rect.right - size.width, window.innerWidth - size.width - margin));
      panel.style.setProperty('top', top + 'px', 'important');
      panel.style.setProperty('left', left + 'px', 'important');
    }

    var portaledActionMenu = null;
    function closePortaledActionMenu(restoreFocus) {
      if (!portaledActionMenu) return;
      var current = portaledActionMenu;
      portaledActionMenu = null;
      current.details.open = false;
      current.details.appendChild(current.panel);
      if (current.style === null) current.panel.removeAttribute('style');
      else current.panel.setAttribute('style', current.style);
      if (restoreFocus) current.trigger.focus({preventScroll: true});
    }

    document.addEventListener('toggle', function (event) {
      var details = event.target;
      if (!details.matches || !details.matches('details.km-admin-action-menu') || !details.closest('.km-event-changelist')) return;
      if (!details.open) {
        if (portaledActionMenu && portaledActionMenu.details === details) closePortaledActionMenu(false);
        return;
      }
      if (portaledActionMenu && portaledActionMenu.details === details) return;
      closePortaledActionMenu(false);
      var panel = details.querySelector('.km-admin-action-menu__panel');
      var trigger = details.querySelector('summary');
      if (!panel || !trigger) return;
      portaledActionMenu = { details: details, panel: panel, trigger: trigger, style: panel.getAttribute('style') };
      document.body.appendChild(panel);
      positionRowMenu(panel, trigger);
      var firstLink = panel.querySelector('a[href], button:not([disabled])');
      if (firstLink) firstLink.focus({preventScroll: true});
    }, true);

    document.addEventListener('click', function (event) {
      if (portaledActionMenu && !portaledActionMenu.panel.contains(event.target) && !portaledActionMenu.trigger.contains(event.target)) closePortaledActionMenu(false);
    });
    document.addEventListener('focusin', function (event) {
      if (portaledActionMenu && !portaledActionMenu.panel.contains(event.target) && !portaledActionMenu.trigger.contains(event.target)) closePortaledActionMenu(false);
    });
    document.addEventListener('keydown', function (event) {
      if (event.key !== 'Escape') return;
      if (portaledActionMenu) {
        event.preventDefault();
        closePortaledActionMenu(true);
      }
      if (activeMoreBtn && rowActionsDropdown && !rowActionsDropdown.hidden) {
        event.preventDefault();
        var trigger = activeMoreBtn;
        closeRowActions();
        trigger.focus({preventScroll: true});
      }
    });
    function dismissRowMenus(event) {
      if (portaledActionMenu && (!event || !portaledActionMenu.panel.contains(event.target))) closePortaledActionMenu(false);
      if (rowActionsDropdown && !rowActionsDropdown.hidden && (!event || !rowActionsDropdown.contains(event.target))) closeRowActions();
    }
    window.addEventListener('resize', dismissRowMenus);
    window.addEventListener('scroll', dismissRowMenus, true);

'''
old="""        var rect = moreBtn.getBoundingClientRect();
        rowActionsDropdown.style.position = 'fixed';
        rowActionsDropdown.style.top = (rect.bottom + 6) + 'px';
        rowActionsDropdown.style.left = Math.max(16, rect.right - 232) + 'px';
        rowActionsDropdown.hidden = false;"""
new="        positionRowMenu(rowActionsDropdown, moreBtn);"
assert source.count(anchor)==source.count(old)==1
proposed=source.replace(anchor,addition+anchor).replace(old,new)
(H/'proposed-menu-v2-kidsmap_place_changelist.js').write_text(proposed)
(H/'MENU_SUPPLEMENT_V2.diff').write_text(''.join(difflib.unified_diff(source.splitlines(True),proposed.splitlines(True),fromfile='a/'+FILE,tofile='b/'+FILE)))
manifest={'applied':False,'scope_id':'MOD-QA-03 row menu supplement','application_files':[FILE],'before_sha256':hashlib.sha256(source.encode()).hexdigest(),'proposed_sha256':hashlib.sha256(proposed.encode()).hexdigest(),'new_lines':len(addition.splitlines()),'replaced_block_lines':5,'approved_css_27lines_unchanged':True}
(H/'menu-supplement-v2-manifest.json').write_text(json.dumps(manifest,indent=2))
# Real browser will receive proposed bytes only for its own JS response, not from disk application file.
route="""let simulatedJS=null;
await c.route('**/*',async r=>{if(!r.request().url().startsWith(B+'/'))return r.abort();if(new URL(r.request().url()).pathname==='/static/admin/js/kidsmap_place_changelist.js'){const response=await r.fetch();const source=await response.text();if(!source.includes(OLD)||!source.includes(ANCHOR))throw new Error('source mismatch');simulatedJS=source.replace(ANCHOR,ADDITION+ANCHOR).replace(OLD,NEW);return r.fulfill({response,body:simulatedJS});}return r.continue();});"""
s=(H/'native-menu-safety.js').read_text();s=s.replace("await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());",'const OLD='+json.dumps(old)+',NEW='+json.dumps(new)+',ANCHOR='+json.dumps(anchor)+',ADDITION='+json.dumps(addition)+';\n'+route)
s=s.replace('safety-','menu-prototype-').replace("await c.close();return{rows,observations,mode:'actual patched CSS; native row panels, no write action selected'};", "await original.goto(B+'/ru/admin/login/');await c.close();return{rows,observations,simulated_js_sha256:await original.evaluate(async text=>Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(text)))).map(x=>x.toString(16).padStart(2,'0')).join(''),simulatedJS),mode:'SIMULATED proposed JS only through own response routing; application JS untouched, actual approved CSS'};")
(H/'native-menu-prototype-v2.js').write_text(s)
print(json.dumps(manifest))
