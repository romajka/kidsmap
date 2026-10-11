async page=>({browser:await page.context().browser().version(),userAgent:await page.evaluate(()=>navigator.userAgent),cliSession:'module05-r1',nativeChromiumHeadless:true,physicalDevice:false})
