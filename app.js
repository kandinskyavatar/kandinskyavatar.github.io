// Renders the sections/videos described by videos.json (see build_manifest.py).

const TOC = document.getElementById('toc');
const HOST = document.getElementById('sections');

// Attach the real source only when a card gets close to the viewport, so
// opening the page does not pull every clip at once.
const lazy = new IntersectionObserver((entries) => {
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    const v = e.target;
    if (!v.src) v.src = v.dataset.src + '#t=0.1';
    lazy.unobserve(v);
  }
}, { rootMargin: '600px 0px' });

// Only one clip plays at a time — they all have audio.
function soloPlayback(v) {
  v.addEventListener('play', () => {
    document.querySelectorAll('video').forEach((o) => { if (o !== v) o.pause(); });
  });
}

function card(item) {
  const el = document.createElement('div');
  el.className = 'card';

  const v = document.createElement('video');
  v.dataset.src = item.src;
  if (item.poster) v.poster = item.poster;
  v.controls = true;
  v.preload = 'none';
  v.playsInline = true;
  v.width = item.width;
  v.height = item.height;
  v.style.aspectRatio = `${item.width} / ${item.height}`;

  const meta = document.createElement('span');
  meta.className = 'meta';
  meta.textContent = `${item.width}×${item.height} · ${item.duration}s`;

  el.append(v, meta);
  lazy.observe(v);
  soloPlayback(v);
  return el;
}

function section(sec) {
  const el = document.createElement('section');
  el.className = 'section';
  el.id = sec.id;

  const h2 = document.createElement('h2');
  h2.textContent = sec.title;

  const blurb = document.createElement('p');
  blurb.className = 'blurb';
  blurb.textContent = sec.blurb;

  const grid = document.createElement('div');
  grid.className = 'grid';
  sec.videos.forEach((item) => grid.append(card(item)));

  el.append(h2, blurb, grid);
  return el;
}

fetch('videos.json')
  .then((r) => r.json())
  .then((data) => {
    data.sections.forEach((sec) => {
      const a = document.createElement('a');
      a.href = `#${sec.id}`;
      a.textContent = sec.title;
      TOC.append(a);
      HOST.append(section(sec));
    });
    const m = document.createElement('a');
    m.href = '#method';
    m.textContent = 'Method Overview';
    TOC.append(m);
  })
  .catch((err) => {
    HOST.textContent = 'Failed to load videos.json — run: python build_manifest.py';
    console.error(err);
  });
