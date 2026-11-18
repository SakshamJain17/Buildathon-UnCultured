'use strict';
function brandMarkup(name='ALLURÉ'){return `<span class="brand-mark" aria-hidden="true"><svg viewBox="190 150 240 240" focusable="false"><image href="/brand/allure-logo.png" width="597" height="610"/></svg></span><span class="brand-name">${name}</span>`}
for(const el of document.querySelectorAll('.wordmark,.mobile-brand,.splash-brand,.logo')){el.classList.add('brand-lockup');el.innerHTML=brandMarkup();if(el.tagName==='A')el.setAttribute('aria-label','ALLURÉ home')}
const assistant=document.querySelector('.assistant-header strong');if(assistant){assistant.classList.add('brand-lockup');assistant.innerHTML=brandMarkup('Allure')}
