document.addEventListener("keydown", (event) => {
  const slides = [...document.querySelectorAll("[data-slide-link]")];
  if (!slides.length) return;

  const active = document.activeElement;
  const index = slides.findIndex((node) => node === active);
  const current = index >= 0 ? index : 0;

  if (event.key === "ArrowDown" || event.key === "PageDown") {
    event.preventDefault();
    const next = slides[Math.min(current + 1, slides.length - 1)];
    next.focus();
    next.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  if (event.key === "ArrowUp" || event.key === "PageUp") {
    event.preventDefault();
    const prev = slides[Math.max(current - 1, 0)];
    prev.focus();
    prev.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});
