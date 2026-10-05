async page => {
 return page.locator('#result_list tbody tr').first().evaluate(e=>Array.from(e.querySelectorAll('td,th')).map(c=>({class:c.className,style:c.getAttribute('style'),height:c.getBoundingClientRect().height,width:c.getBoundingClientRect().width,visibility:getComputedStyle(c).visibility,display:getComputedStyle(c).display,children:Array.from(c.children).map(x=>({class:x.className,display:getComputedStyle(x).display,width:x.getBoundingClientRect().width,height:x.getBoundingClientRect().height,whiteSpace:getComputedStyle(x).whiteSpace}))})));
}
