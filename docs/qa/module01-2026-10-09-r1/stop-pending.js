async original=>{for(const c of original.context().browser().contexts())if(c!==original.context())await c.close();return {ownPendingContextsClosed:true};}
