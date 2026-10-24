"""Retro effects: synthwave grid, PLAY boot screen, typewriter tagline,
tab-switch static, VHS rewind loader and the glitch reveal on top results.

All pure CSS/HTML (Streamlit doesn't run custom JavaScript), so they're
lightweight and safe on Streamlit Cloud. Every animation is switched off for
people who ask their device to reduce motion.
"""
import streamlit as st

REWIND_SECONDS = 1.4  # how long the rewind loader shows for a new search

FX_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&display=swap');

/* ---------- Synthwave grid floor behind the whole app ---------- */
[data-testid="stAppViewContainer"], [data-testid="stMain"], [data-testid="stHeader"], .main {
    background: transparent !important;
}
[data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
.stApp::before {               /* the scrolling grid */
    content: "";
    position: fixed;
    left: -50%; right: -50%; bottom: -10vh;
    height: 100vh;
    z-index: 0;
    pointer-events: none;
    background-image:
        linear-gradient(rgba(247, 37, 133, 0.85) 2px, transparent 2px),
        linear-gradient(90deg, rgba(160, 80, 230, 0.8) 2px, transparent 2px);
    background-size: 64px 64px;
    transform: perspective(600px) rotateX(52deg);
    transform-origin: center bottom;
    -webkit-mask-image: linear-gradient(to top, #000 0%, rgba(0,0,0,0.75) 50%, transparent 95%);
            mask-image: linear-gradient(to top, #000 0%, rgba(0,0,0,0.75) 50%, transparent 95%);
    opacity: 0.6;
    animation: lm-grid-scroll 1.8s linear infinite;
}
.stApp::after {                /* soft glow on the horizon */
    content: "";
    position: fixed;
    left: 0; right: 0; bottom: 0;
    height: 42vh;
    z-index: 0;
    pointer-events: none;
    background: radial-gradient(ellipse 60% 45% at 50% 100%, rgba(247, 37, 133, 0.22), transparent 70%);
}
@keyframes lm-grid-scroll { from { background-position: 0 0, 0 0; } to { background-position: 0 64px, 0 0; } }

/* ---------- Typewriter tagline (VCR on-screen font) ---------- */
.lm-tagline {
    font-family: 'VT323', monospace !important;
    font-size: clamp(1rem, 4.2vw, 1.7rem) !important;
    max-width: 100%;
    color: #4CC9F0 !important;
    white-space: nowrap;
    overflow: hidden;
    width: 0;
    border-right: 0.12em solid #4CC9F0;
    animation:
        lm-type 1.6s steps(35, end) 1.5s forwards,
        lm-caret 0.8s step-end infinite;
}
@keyframes lm-type { from { width: 0; } to { width: 35ch; } }
@keyframes lm-caret { 50% { border-color: transparent; } }

/* ---------- PLAY boot screen (first visit only) ---------- */
.lm-boot {
    position: fixed; inset: 0;
    z-index: 999999;
    background: #1B1FA8;
    pointer-events: none;
    animation: lm-boot-out 0.45s ease-in 1.15s forwards;
}
.lm-boot-osd, .lm-boot-sp {
    position: absolute;
    font-family: 'VT323', monospace;
    color: #F3E9D2;
    font-size: clamp(2.5rem, 7vw, 4.5rem);
    text-shadow: 3px 3px 0 #0B0D55;
}
.lm-boot-osd { top: 8vh; left: 7vw; animation: lm-blink 0.5s step-end 3; }
.lm-boot-sp  { top: 8vh; right: 7vw; }
@keyframes lm-boot-out { to { opacity: 0; visibility: hidden; } }
@keyframes lm-blink { 50% { opacity: 0; } }

/* ---------- TV static when switching tabs ---------- */
[data-baseweb="tab-panel"], [role="tabpanel"] { position: relative; }
[data-baseweb="tab-panel"]::before, [role="tabpanel"]::before {
    content: "";
    position: absolute; inset: -0.5rem;
    z-index: 5;
    pointer-events: none;
    background-image:
        repeating-linear-gradient(0deg, rgba(0,0,0,0.35) 0 2px, transparent 2px 4px),
        url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
    background-color: #2A1F4A;
    animation: lm-static 0.45s steps(5) forwards;
}
@keyframes lm-static {
    0%   { opacity: 0.95; background-position: 0 0, 0 0; }
    40%  { opacity: 0.8;  background-position: 0 0, 40px -60px; }
    80%  { opacity: 0.35; background-position: 0 0, -70px 30px; }
    100% { opacity: 0;    background-position: 0 0, 20px 90px; visibility: hidden; }
}

/* ---------- VHS rewind loader ---------- */
@property --lm-m { syntax: '<integer>'; initial-value: 0; inherits: false; }
@property --lm-s { syntax: '<integer>'; initial-value: 0; inherits: false; }
.lm-rewind {
    display: flex; align-items: center; gap: 1.5rem; flex-wrap: wrap;
    margin: 1rem 0 1.5rem;
    padding: 1.25rem 1.5rem;
    background: #2A1F4A;
    border: 2px solid #3D2E66;
    border-radius: 6px;
}
.lm-rw-cassette {
    width: 170px; padding: 10px;
    background: #1A1230; border: 2px solid #3D2E66; border-radius: 8px;
}
.lm-rw-label {
    background: #F3E9D2; color: #1A1230; border-radius: 3px;
    font-family: 'Bungee', sans-serif; font-size: 0.8rem; padding: 2px 6px; margin-bottom: 8px;
    background-image: linear-gradient(#FF6B35, #FF6B35), linear-gradient(#F72585, #F72585);
    background-size: 80% 3px, 70% 3px; background-repeat: no-repeat;
    background-position: 6px 78%, 6px 92%;
    padding-bottom: 12px;
}
.lm-rw-window {
    display: flex; align-items: center; justify-content: space-between;
    background: #120C22; border-radius: 6px; padding: 8px 14px;
}
.lm-rw-reel {
    width: 34px; height: 34px; border-radius: 50%;
    border: 5px dashed #4CC9F0;
    animation: lm-spin 0.5s linear infinite reverse;
}
.lm-rw-tape { flex: 1; height: 10px; margin: 0 6px; background: #3D2E66; border-radius: 4px; }
.lm-rw-osd { flex: 1 1 240px; font-family: 'VT323', monospace; color: #F3E9D2; font-size: 2rem; line-height: 1.1; }
.lm-rw-arrows { color: #F72585; animation: lm-blink 0.4s step-end infinite; }
.lm-rw-counter::after {
    counter-reset: m var(--lm-m) s var(--lm-s);
    content: "0:" counter(m, decimal-leading-zero) ":" counter(s, decimal-leading-zero);
    animation: lm-count-m 1.4s ease-in forwards, lm-count-s 0.3s linear infinite;
    color: #4CC9F0;
}
.lm-rw-sub { display: block; font-size: 1.2rem; color: #B9A9D9; }
@keyframes lm-count-m { from { --lm-m: 47; } to { --lm-m: 0; } }
@keyframes lm-count-s { from { --lm-s: 59; } to { --lm-s: 0; } }
@keyframes lm-spin { to { transform: rotate(360deg); } }

/* ---------- Glitch reveal on the top result and the "Surprise me" pick ---------- */
[class*="st-key-card-0-"], [class*="st-key-spotlight"] {
    position: relative;
    animation: lm-glitch 0.75s steps(1, end) 1;
}
[class*="st-key-card-0-"]::after, [class*="st-key-spotlight"]::after {
    content: "";
    position: absolute; inset: 0;
    border-radius: 6px;
    pointer-events: none;
    background: repeating-linear-gradient(0deg, rgba(243, 233, 210, 0.12) 0 2px, transparent 2px 4px);
    animation: lm-scan-out 1s ease-out forwards;
}
@keyframes lm-glitch {
    0%   { opacity: 0; transform: translateX(-14px) skewX(10deg); clip-path: inset(10% 0 60% 0); filter: hue-rotate(90deg) saturate(3); }
    12%  { opacity: 1; transform: translateX(12px); clip-path: inset(55% 0 15% 0); }
    25%  { transform: translateX(-8px) skewX(-5deg); clip-path: inset(0 0 70% 0); filter: hue-rotate(-70deg) saturate(2); }
    40%  { transform: translateX(5px); clip-path: inset(70% 0 0 0); filter: none; }
    55%  { transform: translateX(-3px); clip-path: inset(0); filter: contrast(1.6) brightness(1.2); }
    70%  { transform: translateX(2px); filter: none; }
    100% { transform: none; clip-path: inset(0); filter: none; opacity: 1; }
}
@keyframes lm-scan-out { from { opacity: 1; } to { opacity: 0; } }

/* ---------- Respect "reduce motion" ---------- */
@media (prefers-reduced-motion: reduce) {
    .stApp::before, .lm-tagline, .lm-boot, .lm-boot-osd, .lm-rw-reel, .lm-rw-arrows, .lm-rw-counter::after,
    [class*="st-key-card-0-"], [class*="st-key-spotlight"],
    [class*="st-key-card-0-"]::after, [class*="st-key-spotlight"]::after,
    [data-baseweb="tab-panel"]::before, [role="tabpanel"]::before {
        animation: none !important;
    }
    .lm-tagline { width: auto; border-right: none; }
    .lm-boot, [data-baseweb="tab-panel"]::before, [role="tabpanel"]::before,
    [class*="st-key-card-0-"]::after, [class*="st-key-spotlight"]::after { display: none; }
}
</style>
"""

BOOT_HTML = """
<div class="lm-boot" aria-hidden="true">
  <div class="lm-boot-osd">PLAY &#9654;</div>
  <div class="lm-boot-sp">SP</div>
</div>
"""

REWIND_HTML = """
<div class="lm-rewind" role="status" aria-label="Searching">
  <div class="lm-rw-cassette" aria-hidden="true">
    <div class="lm-rw-label">LOST MEDIA</div>
    <div class="lm-rw-window"><span class="lm-rw-reel"></span><span class="lm-rw-tape"></span><span class="lm-rw-reel"></span></div>
  </div>
  <div class="lm-rw-osd">
    <span class="lm-rw-arrows">&#9664;&#9664;</span> REWIND <span class="lm-rw-counter"></span>
    <span class="lm-rw-sub">Searching 9,582 tapes for your memory...</span>
  </div>
</div>
"""


def inject():
    """Add the effects' styles. Call once, right after st.set_page_config."""
    st.markdown(FX_CSS, unsafe_allow_html=True)


def boot_screen():
    """Show the blue PLAY screen on someone's first visit only."""
    if not st.session_state.get("lm_booted"):
        st.session_state.lm_booted = True
        st.markdown(BOOT_HTML, unsafe_allow_html=True)


def show_rewind(placeholder):
    """Put the rewind loader into a st.empty() placeholder."""
    placeholder.markdown(REWIND_HTML, unsafe_allow_html=True)
