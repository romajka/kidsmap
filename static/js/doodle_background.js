/* KidsMap doodles: a hand-drawn background on every page — doodles on
 * "paper" made of soft dots and watercolour spots.
 *
 * Doodles live in page coordinates, so they scroll with the content and are
 * placed only in free space: headings, text, links, controls, images and
 * cards are measured once per layout change and kept clear.
 *
 * 31 hand-drawn kids' doodles (rocket, bear, whale, castle, dino…) with soft
 * colour tints, drawn from cached Path2D outlines.
 *
 * Interaction: the pointer draws a fading crayon line and sweeps doodles
 * aside like a wave (they spring back), doodles near it come alive, a click/tap on empty space drops a new doodle.
 *
 * Cost: one viewport-sized canvas, no libraries, no per-frame DOM reads.
 * Nothing runs until the browser is idle after load. Doodles float gently at
 * ~30 fps while the visitor is active, settle 25 s after the last activity,
 * and the loop stops completely in background tabs.
 */
(() => {
  'use strict';
  const canvas = document.querySelector('[data-doodles]');
  if (!canvas) return;
  let ctx;
  try { ctx = canvas.getContext('2d'); } catch (_) { return; }
  if (!ctx) return;

  const reduced = matchMedia('(prefers-reduced-motion: reduce)');
  const css = getComputedStyle(document.documentElement);
  const token = (name, fallback) => (css.getPropertyValue(name) || '').trim() || fallback;
  // Outline colours and soft tints; each doodle takes one outline and two tints.
  const COLORS = [
    token('--brand-turf', '#136f38'), token('--brand-spruce', '#0d4924'),
    token('--brand-brick', '#c94a4a'), '#b8860b', token('--brand-jungle', '#4caf50'),
  ];
  const TINTS = [token('--brand-celadon', '#a8d59b'), '#f2c14e', '#f4a3a3', '#8fd0f0', '#f59e5b'];
  const palette = n => [COLORS[n % 5], TINTS[n % 5], TINTS[(n + 2) % 5]];
  const TRAIL = [COLORS[4], '#e0a526', COLORS[2], COLORS[0]];

  // Text and controls the doodles must never sit behind.
  const PROTECTED = [
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'li', 'dt', 'dd', 'blockquote', 'figcaption',
    'label', 'legend', 'td', 'th', 'a', 'button', 'input', 'select', 'textarea', 'summary',
    'img', 'picture', 'video', 'iframe', 'svg', 'canvas:not([data-doodles])', 'form',
    '[class*="card"]', '[role="dialog"]', '.topbar', '.gm-style', '.leaflet-container', '[data-map]',
  ].join(',');
  // Clicks on these are real UI clicks, never a request for a new doodle.
  const INTERACTIVE = 'a, button, input, select, textarea, label, summary, [role="button"], [role="dialog"], [contenteditable], [data-map], .gm-style, .leaflet-container, video, iframe';

  // Line-art doodles on a 44×44 grid centred on 0,0 (SVG path syntax).
  // Each part: d = path, c = stroke colour slot (0 main, 1 accent, 2 third),
  // f = fill colour slot (soft tint), dot = filled with the stroke colour.
  const DOODLES = {
    rocket: [
      { d: 'M0 -20C9 -12 10 -1 7 9H-7C-10 -1 -9 -12 0 -20Z', f: 2 },
      { d: 'M4 -6A4 4 0 1 1 -4 -6A4 4 0 1 1 4 -6Z', f: 1 },
      { d: 'M-7 1L-13 11L-7 9M7 1L13 11L7 9', c: 0 },
      { d: 'M-4 11Q0 22 4 11', c: 1, f: 1 },
      { d: 'M-9 17L-11 20M11 16L13 19', c: 1 },
    ],
    balloon: [
      { d: 'M0 -20C10 -20 13 -11 11 -4C9 3 3 7 0 8C-3 7 -9 3 -11 -4C-13 -11 -10 -20 0 -20Z', f: 1 },
      { d: 'M-6 -13Q-7 -8 -5 -5', c: 2 },
      { d: 'M-2.5 10.5L2.5 10.5L0 8Z', dot: 1 },
      { d: 'M0 11C5 14 -5 17 0 20C3 22 1 24 -1 24' },
    ],
    plane: [
      { d: 'M-18 -1L19 -14L5 14L-1 4Z', f: 2 },
      { d: 'M19 -14L-1 4L-3 11L5 14' },
      { d: 'M-20 9Q-25 13 -22 17M-14 14Q-18 18 -14 21', c: 1 },
    ],
    kite: [
      { d: 'M0 -21L12 -5L0 11L-12 -5Z' },
      { d: 'M0 -21L12 -5L0 -5ZM0 -5L-12 -5L0 11Z', f: 1 },
      { d: 'M0 -21V11M-12 -5H12' },
      { d: 'M0 11Q6 15 0 18Q-6 21 0 24', c: 2 },
      { d: 'M-3 14L3 16.5L-3 17ZM3 20L-3 22.5L3 23Z', dot: 1 },
    ],
    bear: [
      { d: 'M-13 -6.8A6 6 0 1 1 -4.8 -15ZM13 -6.8A6 6 0 1 0 4.8 -15Z', f: 1 },
      { d: 'M0 -14C9 -14 14 -8 14 0C14 9 8 14 0 14C-8 14 -14 9 -14 0C-14 -8 -9 -14 0 -14Z', f: 2 },
      { d: 'M0 1C5 1 7 4 7 7C7 10 4 11 0 11C-4 11 -7 10 -7 7C-7 4 -5 1 0 1Z', f: 1 },
      { d: 'M-2 4.5H2L0 6.5Z', dot: 0 },
      { d: 'M0 6.5V8M-2.5 9Q0 10.5 2.5 9' },
      { d: 'M-5.5 -4A1.4 1.4 0 1 1 -5.5 -3.9ZM5.5 -4A1.4 1.4 0 1 1 5.5 -3.9Z', dot: 0 },
    ],
    duck: [
      { d: 'M-16 4C-16 15 13 15 16 4C17 -2 11 -2 7 0C9 -4 9 -15 0 -15C-8 -15 -9 -6 -5 -2C-10 -4 -16 -2 -16 4Z', f: 1 },
      { d: 'M-6 -9L-13 -6L-6 -4Z', c: 2, f: 2 },
      { d: 'M-1.5 -9A1.3 1.3 0 1 1 -1.5 -8.9Z', dot: 0 },
      { d: 'M1 4Q7 1 11 6' },
      { d: 'M-18 18Q-14 15 -10 18T-2 18T6 18T14 18', c: 2 },
    ],
    fish: [
      { d: 'M-15 0C-8 -11 6 -11 11 0C6 11 -8 11 -15 0Z', f: 1 },
      { d: 'M11 0L19 -8V8Z', f: 2 },
      { d: 'M-3 -8Q0 0 -3 8M2 -8Q5 0 2 8', c: 2 },
      { d: 'M-9 -2A1.5 1.5 0 1 1 -9 -1.9Z', dot: 0 },
      { d: 'M-19 -10A2 2 0 1 1 -19 -9.9ZM-22 -16A1.4 1.4 0 1 1 -22 -15.9Z', c: 1 },
    ],
    butterfly: [
      { d: 'M0 -2C-6 -16 -19 -16 -18 -6C-17 1 -8 2 0 -2Z', f: 1 },
      { d: 'M0 -2C6 -16 19 -16 18 -6C17 1 8 2 0 -2Z', f: 1 },
      { d: 'M0 0C-5 4 -14 8 -12 14C-10 18 -3 12 0 4ZM0 0C5 4 14 8 12 14C10 18 3 12 0 4Z', f: 2 },
      { d: 'M0 -8V12', c: 0 },
      { d: 'M0 -8Q-3 -15 -6 -17M0 -8Q3 -15 6 -17' },
      { d: 'M-11 -8A2 2 0 1 1 -11 -7.9ZM11 -8A2 2 0 1 1 11 -7.9Z', dot: 2 },
    ],
    rainbow: [
      { d: 'M-18 8A18 18 0 0 1 18 8', c: 2 },
      { d: 'M-13 8A13 13 0 0 1 13 8', c: 1 },
      { d: 'M-8 8A8 8 0 0 1 8 8', c: 0 },
      { d: 'M-22 12C-24 7 -18 4 -16 7C-15 3 -9 4 -10 9C-7 9 -7 13 -10 13H-20C-22 13 -23 12 -22 12Z', f: 2 },
      { d: 'M22 12C24 7 18 4 16 7C15 3 9 4 10 9C7 9 7 13 10 13H20C22 13 23 12 22 12Z', f: 2 },
    ],
    icecream: [
      { d: 'M-8 0L0 20L8 0Z', f: 2 },
      { d: 'M-5 4L3 12M3 4L-3 10M-1 0L5 6', c: 2 },
      { d: 'M-9 1C-13 1 -13 -7 -7 -7C-8 -14 3 -16 5 -9C11 -10 13 -2 9 1Z', f: 1 },
      { d: 'M2 -14Q4 -19 8 -20', c: 0 },
      { d: 'M4 -14A2.5 2.5 0 1 1 4 -13.9Z', dot: 1 },
      { d: 'M-5 -3h0M0 -5h0M4 -2h0', c: 0 },
    ],
    cupcake: [
      { d: 'M-11 2L-8 18H8L11 2Z', f: 2 },
      { d: 'M-5 2L-4 18M0 2V18M5 2L4 18', c: 2 },
      { d: 'M-13 2C-15 -4 -9 -6 -7 -4C-6 -9 2 -10 3 -6C7 -8 13 -5 12 2Z', f: 1 },
      { d: 'M0 -7V-14', c: 0 },
      { d: 'M0 -15C-3 -18 0 -22 0 -22C2 -19 3 -17 0 -15Z', c: 1, f: 1 },
    ],
    crayon: [
      { d: 'M-14 14L8 -8L14 -2L-8 20Z', f: 1 },
      { d: 'M8 -8L13 -17L20 -10L14 -2', f: 2 },
      { d: 'M-10 10L-4 16M3 -3L9 3', c: 0 },
      { d: 'M-20 -4Q-14 -10 -8 -6T4 -14', c: 1 },
    ],
    palette: [
      { d: 'M0 -17C11 -17 19 -9 18 0C17 7 11 7 7 6C3 5 1 9 4 12C6 15 3 18 -2 17C-12 16 -18 9 -18 0C-18 -10 -10 -17 0 -17Z', f: 2 },
      { d: 'M-8 -8A2.8 2.8 0 1 1 -8 -7.9Z', dot: 1 },
      { d: 'M1 -11A2.8 2.8 0 1 1 1 -10.9Z', dot: 2 },
      { d: 'M9 -5A2.8 2.8 0 1 1 9 -4.9Z', dot: 0 },
      { d: 'M-10 3A2.8 2.8 0 1 1 -10 3.1Z', dot: 1 },
    ],
    soccer: [
      { d: 'M16 0A16 16 0 1 1 -16 0A16 16 0 1 1 16 0Z', f: 2 },
      { d: 'M0 -6L5.7 -1.9L3.5 4.9H-3.5L-5.7 -1.9Z', dot: 0 },
      { d: 'M0 -6V-15M5.7 -1.9L14 -5M3.5 4.9L8 13M-3.5 4.9L-8 13M-5.7 -1.9L-14 -5' },
    ],
    blocks: [
      { d: 'M-18 4H-2V20H-18Z', f: 1 },
      { d: 'M2 4H18V20H2Z', f: 2 },
      { d: 'M-8 -12H8V4H-8Z', f: 1 },
      { d: 'M-14 16L-10 8L-6 16M-12.5 13H-7.5', c: 0 },
      { d: 'M6 8H11C14 8 14 12 11 12H6ZM6 12H12C15 12 15 16 12 16H6Z', c: 0 },
      { d: 'M0 -9L1.5 -5.5H5L2.2 -3.3L3.2 0.5L0 -1.8L-3.2 0.5L-2.2 -3.3L-5 -5.5H-1.5Z', dot: 0 },
    ],
    car: [
      { d: 'M-19 6V0C-19 -3 -17 -4 -14 -4L-9 -11H7L13 -4C17 -4 19 -2 19 1V6Z', f: 1 },
      { d: 'M-7 -9H-1V-4H-11ZM1 -9H6L10 -4H1Z', f: 2 },
      { d: 'M-8 6A4.5 4.5 0 1 1 -17 6A4.5 4.5 0 1 1 -8 6ZM17 6A4.5 4.5 0 1 1 8 6A4.5 4.5 0 1 1 17 6Z', f: 2 },
      { d: 'M16 -1H19', c: 1 },
      { d: 'M-24 2H-21M-25 6H-21', c: 2 },
    ],
    train: [
      { d: 'M-18 8V-6H-4V-14H6V8Z', f: 1 },
      { d: 'M-2 -12H4V-6H-2Z', f: 2 },
      { d: 'M-15 -6V-11H-10V-6', c: 0 },
      { d: 'M-12 -14C-16 -16 -14 -21 -10 -19C-9 -23 -3 -22 -4 -18', c: 2 },
      { d: 'M6 2H14L18 8H6Z', f: 2 },
      { d: 'M-9 12A4 4 0 1 1 -17 12A4 4 0 1 1 -9 12ZM5 12A4 4 0 1 1 -3 12A4 4 0 1 1 5 12Z', f: 2 },
      { d: 'M-20 18H20', c: 2 },
    ],
    boat: [
      { d: 'M-16 6H16L11 14H-11Z', f: 1 },
      { d: 'M0 6V-20' },
      { d: 'M2 -18L14 2H2Z', f: 2 },
      { d: 'M-2 -14L-12 2H-2Z', f: 1 },
      { d: 'M0 -20L6 -18L0 -16', c: 1, f: 1 },
      { d: 'M-21 18Q-17 15 -13 18T-5 18T3 18T11 18T19 18', c: 2 },
    ],
    sun: [
      { d: 'M10 0A10 10 0 1 1 -10 0A10 10 0 1 1 10 0Z', f: 1 },
      { d: 'M0 -14Q2 -17 0 -20M0 14Q-2 17 0 20M14 0Q17 2 20 0M-14 0Q-17 -2 -20 0M10 -10L14 -14M-10 10L-14 14M10 10L14 14M-10 -10L-14 -14', c: 1 },
      { d: 'M-3.5 -2.5A1.2 1.2 0 1 1 -3.5 -2.4ZM3.5 -2.5A1.2 1.2 0 1 1 3.5 -2.4Z', dot: 0 },
      { d: 'M-4 2.5Q0 6.5 4 2.5' },
      { d: 'M-7 2A1.6 1.6 0 1 1 -7 2.1ZM7 2A1.6 1.6 0 1 1 7 2.1Z', dot: 2 },
    ],
    raincloud: [
      { d: 'M-12 4C-19 4 -19 -6 -12 -6C-12 -14 -2 -17 3 -11C7 -16 16 -12 14 -5C20 -5 20 4 14 4Z', f: 2 },
      { d: 'M-8 9L-10 14M0 9L-2 14M8 9L6 14M-4 16L-6 21M4 16L2 21', c: 1 },
    ],
    sparkle: [
      { d: 'M-4 -14Q-3 -5 6 -4Q-3 -3 -4 6Q-5 -3 -14 -4Q-5 -5 -4 -14Z', f: 1 },
      { d: 'M12 4Q12.5 9 17 9.5Q12.5 10 12 15Q11.5 10 7 9.5Q11.5 9 12 4Z', f: 2 },
      { d: 'M12 -16V-10M9 -13H15', c: 2 },
      { d: 'M-14 12A1.6 1.6 0 1 1 -14 12.1Z', dot: 1 },
    ],
    heart: [
      { d: 'M0 16C-6 11 -18 4 -18 -5C-18 -12 -12 -16 -7 -15C-3 -14 -1 -11 0 -9C1 -11 3 -14 7 -15C12 -16 18 -12 18 -5C18 4 6 11 0 16Z', f: 1 },
      { d: 'M-11 -8Q-10 -11 -7 -11', c: 2 },
      { d: 'M19 -16L21 -19M22 -11H25M14 -19V-22', c: 2 },
    ],
    notes: [
      { d: 'M-10 10V-10L12 -15V5', c: 0 },
      { d: 'M-10 -4L12 -9', c: 0 },
      { d: 'M-10 10A4.5 3.5 -20 1 1 -19 11A4.5 3.5 -20 1 1 -10 10Z', f: 1 },
      { d: 'M12 5A4.5 3.5 -20 1 1 3 6A4.5 3.5 -20 1 1 12 5Z', f: 1 },
      { d: 'M17 12Q20 15 18 19', c: 2 },
    ],
    book: [
      { d: 'M0 -9C-6 -13 -13 -13 -18 -11V13C-13 11 -6 11 0 15Z', f: 2 },
      { d: 'M0 -9C6 -13 13 -13 18 -11V13C13 11 6 11 0 15Z', f: 1 },
      { d: 'M0 -9V15' },
      { d: 'M-14 -5Q-9 -7 -4 -5M-14 0Q-9 -2 -4 0M4 -5Q9 -7 14 -5M4 0Q9 -2 14 0', c: 2 },
      { d: 'M-6 -20L-5 -16M6 -20L5 -16M0 -22V-17', c: 1 },
    ],
    snail: [
      { d: 'M12 2A11 11 0 1 1 -10 2A11 11 0 1 1 12 2Z', f: 1 },
      { d: 'M1 2A5 5 0 1 1 6 7A9 9 0 0 1 -7 3A12 12 0 0 1 4 -8', c: 2 },
      { d: 'M-18 13H12C16 13 19 10 19 6C19 3 17 1 15 2', f: 2 },
      { d: 'M15 2L13 -6M18 3L20 -5' },
      { d: 'M13 -7A1.5 1.5 0 1 1 13 -6.9ZM20 -6A1.5 1.5 0 1 1 20 -5.9Z', dot: 0 },
    ],
    tree: [
      { d: 'M0 -20C9 -20 15 -13 14 -6C18 -2 15 7 8 6C5 10 -5 10 -8 6C-15 7 -18 -2 -14 -6C-15 -13 -9 -20 0 -20Z', f: 1 },
      { d: 'M-3 7V20H3V7', f: 2 },
      { d: 'M0 9L-5 4M1 11L6 5', c: 0 },
      { d: 'M-6 -9A2.5 2.5 0 1 1 -6 -8.9ZM6 -12A2.5 2.5 0 1 1 6 -11.9ZM4 -1A2.5 2.5 0 1 1 4 -0.9Z', dot: 2 },
      { d: 'M-20 20H20', c: 2 },
    ],
    castle: [
      { d: 'M-16 20V-4H-8V20M8 20V-4H16V20M-8 20V2H8V20', f: 1 },
      { d: 'M-17 -4L-12 -14L-7 -4ZM7 -4L12 -14L17 -4Z', f: 2 },
      { d: 'M-12 -14V-20L-7 -18L-12 -16M12 -14V-20L17 -18L12 -16', c: 2 },
      { d: 'M-3 20V13C-3 10 3 10 3 13V20', f: 2 },
      { d: 'M-8 2V-2H-4V2H0V-2H4V2H8V-2', c: 0 },
    ],
    pin: [
      { d: 'M0 20C-6 12 -14 4 -14 -5C-14 -14 -7 -20 0 -20C7 -20 14 -14 14 -5C14 4 6 12 0 20Z', f: 1 },
      { d: 'M0 2C-3 -1 -7 -3 -7 -7C-7 -10 -4 -11 -2 -10C-1 -9.5 0 -8.5 0 -8C0 -8.5 1 -9.5 2 -10C4 -11 7 -10 7 -7C7 -3 3 -1 0 2Z', dot: 2 },
      { d: 'M-9 22H9', c: 2 },
    ],
    whale: [
      { d: 'M-17 4C-17 -8 -4 -12 6 -8C12 -6 14 0 15 4C16 8 18 8 21 4C21 11 16 14 12 12C6 16 -4 16 -10 13C-15 11 -17 8 -17 4Z', f: 2 },
      { d: 'M-17 5C-10 9 4 9 12 6', c: 0 },
      { d: 'M-9 -3A1.5 1.5 0 1 1 -9 -2.9Z', dot: 0 },
      { d: 'M-2 -11Q-2 -16 -6 -19M-2 -11Q-1 -17 3 -19M-2 -11V-18', c: 1 },
    ],
    dino: [
      { d: 'M-16 12C-16 2 -8 -4 2 -4C6 -4 8 -8 8 -13C8 -18 18 -18 19 -12C20 -8 16 -7 13 -6C13 4 12 12 6 14H-10C-13 14 -16 14 -16 12Z', f: 1 },
      { d: 'M-16 12C-20 12 -23 8 -22 4', c: 0 },
      { d: 'M-8 14V20M2 14V20', c: 0 },
      { d: 'M-10 -2L-8 -7L-5 -3M-3 -4L0 -9L2 -4', c: 2, f: 2 },
      { d: 'M14 -13A1.3 1.3 0 1 1 14 -12.9Z', dot: 0 },
    ],
    airballoon: [
      { d: 'M0 -21C10 -21 16 -14 16 -6C16 2 7 7 5 10H-5C-7 7 -16 2 -16 -6C-16 -14 -10 -21 0 -21Z', f: 1 },
      { d: 'M0 -21C-5 -14 -5 2 -2 10M0 -21C5 -14 5 2 2 10', c: 2 },
      { d: 'M-5 10L-4 15M5 10L4 15' },
      { d: 'M-5 15H5V21H-5Z', f: 2 },
      { d: 'M-20 6Q-16 3 -12 6', c: 2 },
    ],
    planet: [
      { d: 'M10 0A10 10 0 1 1 -10 0A10 10 0 1 1 10 0Z', f: 1 },
      { d: 'M-9 -4C-20 -2 -22 4 -14 5C-6 6 10 2 16 -3C22 -8 18 -11 9 -9', c: 2 },
      { d: 'M-3 -5A2 2 0 1 1 -3 -4.9ZM4 3A1.4 1.4 0 1 1 4 3.1Z', dot: 2 },
      { d: 'M16 -18L17 -15L20 -14L17 -13L16 -10L15 -13L12 -14L15 -15Z', dot: 1 },
    ],
  };
  const NAMES = Object.keys(DOODLES);
  const PATHS = new Map();
  const path2d = d => { let p = PATHS.get(d); if (!p) { p = new Path2D(d); PATHS.set(d, p); } return p; };
  // Draw one doodle; size is half its width in CSS px, cols = [stroke, tint, tint].
  function drawDoodle(c, kind, size, cols, alpha) {
    const k = size / 20;
    c.scale(k, k);
    c.lineWidth = 2 / k;
    for (const part of DOODLES[kind]) {
      const p = path2d(part.d);
      if (part.f != null) { c.globalAlpha = alpha * .42; c.fillStyle = cols[part.f]; c.fill(p); }
      if (part.dot != null) { c.globalAlpha = alpha; c.fillStyle = cols[part.dot]; c.fill(p); continue; }
      c.globalAlpha = alpha; c.strokeStyle = cols[part.c || 0]; c.stroke(p);
    }
  }

  // ---- Paper: hand-scattered ink dots and watercolour spots ------------------
  // Dots come from one 480px tile of jittered points drawn once into a
  // pattern, so the whole field costs a single fill per frame. Only dots near
  // the cursor or inside a click ripple are drawn one by one, displaced.
  const TILE = 480;
  const paper = { dots: [], pattern: null, spots: [], splashes: [], ripples: [], curK: 0, cx: 0, cy: 0 };
  // Dot styles (canvas data-dots): soft — sparse pastel polka dots (default),
  // confetti — tiny colourful dots and dashes, grid — a tidy dotted notebook,
  // none — watercolour spots only. Steps divide TILE so the tile is seamless.
  function genDots(style) {
    let seed = 90210;
    const r = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
    const cfg = {
      soft: { step: 40, skip: .15, jit: 22, r: [1.2, 2.2], a: [.18, .32], dash: 0, col: () => '#7fb87a' },
      confetti: { step: 48, skip: .25, jit: 30, r: [1.1, 2], a: [.35, .6], dash: .32, col: () => [TINTS[0], TINTS[1], TINTS[2], TINTS[3], TINTS[4], COLORS[4]][Math.floor(r() * 6)] },
      grid: { step: 24, skip: 0, jit: 2, r: [1.05, 1.2], a: [.13, .17], dash: 0, col: () => COLORS[0] },
    }[style];
    paper.dots = [];
    if (!cfg) return;
    for (let y = 0; y < TILE; y += cfg.step) for (let x = 0; x < TILE; x += cfg.step) {
      if (r() < cfg.skip) continue;
      paper.dots.push({
        x: (x + cfg.step / 2 + (r() - .5) * cfg.jit + TILE) % TILE, y: (y + cfg.step / 2 + (r() - .5) * cfg.jit + TILE) % TILE,
        r: cfg.r[0] + r() * (cfg.r[1] - cfg.r[0]), a: cfg.a[0] + r() * (cfg.a[1] - cfg.a[0]),
        comma: r() < cfg.dash, ang: r() * 6.283, c: cfg.col(),
      });
    }
  }
  function inkDot(c, d, x, y, scale) {
    if (d.comma) {
      const l = d.r * 1.6 * scale, dx = Math.cos(d.ang) * l, dy = Math.sin(d.ang) * l;
      c.lineWidth = d.r * 1.1 * scale; c.lineCap = 'round';
      c.beginPath(); c.moveTo(x - dx, y - dy); c.lineTo(x + dx, y + dy); c.stroke();
    } else {
      c.beginPath(); c.arc(x, y, d.r * scale, 0, 6.283); c.fill();
    }
  }
  function buildPattern() {
    const canScale = typeof CanvasPattern !== 'undefined' && 'setTransform' in CanvasPattern.prototype;
    const k = canScale ? S.dpr : 1;
    const tc = document.createElement('canvas');
    tc.width = tc.height = Math.round(TILE * k);
    const t = tc.getContext('2d');
    t.scale(k, k);
    for (const d of paper.dots) {
      t.globalAlpha = d.a; t.fillStyle = t.strokeStyle = d.c;
      // Wrap dots that touch an edge so the tile repeats seamlessly.
      for (const ox of [0, d.x < 4 ? TILE : d.x > TILE - 4 ? -TILE : 0])
        for (const oy of [0, d.y < 4 ? TILE : d.y > TILE - 4 ? -TILE : 0]) inkDot(t, d, d.x + ox, d.y + oy, 1);
    }
    paper.pattern = ctx.createPattern(tc, 'repeat');
    if (canScale && k !== 1) paper.pattern.setTransform(new DOMMatrix([1 / k, 0, 0, 1 / k, 0, 0]));
  }
  const blobCache = new Map();
  // A soft, irregular watercolour blob, rendered small once and scaled up.
  function blob(seedN, color) {
    const key = seedN + color;
    if (blobCache.has(key)) return blobCache.get(key);
    let seed = 7 + seedN * 7919;
    const r = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
    const c = document.createElement('canvas'); c.width = c.height = 128;
    const g = c.getContext('2d');
    for (let i = 0; i < 5; i++) {
      const x = 64 + (r() - .5) * 46, y = 64 + (r() - .5) * 46, rad = 26 + r() * 30;
      const gr = g.createRadialGradient(x, y, 0, x, y, rad);
      gr.addColorStop(0, color); gr.addColorStop(1, 'rgba(255,255,255,0)');
      g.globalAlpha = .55 + r() * .35; g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
    }
    blobCache.set(key, c);
    return c;
  }
  function makeSpots() {
    const mobile = S.w < 700, step = mobile ? 420 : 560;
    paper.spots = [];
    for (let i = 0, y = 60; y < S.pageH + 200; i++, y += step) {
      let seed = 31 + i * 104729;
      const r = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;
      const count = r() < .45 ? 2 : 1;
      for (let k = 0; k < count; k++) {
        const side = r(), x = side < .42 ? S.w * (-.05 + r() * .25) : side < .84 ? S.w * (.8 + r() * .25) : S.w * (.3 + r() * .4);
        const rad = (mobile ? 120 : 190) + r() * (mobile ? 90 : 170);
        paper.spots.push({ x, y: y + (r() - .5) * step * .6, r: rad, n: i * 3 + k, c: TINTS[Math.floor(r() * TINTS.length)],
          a: .22 + r() * .14, ph: r() * 6.283, sp: .00018 + r() * .00016 });
      }
    }
  }
  function zones() {
    const z = [];
    if (paper.curK > .01) z.push({ x: paper.cx, y: paper.cy, r: 120 });
    for (const q of paper.ripples) z.push({ x: q.x, y: q.y, r: q.rad + 34 });
    return z;
  }
  function drawPaper() {
    const top = S.scroll, bottom = top + S.h;
    // watercolour spots (slow drift while the page is alive)
    for (const sp of paper.spots) {
      if (sp.y + sp.r < top || sp.y - sp.r > bottom) continue;
      const w = S.t * sp.sp + sp.ph, dx = Math.sin(w) * 14 * S.amb, dy = Math.cos(w * .8) * 10 * S.amb;
      ctx.globalAlpha = sp.a;
      ctx.drawImage(blob(sp.n, sp.c), sp.x - sp.r + dx, sp.y - sp.r + dy, sp.r * 2, sp.r * 2);
    }
    for (const q of paper.splashes) {
      const k = (S.t - q.t) / 700, grow = k >= 1 ? 1 : 1 - Math.pow(1 - k, 3) * Math.cos(k * 4);
      const fade = clamp(1 - (S.t - q.t - 1400) / 1600, 0, 1);
      const rad = q.r * clamp(grow, 0, 1.15);
      ctx.globalAlpha = .5 * fade;
      ctx.drawImage(blob(q.n, q.c), q.x - rad, q.y - rad, rad * 2, rad * 2);
    }
    // ink dots: one pattern fill, minus the zones drawn dot by dot
    const zs = zones();
    ctx.save();
    if (zs.length) {
      ctx.beginPath(); ctx.rect(0, top, S.w, S.h);
      for (const z of zs) { ctx.moveTo(z.x + z.r, z.y); ctx.arc(z.x, z.y, z.r, 0, 6.283); }
      ctx.clip('evenodd');
    }
    if (paper.dots.length) { ctx.globalAlpha = 1; ctx.fillStyle = paper.pattern; ctx.fillRect(0, top, S.w, S.h); }
    ctx.restore();
    if (zs.length && paper.dots.length) drawZoneDots(zs);
  }
  function drawZoneDots(zs) {
    const seen = new Set();
    for (const z of zs) {
      const tx0 = Math.floor((z.x - z.r) / TILE), tx1 = Math.floor((z.x + z.r) / TILE);
      const ty0 = Math.floor((z.y - z.r) / TILE), ty1 = Math.floor((z.y + z.r) / TILE);
      for (let ty = ty0; ty <= ty1; ty++) for (let tx = tx0; tx <= tx1; tx++) {
        for (let i = 0; i < paper.dots.length; i++) {
          const d = paper.dots[i], gx = tx * TILE + d.x, gy = ty * TILE + d.y;
          if (Math.abs(gx - z.x) > z.r || Math.abs(gy - z.y) > z.r || Math.hypot(gx - z.x, gy - z.y) > z.r) continue;
          const key = ((tx + 5000) * 8192 + (ty + 5000)) * 1024 + i;
          if (seen.has(key)) continue;
          seen.add(key);
          let ox = 0, oy = 0, glow = 0;
          if (paper.curK > .01) {
            const dx = gx - paper.cx, dy = gy - paper.cy, dist = Math.hypot(dx, dy) || .01;
            if (dist < 120) { const f = (1 - dist / 120) ** 2 * paper.curK; ox += dx / dist * f * 16; oy += dy / dist * f * 16; glow = Math.max(glow, f); }
          }
          for (const q of paper.ripples) {
            const dx = gx - q.x, dy = gy - q.y, dist = Math.hypot(dx, dy) || .01;
            const band = 1 - Math.abs(dist - q.rad) / 34;
            if (band > 0) { const f = band * q.life; ox += dx / dist * f * 11; oy += dy / dist * f * 11; glow = Math.max(glow, f); }
          }
          ctx.globalAlpha = Math.min(1, d.a + glow * .5);
          ctx.fillStyle = ctx.strokeStyle = glow > .25 ? COLORS[4] : d.c;
          inkDot(ctx, d, gx + ox, gy + oy, 1 + glow * .8);
        }
      }
    }
  }
  function stepPaper() {
    const p = S.p, moving = p.on && S.t - p.moved < 250;
    if (moving) { paper.cx = p.x; paper.cy = p.y + S.scroll; }
    paper.curK += ((moving ? 1 : 0) - paper.curK) * (moving ? .2 : .06);
    if (paper.curK < .01 && !moving) paper.curK = 0;
    for (const q of paper.ripples) { const k = (S.t - q.t) / 1500; q.rad = 420 * (1 - Math.pow(1 - Math.min(k, 1), 2.4)); q.life = 1 - k; }
    paper.ripples = paper.ripples.filter(q => q.life > 0);
    paper.splashes = paper.splashes.filter(q => S.t - q.t < 3000);
  }

  const S = {
    w: 0, h: 0, dpr: 1, scroll: 0, pageH: 0, t: 0, raf: 0, awakeUntil: 0,
    items: [], extra: [], trail: [], rects: [], hue: 0, introDone: false, stopped: false,
    p: { x: -1e4, y: -1e4, vx: 0, vy: 0, on: false, moved: 0 },
    amb: 0, lastAct: 0, drawn: 0,
  };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  // Stable random per grid cell: a layout change elsewhere does not move a doodle.
  const cellRandom = (col, row) => {
    let seed = (col * 73856093) ^ (row * 19349663) ^ 0x5bd1e995;
    return () => { seed = Math.imul(seed ^ (seed >>> 15), 0x2c1b3c6d); seed ^= seed + Math.imul(seed ^ (seed >>> 7), 0x297a2d39); return ((seed ^ (seed >>> 14)) >>> 0) / 4294967296; };
  };

  function measure() {
    S.w = document.documentElement.clientWidth;
    S.h = window.innerHeight;
    S.scroll = window.scrollY;
    S.pageH = Math.max(document.documentElement.scrollHeight, S.h);
    // Keep the backing store under ~4.5 MP on large/high-DPI screens (2K, 4K).
    S.dpr = Math.min(window.devicePixelRatio || 1, 2, Math.sqrt(4.5e6 / Math.max(1, S.w * S.h)));
    const cw = Math.round(S.w * S.dpr), ch = Math.round(S.h * S.dpr);
    if (canvas.width !== cw || canvas.height !== ch) { canvas.width = cw; canvas.height = ch; }
    ctx.setTransform(S.dpr, 0, 0, S.dpr, 0, 0);
    const style = canvas.dataset.dots || 'soft';
    if (!paper.pattern || paper.k !== S.dpr || paper.style !== style) { genDots(style); buildPattern(); paper.k = S.dpr; paper.style = style; }
    makeSpots();

    const pad = S.w < 700 ? 8 : 16;
    S.rects = [];
    for (const el of document.querySelectorAll(PROTECTED)) {
      if (el.closest('[data-doodles]')) continue;
      const r = el.getBoundingClientRect();
      if (r.width < 2 || r.height < 2) continue;
      S.rects.push({ l: r.left - pad, t: r.top + S.scroll - pad, r: r.right + pad, b: r.bottom + S.scroll + pad });
    }
    place();
  }

  function blocked(x, y, rad) {
    for (const r of S.rects) {
      if (x + rad > r.l && x - rad < r.r && y + rad > r.t && y - rad < r.b) return true;
    }
    return false;
  }

  // Personal space: no doodle sits on a neighbour placed in this or the last row.
  function crowded(x, y, size, back) {
    for (let i = S.items.length - 1, n = 0; i >= 0 && n < back; i--, n++) {
      const o = S.items[i];
      if (Math.hypot(o.x - x, o.y - y) < (o.s + size) * 1.45) return true;
    }
    return false;
  }

  function place() {
    const mobile = S.w < 700;
    const cell = mobile ? 150 : clamp(Math.round(Math.sqrt(S.w * S.h / 16)), 190, 320);
    const cols = Math.max(2, Math.round(S.w / cell)), cw = S.w / cols;
    const rows = Math.ceil(S.pageH / cell);
    const old = new Map(S.items.map(d => [d.key, d]));
    S.items = [];
    for (let row = 0; row < rows; row++) {
      for (let col = 0; col < cols; col++) {
        const rnd = cellRandom(col, row);
        const size = (mobile ? 12 : 15) + rnd() * (mobile ? 6 : 11);
        let spot = null;
        for (let k = 0; k < 6 && !spot; k++) {
          const x = (col + .15 + rnd() * .7) * cw, y = (row + .15 + rnd() * .7) * cell;
          if (!blocked(x, y, size * 1.2) && !crowded(x, y, size, cols + 2)) spot = [x, y];
        }
        if (!spot) continue;
        const key = col + ':' + row, prev = old.get(key);
        S.items.push({
          key, x: spot[0], y: spot[1], s: size, rot: (rnd() - .5) * .7, ph: rnd() * 6.28,
          kind: NAMES[Math.floor(rnd() * NAMES.length)], c: palette(Math.floor(rnd() * 5)),
          sp: .00045 + rnd() * .0005, amp: 3 + rnd() * 4,
          wig: prev ? prev.wig : 0, ox: 0, oy: 0, vx: 0, vy: 0, pop: prev ? prev.pop : (S.introDone || reduced.matches ? 1 : 0),
          delay: prev ? 0 : clamp((spot[1] - S.scroll) / S.h, 0, 1) * 500 + rnd() * 250,
        });
      }
    }
    if (!S.introDone) { S.introStart = performance.now(); S.introDone = true; wake(1400); }
  }

  function step() {
    const p = S.p, px = p.x, py = p.y + S.scroll, top = S.scroll - 60, bottom = S.scroll + S.h + 60;
    const motion = !reduced.matches;
    for (const list of [S.items, S.extra]) {
      for (const d of list) {
        if (d.y < top || d.y > bottom) continue;
        if (d.pop < 1) {
          const since = S.t - (d.born || S.introStart || 0) - (d.delay || 0);
          d.pop = since > 0 ? Math.min(1, since / 420) : 0;
        }
        if (motion) {
          const near = p.on && S.t - p.moved < 1500 && Math.abs(d.x - px) < 120 && Math.abs(d.y - py) < 120 && Math.hypot(d.x - px, d.y - py) < 110;
          d.wig += ((near ? 1 : 0) - d.wig) * .1;
          if (d.wig < .005) d.wig = 0;
        }
      }
    }
    if (motion) push(top, bottom);
    if (motion) stepPaper();
    S.extra = S.extra.filter(d => S.t - d.born < 5000);
    if (motion && p.on && Math.hypot(p.vx, p.vy) > 1.5) {
      S.hue = (S.hue + 1) % 400;
      S.trail.push({ x: px, y: py, t: S.t, c: TRAIL[Math.floor(S.hue / 100)] });
      p.vx = p.vy = 0;
      if (S.trail.length > 120) S.trail.shift();
    }
    S.trail = S.trail.filter(q => S.t - q.t < 1400);
  }

  function freeSpot(x, y, size) {
    const others = [...S.items, ...S.extra];
    const free = (px, py) => !blocked(px, py, size * .9) &&
      others.every(o => Math.hypot(o.x + o.ox - px, o.y + o.oy - py) > (o.s + size) * 1.3);
    if (free(x, y)) return [x, y];
    for (let r = 24; r <= 200; r += 16) {
      const turn = Math.random() * 6.283;
      for (let k = 0; k < 12; k++) {
        const a = turn + k * .5236, px = x + Math.cos(a) * r, py = y + Math.sin(a) * r;
        if (px > size && px < S.w - size && free(px, py)) return [px, py];
      }
    }
    return [x, y];
  }

  // New doodles push their neighbours aside like bubbles; springs bring them back.
  function push(top, bottom) {
    const live = S.extra.filter(e => e.pop > 0 && S.t - e.born < 4300);
    const near = [];
    for (const list of [S.items, S.extra]) for (const d of list) if (d.y > top && d.y < bottom) near.push(d);
    // The moving cursor sends a wave: doodles in its way are swept aside and
    // along its direction, harder the faster it moves.
    const p = S.p, waving = p.on && S.t - p.moved < 80;
    const px = p.x, py = p.y + S.scroll;
    const speed = waving ? Math.min(Math.hypot(p.dx || 0, p.dy || 0), 60) : 0;
    const R = 150;
    for (const d of near) {
      let fx = 0, fy = 0;
      if (speed > 1) {
        const dx = d.x + d.ox - px, dy = d.y + d.oy - py, dist = Math.hypot(dx, dy) || .01;
        if (dist < R) {
          const f = (1 - dist / R) ** 2 * (.5 + speed * .09);
          fx += dx / dist * f + (p.dx / speed) * f * .6;
          fy += dy / dist * f + (p.dy / speed) * f * .6;
          d.spin = (d.spin || 0) + (dx * p.dy - dy * p.dx > 0 ? 1 : -1) * f * .006;
        }
      }
      for (const e of live) {
        if (e === d) continue;
        const dx = d.x + d.ox - (e.x + e.ox), dy = d.y + d.oy - (e.y + e.oy);
        const dist = Math.hypot(dx, dy) || .01, min = (d.s + e.s) * 1.5 * Math.min(1, e.pop * 1.4);
        if (dist < min) { const f = (min - dist) / min * 3.2; fx += dx / dist * f; fy += dy / dist * f; }
      }
      d.vx = (d.vx + fx - d.ox * .05) * .84;
      d.vy = (d.vy + fy - d.oy * .05) * .84;
      if (d.spin) { d.spin *= .9; d.tilt = clamp(((d.tilt || 0) + d.spin) * .94, -.45, .45); if (Math.abs(d.tilt) + Math.abs(d.spin) < .001) d.spin = d.tilt = 0; }
      d.ox += d.vx; d.oy += d.vy;
      const m = Math.hypot(d.ox, d.oy), cap = d.s * (d.born ? 5 : 3.2);
      if (m > cap) { d.ox *= cap / m; d.oy *= cap / m; }
      if (Math.abs(d.ox) + Math.abs(d.oy) < .05 && Math.abs(d.vx) + Math.abs(d.vy) < .05) { d.ox = d.oy = d.vx = d.vy = 0; }
    }
  }

  function busy() {
    if (S.trail.length || S.extra.length || paper.ripples.length || paper.splashes.length || paper.curK > 0) return true;
    const top = S.scroll - 60, bottom = S.scroll + S.h + 60;
    for (const d of S.items) if (d.y > top && d.y < bottom && (d.wig > 0 || d.pop < 1 || d.ox || d.oy || d.tilt)) return true;
    return false;
  }

  function draw() {
    ctx.clearRect(0, 0, S.w, S.h);
    ctx.save();
    ctx.translate(0, -S.scroll);
    drawPaper();
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    for (let i = 1; i < S.trail.length; i++) {
      const a = S.trail[i - 1], b = S.trail[i];
      if (b.t - a.t > 90 || Math.abs(b.x - a.x) + Math.abs(b.y - a.y) > 120) continue;
      const life = 1 - (S.t - b.t) / 1400;
      ctx.globalAlpha = life * .5; ctx.strokeStyle = b.c; ctx.lineWidth = 5 * life + 1;
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
    }
    const top = S.scroll - 60, bottom = S.scroll + S.h + 60;
    for (const list of [S.items, S.extra]) {
      for (const d of list) {
        if (d.y < top || d.y > bottom || d.pop <= 0) continue;
        const k = d.pop, grow = k < 1 ? Math.max(0, 1 + Math.sin(k * Math.PI) * .35 - (1 - k)) : 1;
        const fade = d.born ? clamp((5000 - (S.t - d.born)) / 800, 0, 1) : 1;
        ctx.save();
        // Ambient life: each doodle floats on its own slow, looping path.
        const a = S.amb * (d.amp || 3), w = S.t * (d.sp || .0006) + d.ph;
        ctx.translate(d.x + d.ox + Math.sin(w * 1.3) * a * .7, d.y + d.oy + Math.sin(w) * a);
        ctx.rotate(d.rot + (d.tilt || 0) + Math.sin(w * .8) * .09 * S.amb + Math.sin(S.t * .012 + d.ph) * .22 * d.wig);
        const sc = (1 + d.wig * .25 + Math.sin(w * 1.7) * .035 * S.amb) * grow;
        ctx.scale(sc, sc);
        drawDoodle(ctx, d.kind, d.s, d.c, (.3 + d.wig * .55) * fade);
        ctx.restore();
      }
    }
    ctx.restore();
    ctx.globalAlpha = 1;
  }

  // Floating runs at ~30 fps while the visitor is active and eases to a stop
  // 25 s after the last mouse/touch/scroll; interaction itself runs at full rate.
  const AMBIENT_IDLE = 25000;
  function frame(now) {
    S.raf = 0;
    if (S.stopped || document.hidden) return;
    const still = reduced.matches;
    const target = !still && now - S.lastAct < AMBIENT_IDLE ? 1 : 0;
    S.amb += (target - S.amb) * (target ? .03 : .015);
    if (S.amb < .002 && !target) S.amb = 0;
    const lively = !still && (now < S.awakeUntil || busy());
    const ambient = S.amb > 0;
    if (!lively && ambient && now - S.drawn < 32) { S.raf = requestAnimationFrame(frame); return; }
    S.t = now; S.drawn = now;
    step();
    draw();
    if (lively || ambient) S.raf = requestAnimationFrame(frame);
  }
  function activity() { S.lastAct = performance.now(); }
  function wake(ms) {
    if (S.stopped) return;
    S.awakeUntil = Math.max(S.awakeUntil, performance.now() + ms);
    if (!S.raf && !document.hidden) S.raf = requestAnimationFrame(frame);
  }

  let relayout = 0;
  function scheduleLayout(delay) {
    clearTimeout(relayout);
    relayout = setTimeout(() => { if (!S.stopped) { measure(); wake(60); } }, delay);
  }

  function start() {
    measure();
    const opts = { passive: true };
    activity();
    addEventListener('scroll', () => { S.scroll = window.scrollY; activity(); wake(60); }, opts);
    addEventListener('resize', () => scheduleLayout(200), opts);
    if (typeof ResizeObserver === 'function') new ResizeObserver(() => scheduleLayout(400)).observe(document.body);
    if (document.fonts && document.fonts.ready) document.fonts.ready.then(() => scheduleLayout(100));
    addEventListener('load', () => scheduleLayout(300));
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) { cancelAnimationFrame(S.raf); S.raf = 0; } else wake(60);
    });
    addEventListener('pagehide', () => { cancelAnimationFrame(S.raf); S.raf = 0; });
    addEventListener('pageshow', () => wake(60));

    addEventListener('pointermove', e => {
      if (reduced.matches) return;
      const p = S.p;
      if (p.on) { p.vx = e.clientX - p.x; p.vy = e.clientY - p.y; p.dx = p.vx; p.dy = p.vy; }
      p.x = e.clientX; p.y = e.clientY; p.on = true; p.moved = performance.now();
      activity(); wake(300);
    }, opts);
    document.documentElement.addEventListener('pointerleave', () => { S.p.on = false; wake(300); });
    addEventListener('blur', () => { S.p.on = false; });
    addEventListener('pointerup', e => { if (e.pointerType !== 'mouse') setTimeout(() => { S.p.on = false; wake(300); }, 700); }, opts);
    addEventListener('pointerdown', e => {
      activity();
      if (reduced.matches || e.button > 0) return;
      const t = e.target;
      if (t && t.closest && t.closest(INTERACTIVE)) return;
      const x = e.clientX, y = e.clientY + S.scroll;
      if (blocked(x, y, 18)) return;
      S.p.x = e.clientX; S.p.y = e.clientY; S.p.on = true; S.p.moved = performance.now();
      paper.ripples.push({ x, y, t: performance.now(), rad: 0, life: 1 });
      paper.splashes.push({ x, y, t: performance.now(), r: 70 + Math.random() * 50, n: 500 + Math.floor(Math.random() * 40), c: TINTS[Math.floor(Math.random() * TINTS.length)] });
      if (paper.ripples.length > 4) paper.ripples.shift();
      if (paper.splashes.length > 6) paper.splashes.shift();
      // The new doodle flies out of the click point to the nearest free spot.
      const spot = freeSpot(x, y, 22);
      S.extra.push({
        x: spot[0], y: spot[1], s: 22, rot: (Math.random() - .5) * .6, ph: 0, wig: 1, pop: 0, ox: x - spot[0], oy: y - spot[1], vx: 0, vy: 0, born: performance.now(),
        kind: NAMES[Math.floor(Math.random() * NAMES.length)], c: palette(Math.floor(Math.random() * 5)),
      });
      if (S.extra.length > (S.w < 700 ? 5 : 12)) S.extra.shift();
      wake(5200);
    }, opts);
    reduced.addEventListener && reduced.addEventListener('change', () => { S.trail = []; S.extra = []; paper.ripples = []; paper.splashes = []; paper.curK = 0; for (const d of S.items) { d.wig = 0; d.pop = 1; } wake(60); });
  }

  // The background never competes with the page's own first paint.
  const go = () => { try { start(); } catch (_) { S.stopped = true; } };
  if ('requestIdleCallback' in window) requestIdleCallback(go, { timeout: 1500 });
  else setTimeout(go, 300);
})();
