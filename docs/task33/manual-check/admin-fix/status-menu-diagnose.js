async page => {
 return page.locator('.km-status-tabs__more, .km-status-tabs__dropdown, .km-status-tabs').evaluateAll(es=>es.map(e=>({class:e.className,open:e.open,rect:{x:e.getBoundingClientRect().x,width:e.getBoundingClientRect().width,right:e.getBoundingClientRect().right},css:{left:getComputedStyle(e).left,right:getComputedStyle(e).right,minWidth:getComputedStyle(e).minWidth,display:getComputedStyle(e).display},viewport:innerWidth,scroll:document.documentElement.scrollWidth})));
}
