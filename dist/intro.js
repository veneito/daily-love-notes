(() => {
  const intro = document.querySelector('#gift-intro');
  const main = document.querySelector('main');
  const envelope = document.querySelector('#gift-envelope');
  const reveal = document.querySelector('#reveal-heart');
  const canvas = document.querySelector('#love-canvas');
  const reducedMotion = matchMedia('(prefers-reduced-motion: reduce)');
  let frame = 0;
  let heartActive = false;
  let width = 0, height = 0;
  const particles = Array.from({length: 420}, (_, i) => {
    const angle = i / 420 * Math.PI * 2;
    const depth = .8 + Math.random() * .2;
    return {x: 16 * Math.sin(angle) ** 3 * depth,
      y: -(13 * Math.cos(angle) - 5 * Math.cos(2 * angle) - 2 * Math.cos(3 * angle) - Math.cos(4 * angle)) * depth,
      phase: Math.random() * Math.PI * 2, size: .65 + Math.random() * 1.5};
  });
  const context = canvas.getContext('2d');
  function resize() {
    const bounds = canvas.getBoundingClientRect();
    width = bounds.width; height = bounds.height;
    const ratio = Math.min(devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio);
    context?.setTransform(ratio, 0, 0, ratio, 0, 0);
  }
  function paint(time = 0) {
    if (!context) return;
    context.clearRect(0, 0, width, height);
    const scale = Math.min(width * .023, height * .012, 12);
    const pulse = reducedMotion.matches ? 1 : 1 + Math.sin(time / 950) * .035;
    const centerY = Math.min(height * .25, 225);
    for (const p of particles) {
      const shimmer = reducedMotion.matches ? .8 : .55 + .4 * Math.sin(time / 650 + p.phase);
      context.beginPath();
      context.fillStyle = `rgba(255,${Math.round(155 + shimmer * 70)},110,${.4 + shimmer * .6})`;
      context.shadowColor = '#ff8a32'; context.shadowBlur = reducedMotion.matches ? 4 : 9;
      context.arc(width / 2 + p.x * scale * pulse, centerY + p.y * scale * pulse, p.size, 0, Math.PI * 2);
      context.fill();
    }
    context.shadowBlur = 0;
  }
  function animate(time) {
    paint(time);
    if (heartActive && !document.hidden && !reducedMotion.matches) frame = requestAnimationFrame(animate);
  }
  function resume() {
    cancelAnimationFrame(frame);
    if (heartActive && !document.hidden) { resize(); animate(); }
  }
  function enter() {
    heartActive = false;
    cancelAnimationFrame(frame);
    intro.hidden = true; main.hidden = false;
    window.scrollTo(0, 0);
    const heading = document.querySelector('#title');
    heading.tabIndex = -1; heading.focus({preventScroll:true});
  }
  main.hidden = true;
  window.addEventListener('signed-in', () => {intro.hidden = false; main.hidden = true;});
  envelope.onclick = () => {
    document.querySelector('.envelope-stage').classList.add('opened');
    envelope.setAttribute('aria-expanded', 'true'); envelope.disabled = true;
    document.querySelector('#intro-letter').removeAttribute('aria-hidden');
    document.querySelector('#tap-instruction').hidden = true;
    document.querySelector('#envelope-hint').textContent = 'Just a little reminder, from me to you.';
    reveal.hidden = false;
    reveal.focus({preventScroll:true});
  };
  reveal.onclick = () => {
    document.querySelector('#envelope-scene').hidden = true;
    document.querySelector('#heart-scene').hidden = false;
    intro.classList.add('heart-mode');
    intro.setAttribute('aria-labelledby','heart-title');
    document.querySelector('.heart-copy h2').id = 'heart-title';
    heartActive = true;
    resume();
    document.querySelector('#enter-room').focus({preventScroll:true});
    window.scrollTo(0, 0);
  };
  document.querySelector('#enter-room').onclick = enter;
  document.querySelector('#skip-intro').onclick = enter;
  window.addEventListener('show-love', () => {
    main.hidden = true;
    intro.hidden = false;
    reveal.onclick();
  });
  window.addEventListener('resize', resume);
  document.addEventListener('visibilitychange', resume);
  reducedMotion.addEventListener('change', resume);
})();
