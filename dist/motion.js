(() => {
  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const ease = 'cubic-bezier(.16,1,.3,1)';
  const active = new Set();
  function animate(element, frames, options = {}) {
    if (!element || reduced.matches || document.hidden || !element.animate) return;
    element.getAnimations().forEach(a => a.cancel());
    const animation = element.animate(frames, {duration:450,easing:ease,...options});
    active.add(animation);
    animation.finished.catch(() => {}).finally(() => active.delete(animation));
  }
  function hearts(anchor, count = 6) {
    if (!anchor || reduced.matches || document.hidden) return;
    document.querySelectorAll('.love-puff').forEach(p => {p.getAnimations().forEach(a => a.cancel());p.remove();});
    const bounds = anchor.getBoundingClientRect();
    const x = bounds.left + bounds.width / 2, y = bounds.top + bounds.height / 2;
    for (let i = 0; i < count; i++) {
      const puff = document.createElement('span');
      puff.className = 'love-puff'; puff.setAttribute('aria-hidden','true');
      puff.innerHTML = '<svg viewBox="0 0 24 24"><path d="M12 21S2 15 2 8c0-6 7-7 10-2 3-5 10-4 10 2 0 7-10 13-10 13Z"/></svg>';
      puff.style.left = x + 'px'; puff.style.top = y + 'px';
      puff.style.color = ['#c6662e','#ea9846','#a84b21'][i % 3];
      document.body.append(puff);
      const spread = (i - (count - 1) / 2) * 27;
      const animation = puff.animate([
        {transform:'translate(-50%,-50%) scale(.35)',opacity:0},
        {opacity:1,offset:.18},
        {transform:`translate(calc(-50% + ${spread}px),calc(-50% - ${70 + i % 3 * 18}px)) rotate(${spread / 2}deg) scale(1)`,opacity:0}
      ], {duration:850+i%3*90,easing:'cubic-bezier(.2,.65,.3,1)'});
      active.add(animation);
      animation.finished.catch(() => {}).finally(() => {puff.remove();active.delete(animation);});
    }
  }
  function turn(direction = 1) {
    animate(document.querySelector('.daily-paper'),[
      {transform:`perspective(900px) rotateY(${direction * 6}deg) translateX(${direction * 12}px)`,opacity:.65,clipPath:'inset(0 0 3% 0 round 6px)'},
      {transform:'perspective(900px) rotateY(0deg) translateX(0)',opacity:1,clipPath:'inset(0 0 0 0 round 6px)'}
    ],{duration:420});
  }
  document.addEventListener('click', event => {
    const button = event.target.closest('button');
    if (!button || button.disabled) return;
    if (button.id === 'save-note') {
      const kept = button.getAttribute('aria-pressed') === 'true';
      animate(button,[{transform:'scale(1)'},{transform:'scale(.94)',offset:.22},{transform:'scale(1.045)',offset:.6},{transform:'scale(1)'}],{duration:400});
      if (kept) {
        hearts(button);
        animate(document.querySelector('.paper-heart'),[{transform:'scale(1) rotate(0deg)'},{transform:'scale(1.25) rotate(-12deg)',offset:.45},{transform:'scale(1) rotate(0deg)'}],{duration:600});
      }
    } else if (button.id === 'cat') {
      hearts(button,4);
      animate(button.querySelector('svg'),[{transform:'rotate(0deg) scale(1)'},{transform:'rotate(-4deg) scale(1.07)',offset:.3},{transform:'rotate(3deg) scale(1.04)',offset:.65},{transform:'rotate(0deg) scale(1)'}],{duration:650});
      animate(button.querySelector('g path:nth-child(2)'),[{transform:'rotate(0deg)'},{transform:'rotate(-13deg)',offset:.4},{transform:'rotate(0deg)'}],{duration:650});
      animate(document.querySelector('#cat-message'),[{opacity:.4,transform:'translateY(4px)'},{opacity:1,transform:'translateY(0)'}],{duration:250});
    } else if (button.id === 'next' || button.id === 'previous' || button.id === 'back-today' || button.closest('#note-list') || button.dataset.view === 'today') {
      turn(button.id === 'previous' ? -1 : 1);
    } else if (button.dataset.view) {
      animate(document.querySelector('.collection-top'),[{opacity:.5,clipPath:'inset(0 0 15% 0)'},{opacity:1,clipPath:'inset(0 0 0 0)'}],{duration:300});
    }
  });
  const envelope = document.querySelector('#gift-envelope');
  function wiggle() {
    if (envelope.disabled) return;
    animate(envelope,[{transform:'rotate(0deg)'},{transform:'rotate(-5deg)',offset:.25},{transform:'rotate(4deg)',offset:.5},{transform:'rotate(-2deg)',offset:.75},{transform:'rotate(0deg)'}],{duration:650});
  }
  envelope.addEventListener('pointerenter',wiggle);
  envelope.addEventListener('focus',wiggle);
  envelope.addEventListener('click',() => {
    envelope.getAnimations().forEach(a => a.cancel());
    hearts(envelope,7);
  });
  const main = document.querySelector('main');
  new MutationObserver(() => {if (!main.hidden) turn();}).observe(main,{attributes:true,attributeFilter:['hidden']});
  function stop() {
    if (document.hidden || reduced.matches) {
      active.forEach(animation => animation.cancel());
      document.querySelectorAll('.love-puff').forEach(p => p.remove());
    }
  }
  document.addEventListener('visibilitychange',stop);
  reduced.addEventListener('change',stop);
})();
