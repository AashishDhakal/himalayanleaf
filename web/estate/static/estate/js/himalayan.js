/* Himalayan Leaf — motion layer.
 *
 * Alpine owns only state that CSS cannot derive on its own: pointer position,
 * scroll offset, the Ascent's progress, and which lot the cursor is over.
 * Everything visual reads those as custom properties, so the browser
 * interpolates rather than React re-rendering on every pointer move.
 */

const REDUCED = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const root = document.documentElement;

/* Writes are batched into one rAF so a fast pointer can't thrash style recalc. */
function makeWriter() {
  let pending = null;
  let frame = null;
  return (props) => {
    pending = Object.assign(pending || {}, props);
    if (frame) return;
    frame = requestAnimationFrame(() => {
      frame = null;
      const batch = pending;
      pending = null;
      for (const [key, value] of Object.entries(batch)) root.style.setProperty(key, value);
    });
  };
}

document.addEventListener("alpine:init", () => {
  const write = makeWriter();

  /* ── ambient: cursor drop, ripples, scroll, the brew-in intro ─────────── */
  Alpine.data("hlAmbience", () => ({
    ripples: [],
    introVisible: !REDUCED,
    introPct: 0,
    pouring: false,
    liquor: "#c98f2e",

    init() {
      if (this.introVisible) this.runIntro();

      if (!REDUCED) {
        this.$root.addEventListener("pointerdown", (e) => this.ripple(e), { passive: true });
        window.addEventListener(
          "mousemove",
          (e) => {
            const mx = e.clientX / window.innerWidth;
            const my = e.clientY / window.innerHeight;
            write({ "--mx": mx.toFixed(4), "--my": my.toFixed(4), "--lean": ((mx - 0.5) * 2).toFixed(4) });
          },
          { passive: true }
        );
      }

      const onScroll = () => {
        const y = window.scrollY;
        // The ghosted ILAM and the estate frame drift on a wrapped offset so
        // their translation never grows without bound down a long page.
        write({ "--scroll": y.toFixed(1), "--scroll-wrapped": (y % 3000).toFixed(1) });
      };
      window.addEventListener("scroll", onScroll, { passive: true });
      onScroll();
    },

    runIntro() {
      const started = Date.now();
      const tick = setInterval(() => {
        const elapsed = Date.now() - started;
        if (elapsed > 3700) {
          clearInterval(tick);
          this.introVisible = false;
          this.introPct = 100;
        } else {
          this.introPct = Math.min(100, Math.round((elapsed / 2500) * 100));
        }
      }, 90);
    },

    /* Opening or switching a lot pours a sheet of that liquor down the screen. */
    pour(liquor) {
      if (REDUCED) return;
      this.liquor = liquor || this.liquor;
      this.pouring = true;
      setTimeout(() => {
        this.pouring = false;
      }, 1500);
    },

    ripple(event) {
      const id = Date.now() + Math.random();
      this.ripples.push({ id, x: event.clientX, y: event.clientY });
      setTimeout(() => {
        this.ripples = this.ripples.filter((r) => r.id !== id);
      }, 1100);
    },
  }));

  /* ── the collection steeps into the hovered lot's liquor ──────────────── */
  Alpine.data("hlCollection", () => ({
    steep(colour, index) {
      this.$root.style.setProperty("--steep-colour", colour);
      this.$root.style.setProperty("--steep-x", `${index * 25 + 12}%`);
      this.$root.style.setProperty("--steep-opacity", "0.9");
    },
    clear() {
      this.$root.style.setProperty("--steep-colour", "rgba(27,58,44,0.5)");
      this.$root.style.setProperty("--steep-x", "50%");
      this.$root.style.setProperty("--steep-opacity", "0.7");
    },
  }));

  /* ── the ascent: 240 m → 2,100 m as the section scrolls past ──────────── */
  Alpine.data("hlAscent", (linesElementId, baseM, riseM) => ({
    p: 0,
    lines: JSON.parse(document.getElementById(linesElementId).textContent),
    baseM,
    riseM,

    init() {
      this.photos = Array.from(this.$root.querySelectorAll("[data-ascent-photo]"));
      const measure = () => this.measure();
      window.addEventListener("scroll", measure, { passive: true });
      window.addEventListener("resize", measure, { passive: true });
      measure();
    },

    measure() {
      const span = this.$root.offsetHeight - window.innerHeight;
      const raw = (window.scrollY - this.$root.offsetTop) / (span || 1);
      this.p = Math.min(1, Math.max(0, raw));
      this.$root.style.setProperty("--p", this.p.toFixed(4));
      this.paintPhotos();
    },

    /* Each photograph fades up as its altitude comes round and fades out
       behind the next — the ends hold rather than fading to nothing. */
    paintPhotos() {
      const SPAN = 0.36;
      const last = this.photos.length - 1;
      this.photos.forEach((el, i) => {
        const at = parseFloat(el.dataset.at);
        const d = Math.abs(this.p - at);
        const on = i === 0 ? this.p < at + SPAN : i === last ? this.p >= at - SPAN * 0.5 : d < SPAN;
        el.style.opacity = on ? Math.max(0.3, 0.86 - d * 1.1).toFixed(3) : "0";
        el.style.transform =
          `scale(${(1.06 + this.p * 0.14).toFixed(3)}) ` +
          `translate3d(calc(var(--lean) * 12px), ${((this.p - at) * -60).toFixed(1)}px, 0)`;
      });
    },

    get altitude() {
      return Math.round(this.baseM + this.p * this.riseM).toLocaleString("en");
    },

    get line() {
      const passed = this.lines.filter((l) => this.p >= l.at);
      return (passed.length ? passed[passed.length - 1] : this.lines[0]).text;
    },

    passed(at) {
      return this.p >= at;
    },
  }));

  /* ── quote ceremony ───────────────────────────────────────────────────── */

  /* The fill and glow live on the shell, which HTMX never swaps, so their CSS
     transitions run continuously across steps. The server reports the new
     progress on each step response; this picks it up. */
  Alpine.data("hlCeremony", (progress, liquor) => ({
    init() {
      this.apply(progress, liquor, false);
    },
    apply(p, colour, done) {
      this.$root.style.setProperty("--progress", p);
      this.$root.style.setProperty("--liquor", colour);
      this.$root.style.setProperty("--glow", done ? "40%" : "23%");
    },
    onBrew(event) {
      const d = event.detail || {};
      this.apply(d.progress ?? 0, d.liquor || "#c98f2e", !!d.done);
    },
  }));

  /* Within a step, Alpine decides when Continue lights up; the server decides
     what happens when it is pressed. */
  Alpine.data("hlStep", (config) => ({
    filled: false,

    init() {
      this.sync();
    },

    /* The form is the source of truth — this only reads it back. */
    sync() {
      const data = new FormData(this.$root);
      if (config.kind === "choice") {
        this.filled = data.getAll(config.name).some((v) => v !== "");
      } else if (config.kind === "text") {
        this.filled = config.keys.every((key) => (data.get(key) || "").trim().length > 0);
      } else {
        this.filled = true;
      }
    },

    /* A single pick registers, holds for a beat, then carries you forward.
       Submitting with no submitter means no `action` field, which the view
       reads as "next". */
    choose() {
      setTimeout(() => this.$root.requestSubmit(), REDUCED ? 0 : 380);
    },
  }));
});

/* ── overlay plumbing ───────────────────────────────────────────────────── */

/* The page behind an open sheet or ceremony must not scroll. */
function syncScrollLock() {
  const open = ["hl-sheet", "hl-quote"].some((id) => {
    const el = document.getElementById(id);
    return el && el.children.length > 0;
  });
  document.body.classList.toggle("hl-locked", open);
}

document.body.addEventListener("htmx:afterSwap", (event) => {
  syncScrollLock();
  if (event.target.id === "hl-sheet" && event.target.children.length) {
    window.scrollTo({ top: 0 });
  }
});

document.addEventListener("DOMContentLoaded", syncScrollLock);

/* Escape closes whichever overlay is on top. */
document.addEventListener("keydown", (event) => {
  if (event.key !== "Escape") return;
  const quote = document.getElementById("hl-quote");
  const sheet = document.getElementById("hl-sheet");
  const target = quote && quote.children.length ? quote : sheet && sheet.children.length ? sheet : null;
  if (!target) return;
  const closer = target.querySelector("[data-close]");
  if (closer) closer.click();
});
