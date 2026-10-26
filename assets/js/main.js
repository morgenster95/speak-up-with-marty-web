/* Speak up with Marty — interakce */
(() => {
  const $ = (s, root = document) => root.querySelector(s);
  const $$ = (s, root = document) => [...root.querySelectorAll(s)];
  const reduceMotion = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const finePointer = matchMedia('(hover: hover) and (pointer: fine)').matches;

  /* ---------- přepínač varianty (?design=pink|editorial, pamatuje se) ---------- */
  const themeButtons = $$('[data-theme]');
  function setTheme(theme) {
    document.body.classList.toggle('editorial', theme === 'editorial');
    themeButtons.forEach(b => b.setAttribute('aria-pressed', String(b.dataset.theme === theme)));
    try { localStorage.setItem('marty-design', theme); } catch {}
    const u = new URL(location.href);
    u.searchParams.set('design', theme);
    history.replaceState({}, '', u);
  }
  let initial = new URLSearchParams(location.search).get('design');
  if (!initial) { try { initial = localStorage.getItem('marty-design'); } catch {} }
  setTheme(initial === 'editorial' ? 'editorial' : 'pink');
  themeButtons.forEach(b => b.addEventListener('click', () => setTheme(b.dataset.theme)));

  /* ---------- hlavička a mobilní menu ---------- */
  const header = $('.site-header');
  const onScroll = () => header.classList.toggle('scrolled', scrollY > 10);
  addEventListener('scroll', onScroll, { passive: true });
  onScroll();

  const burger = $('.burger'), navlinks = $('#navlinks');
  burger.addEventListener('click', () => {
    const open = navlinks.classList.toggle('open');
    burger.setAttribute('aria-expanded', String(open));
  });
  $$('a', navlinks).forEach(a => a.addEventListener('click', () => {
    navlinks.classList.remove('open');
    burger.setAttribute('aria-expanded', 'false');
  }));

  /* ---------- překlady slov ---------- */
  function bindWords(root = document) {
    $$('.word', root).forEach(b => {
      b.setAttribute('aria-label', `${b.textContent} — ${b.dataset.cs}`);
      b.addEventListener('click', () => {
        const active = b.classList.contains('active');
        $$('.word.active').forEach(w => w.classList.remove('active'));
        b.classList.toggle('active', !active);
      });
    });
  }
  bindWords();
  document.addEventListener('click', e => {
    if (!e.target.closest('.word')) $$('.word.active').forEach(w => w.classList.remove('active'));
  });

  /* ---------- rozbalení lekcí ---------- */
  $$('.expand').forEach(b => b.addEventListener('click', () => {
    const open = b.closest('.lesson').classList.toggle('open');
    b.setAttribute('aria-expanded', String(open));
  }));

  /* ---------- kontaktní modal ---------- */
  const modal = $('#contact');
  $$('.contact').forEach(b => b.addEventListener('click', () => modal.showModal()));
  $('.close', modal).addEventListener('click', () => modal.close());
  modal.addEventListener('click', e => {
    if (e.target !== modal) return;
    const r = modal.getBoundingClientRect();
    if (e.clientX < r.left || e.clientX > r.right || e.clientY < r.top || e.clientY > r.bottom) modal.close();
  });

  /* ---------- formulář (pouze ukázka) ---------- */
  $('#gift-form').addEventListener('submit', e => {
    e.preventDefault();
    $('#result').textContent = '✓ Takhle bude vypadat dokončení formuláře. V ostré verzi sem naváže odeslání PDF. Teď se žádné údaje neodeslaly.';
  });

  /* ---------- konfety ---------- */
  function burst(x, y) {
    if (reduceMotion) return;
    const bits = ['✳', '♡', '★', '✦', '☺'];
    for (let i = 0; i < 14; i++) {
      const s = document.createElement('span');
      s.className = 'burst';
      s.textContent = bits[i % bits.length];
      s.style.left = `${x}px`;
      s.style.top = `${y}px`;
      s.style.color = ['#0a7a5c', '#ec8fc6', '#b98af0', '#e0b400'][i % 4];
      const a = Math.random() * Math.PI * 2, d = 60 + Math.random() * 90;
      s.style.setProperty('--bx', `${Math.cos(a) * d}px`);
      s.style.setProperty('--by', `${Math.sin(a) * d - 40}px`);
      s.style.setProperty('--br', `${Math.random() * 360 - 180}deg`);
      document.body.append(s);
      s.addEventListener('animationend', () => s.remove());
    }
  }

  /* ---------- kvíz ---------- */
  const QUIZ = [
    { q: 'Byla jsem ve fitku. Jak to říct anglicky?', a: ['I was in the fitness.', 'I was at the gym.', 'I was in the fit.'], ok: 1,
      why: '„Fitness“ je spíš obor nebo kondice. Do posilovny se chodí „to the gym“.' },
    { q: 'Jak říct „Těším se na to“?', a: ['I’m looking forward to it.', 'I’m happy on it.', 'I look forward on it.'], ok: 0,
      why: '„Look forward to“ + to, na co se těšíš. Přesně tak.' },
    { q: 'Kamarád ti platí kafe. Co mu řekneš?', a: ['You’re welcome!', 'That’s so kind of you!', 'Be my guest!'], ok: 1,
      why: '„You’re welcome“ odpovídáš na poděkování a „Be my guest“ říká ten, kdo nabízí.' },
  ];
  let qi = 0;
  const qEl = $('#quiz-q'), optEl = $('#quiz-options'), fbEl = $('#quiz-feedback'), nextEl = $('#quiz-next'), countEl = $('.quiz-count');
  function renderQuiz() {
    const item = QUIZ[qi];
    qEl.textContent = item.q;
    countEl.textContent = `${qi + 1} / ${QUIZ.length}`;
    fbEl.textContent = '';
    nextEl.hidden = true;
    optEl.replaceChildren(...item.a.map((text, i) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.textContent = text;
      b.addEventListener('click', e => {
        if (i === item.ok) {
          b.classList.add('right');
          $$('button', optEl).forEach(x => (x.disabled = true));
          fbEl.textContent = `Yes! ${item.why}`;
          nextEl.hidden = false;
          nextEl.firstChild.textContent = qi === QUIZ.length - 1 ? 'Zkusit znovu ' : 'Další otázka ';
          burst(e.clientX, e.clientY);
        } else {
          b.classList.remove('wrong');
          void b.offsetWidth;
          b.classList.add('wrong');
          fbEl.textContent = 'Skoro! Zkus to ještě jednou.';
        }
      });
      return b;
    }));
  }
  nextEl.addEventListener('click', () => { qi = (qi + 1) % QUIZ.length; renderQuiz(); });
  renderQuiz();

  /* ---------- otočné kartičky ---------- */
  $$('.flip').forEach(f => f.addEventListener('click', () => {
    f.setAttribute('aria-pressed', String(f.getAttribute('aria-pressed') !== 'true'));
  }));

  /* ---------- odhalení při scrollu ---------- */
  const io = new IntersectionObserver(entries => entries.forEach(en => {
    if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
  }), { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });
  $$('.reveal').forEach((el, i) => {
    el.style.transitionDelay = `${(i % 4) * 70}ms`;
    io.observe(el);
  });

  if (!finePointer || reduceMotion) return;

  /* ---------- parallax koláží ---------- */
  $$('[data-parallax]').forEach(box => {
    const layers = $$('.layer', box);
    box.addEventListener('pointermove', e => {
      const r = box.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      layers.forEach(l => {
        const d = parseFloat(l.dataset.depth || 1) * 18;
        l.style.transform = `translate(${x * d}px, ${y * d}px)`;
      });
    });
    box.addEventListener('pointerleave', () => layers.forEach(l => (l.style.transform = '')));
  });

  /* ---------- náklon karet lekcí ---------- */
  $$('[data-tilt]').forEach(card => {
    card.addEventListener('pointermove', e => {
      const r = card.getBoundingClientRect();
      card.style.setProperty('--ry', `${((e.clientX - r.left) / r.width - 0.5) * 6}deg`);
      card.style.setProperty('--rx', `${((e.clientY - r.top) / r.height - 0.5) * -6}deg`);
    });
    card.addEventListener('pointerleave', () => { card.style.removeProperty('--rx'); card.style.removeProperty('--ry'); });
  });

  /* ---------- přetahování samolepek ---------- */
  let z = 10;
  $$('.drag').forEach(el => {
    let sx, sy, ox, oy, moved;
    el.addEventListener('pointerdown', e => {
      if (e.button !== 0) return;
      e.preventDefault();
      el.setPointerCapture(e.pointerId);
      sx = e.clientX; sy = e.clientY;
      ox = parseFloat(el.style.getPropertyValue('--dx')) || 0;
      oy = parseFloat(el.style.getPropertyValue('--dy')) || 0;
      moved = false;
      el.classList.add('dragging');
      el.style.zIndex = ++z;
    });
    el.addEventListener('pointermove', e => {
      if (!el.hasPointerCapture(e.pointerId)) return;
      const dx = e.clientX - sx, dy = e.clientY - sy;
      if (Math.abs(dx) + Math.abs(dy) > 3) moved = true;
      el.style.setProperty('--dx', `${ox + dx}px`);
      el.style.setProperty('--dy', `${oy + dy}px`);
    });
    const end = e => {
      if (!el.hasPointerCapture(e.pointerId)) return;
      el.releasePointerCapture(e.pointerId);
      el.classList.remove('dragging');
      if (moved) document.body.classList.add('dragged-once');
    };
    el.addEventListener('pointerup', end);
    el.addEventListener('pointercancel', end);
  });
})();
