(() => {
  const root = document.querySelector("[data-bg-floaters]");
  if (!root) return;

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  if (reduceMotion.matches) return;

  const pointer = {
    x: window.innerWidth / 2,
    y: window.innerHeight / 2,
    active: false,
  };

  const shapes = [];
  let rafId = 0;

  function createShape(config) {
    const el = document.createElement("span");
    el.className = `bg-floater ${config.tone} ${config.shape}`;
    el.style.width = `${config.width}px`;
    el.style.height = `${config.height}px`;

    if (config.shape === "shape-pill") {
      el.style.width = `${config.width * 1.45}px`;
      el.style.height = `${config.height * 0.62}px`;
    }

    if (config.shape === "shape-diamond") {
      el.style.transform = "rotate(45deg)";
    }

    root.appendChild(el);

    return {
      el,
      ox: config.x,
      oy: config.y,
      x: config.x,
      y: config.y,
      vx: 0,
      vy: 0,
      width: config.width,
      height: config.height,
      angle: config.angle,
      driftX: config.driftX,
      driftY: config.driftY,
      speed: config.speed,
      phase: config.phase,
      shape: config.shape,
    };
  }

  function buildScene() {
    root.textContent = "";
    shapes.length = 0;

    const width = window.innerWidth;
    const height = window.innerHeight;
    const count = width < 700 ? 14 : width < 1100 ? 18 : 24;
    const palette = ["tone-soft", "tone-jungle", "tone-bright"];
    const kinds = ["shape-circle", "shape-rounded", "shape-pill", "shape-diamond", "shape-ring"];

    for (let i = 0; i < count; i += 1) {
      const size = width < 700 ? 38 + Math.random() * 52 : 44 + Math.random() * 84;
      const x = Math.random() * width;
      const y = Math.random() * height;
      const shape = kinds[i % kinds.length];
      const tone = palette[i % palette.length];
      const angle = Math.random() * 32 - 16;

      shapes.push(
        createShape({
          x,
          y,
          width: size,
          height: size,
          shape,
          tone,
          angle,
          driftX: 10 + Math.random() * 22,
          driftY: 12 + Math.random() * 26,
          speed: 0.18 + Math.random() * 0.28,
          phase: Math.random() * Math.PI * 2,
        }),
      );
    }
  }

  function tick(now) {
    const t = now * 0.001;
    const radius = window.innerWidth < 700 ? 150 : 190;
    const spring = 0.035;
    const damping = 0.9;

    shapes.forEach((shape, index) => {
      const idleX = shape.ox + Math.sin(t * shape.speed + shape.phase) * shape.driftX;
      const idleY = shape.oy + Math.cos(t * shape.speed * 0.92 + shape.phase) * shape.driftY;

      let targetX = idleX;
      let targetY = idleY;
      let angle = shape.angle + Math.sin(t * shape.speed + index) * 4;

      if (pointer.active) {
        const dx = idleX - pointer.x;
        const dy = idleY - pointer.y;
        const distance = Math.hypot(dx, dy);

        if (distance && distance < radius) {
          const force = 1 - distance / radius;
          const push = force * force * 32;
          targetX += (dx / distance) * push;
          targetY += (dy / distance) * push;
          angle += (dx / distance) * force * 10;
        }
      }

      shape.vx += (targetX - shape.x) * spring;
      shape.vy += (targetY - shape.y) * spring;
      shape.vx *= damping;
      shape.vy *= damping;
      shape.x += shape.vx;
      shape.y += shape.vy;

      const rotate = shape.shape === "shape-diamond" ? angle + 45 : angle;
      shape.el.style.transform = `translate3d(${shape.x.toFixed(2)}px, ${shape.y.toFixed(2)}px, 0) rotate(${rotate.toFixed(2)}deg)`;
    });

    rafId = window.requestAnimationFrame(tick);
  }

  function start() {
    buildScene();
    cancelAnimationFrame(rafId);
    rafId = window.requestAnimationFrame(tick);
  }

  window.addEventListener(
    "pointermove",
    (event) => {
      if (event.pointerType === "touch") return;
      pointer.x = event.clientX;
      pointer.y = event.clientY;
      pointer.active = true;
    },
    { passive: true },
  );

  document.addEventListener(
    "mouseleave",
    () => {
      pointer.active = false;
    },
    { passive: true },
  );

  window.addEventListener(
    "blur",
    () => {
      pointer.active = false;
    },
    { passive: true },
  );

  window.addEventListener(
    "resize",
    () => {
      start();
    },
    { passive: true },
  );

  start();
})();
