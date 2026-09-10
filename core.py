import json
import random

import streamlit as st
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# DRAW STRUCTURE
# Edit COUNT here if the event details change.
# --------------------------------------------------------------------------
ROUNDS = [
    {"key": "s1r1", "session": 1, "round": 1, "count": 40},
    {"key": "s1r2", "session": 1, "round": 2, "count": 40},
    {"key": "s2r1", "session": 2, "round": 1, "count": 30},
    {"key": "s2r2", "session": 2, "round": 2, "count": 35},
]


def rounds_for_session(session_num: int):
    return [r for r in ROUNDS if r["session"] == session_num]


# --------------------------------------------------------------------------
# SESSION STATE
# --------------------------------------------------------------------------
def init_state():
    defaults = {
        "pool": [],
        "all_ids": [],
        "results": {},
        "pre_draw_pool": {},
        "loaded": False,
        "revealed": set(),
        "paste_text": "",
        "page": "home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def parse_ids(text: str) -> list[str]:
    """Only numeric worker IDs are accepted — anything non-numeric pasted
    in by mistake is silently dropped rather than loaded."""
    if not text or not text.strip():
        return []
    raw = text.replace(",", "\n").splitlines()
    return [x.strip() for x in raw if x.strip().isdigit()]


def load_participants(ids: list[str]):
    clean = [str(i).strip() for i in ids if str(i).strip()]
    st.session_state.all_ids = clean
    st.session_state.pool = clean.copy()
    st.session_state.results = {}
    st.session_state.pre_draw_pool = {}
    st.session_state.revealed = set()
    st.session_state.loaded = True


def draw_round(round_key: str, count: int):
    pool = st.session_state.pool
    # snapshot the pool BEFORE removing winners, so the wheel can show
    # every candidate that was still in play for this round
    st.session_state.pre_draw_pool[round_key] = pool.copy()
    n = min(count, len(pool))
    winners = random.sample(pool, n)
    st.session_state.pool = [i for i in pool if i not in winners]
    st.session_state.results[round_key] = winners


def reset_all():
    st.session_state.pool = []
    st.session_state.all_ids = []
    st.session_state.results = {}
    st.session_state.pre_draw_pool = {}
    st.session_state.revealed = set()
    st.session_state.loaded = False
    st.session_state.paste_text = ""
    st.session_state.page = "home"


def all_results_rows():
    """Flat list of dicts for the Result page / CSV export."""
    rows = []
    for r in ROUNDS:
        for wid in st.session_state.results.get(r["key"], []):
            rows.append(
                {
                    "Session": r["session"],
                    "Round": r["round"],
                    "Worker ID": wid,
                }
            )
    return rows


def go_to(page: str):
    st.session_state.page = page


# --------------------------------------------------------------------------
# THEME — deep navy background, brass-gold accents, formal serif + sans
# font pairing. An exclusive, gala-invitation feel for the page chrome; the
# jar draw itself keeps its own frosted-glass + gold look.
# NOTE: colors are set two ways on purpose — via .streamlit/config.toml
# (Streamlit's native theme engine, works on every version) AND via this
# CSS (for finer details). If the CSS below doesn't fully apply on your
# Streamlit version, the config.toml colors still guarantee the look.
# --------------------------------------------------------------------------
def inject_theme():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
            color: #f3ede0;
        }
        h1, h2, h3,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3 {
            font-family: 'Playfair Display', serif !important;
            color: #f3ede0 !important;
        }
        [data-testid="stMarkdownContainer"] p {
            color: #f3ede0 !important;
        }
        .stApp {
            background:
                radial-gradient(ellipse 900px 500px at 50% -8%, rgba(201,162,39,0.14), transparent 60%),
                #0b1224;
        }
        [data-testid="stSidebar"] {
            background: #131c33;
        }
        [data-testid="stHeader"] {
            background: transparent;
        }
        .stTextArea textarea, .stTextInput input {
            background-color: #131c33 !important;
            color: #f3ede0 !important;
            border: 1.5px solid #c9a227 !important;
            border-radius: 12px !important;
        }
        .stTextArea textarea:focus, .stTextInput input:focus {
            border: 1.5px solid #f0d878 !important;
            box-shadow: 0 0 0 2px rgba(201,162,39,0.3) !important;
        }
        .stTextArea textarea::placeholder {
            color: #7c8ba0 !important;
        }
        .stButton > button,
        [data-testid="stButton"] button,
        [data-testid^="stBaseButton"] {
            background: linear-gradient(135deg, #f0d878, #c9a227) !important;
            color: #241a05 !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 0.95rem;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.3rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.4) !important;
        }
        .stButton > button p,
        [data-testid^="stBaseButton"] p {
            color: #241a05 !important;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #f5e2a0, #d9b23a) !important;
        }
        .stButton > button:disabled {
            background: #24374d !important;
            color: #66768c !important;
            box-shadow: none !important;
        }
        .stButton > button:disabled p {
            color: #66768c !important;
        }
        /* Clear button — quiet outline, light red on hover (distinct from primary actions) */
        .st-key-clear_btn button {
            background: transparent !important;
            color: #c9a227 !important;
            border: 1.5px solid #c9a227 !important;
        }
        .st-key-clear_btn button p {
            color: #c9a227 !important;
        }
        .st-key-clear_btn button:hover {
            background: rgba(178,59,59,0.15) !important;
            color: #e08a8a !important;
            border: 1.5px solid #e08a8a !important;
        }
        .st-key-clear_btn button:hover p {
            color: #e08a8a !important;
        }
        /* Load Participant button — same gold style, soft glow on hover */
        .st-key-load_btn button:hover {
            box-shadow: 0 0 14px rgba(240,216,120,0.55) !important;
        }
        /* Reset button — distinct warm/warning tone since it's a destructive action */
        .st-key-reset_btn button {
            background: linear-gradient(135deg, #b5533c, #943f2c) !important;
            color: #f3ede0 !important;
        }
        .st-key-reset_btn button p {
            color: #f3ede0 !important;
        }
        .st-key-reset_btn button:hover {
            background: linear-gradient(135deg, #c5624a, #a34a35) !important;
        }
        /* download button — same gold style */
        .stDownloadButton > button,
        [data-testid="stDownloadButton"] button {
            background: linear-gradient(135deg, #f0d878, #c9a227) !important;
            color: #241a05 !important;
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            border: none !important;
            border-radius: 10px !important;
            padding: 0.55rem 1.3rem;
        }
        .stDownloadButton > button:hover,
        [data-testid="stDownloadButton"] button:hover {
            background: linear-gradient(135deg, #f5e2a0, #d9b23a) !important;
            color: #241a05 !important;
        }
        [data-testid="stMetricValue"] {
            color: #f0d878 !important;
            font-family: 'Playfair Display', serif !important;
        }
        [data-testid="stMetricLabel"] {
            color: #9fb0c4 !important;
        }
        hr {
            border-color: rgba(201,162,39,0.3) !important;
        }
        .entries-pill {
            display:inline-block;
            background: #131c33;
            color: #f0d878;
            font-weight: 600;
            padding: 4px 16px;
            border-radius: 999px;
            font-size: 0.9rem;
            border: 1px solid #c9a227;
        }
        .section-label {
            display:block;
            font-family: 'Playfair Display', serif;
            font-size: 2rem;
            font-weight: 700;
            color: #f3ede0;
            border-bottom: 3px solid #c9a227;
            padding-bottom: 0.3rem;
            margin-bottom: 1.2rem;
            width: fit-content;
        }
        .round-label {
            display:block;
            font-family: 'Playfair Display', serif;
            font-size: 1.1rem;
            font-weight: 700;
            color: #f3ede0;
            margin-bottom: 0.6rem;
            padding-left: 0.6rem;
            border-left: 3px solid #c9a227;
        }
        /* nav card containers on Home (native bordered container, not CSS-hack dependent) */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 14px !important;
            border-color: #c9a227 !important;
            border-width: 1.5px !important;
            background: linear-gradient(180deg, #131c33, #0f1830) !important;
        }

        /* -------- shimmering title: a slow gold sweep across the letters,
           for a subtle, premium "moving" feel rather than a bounce/wiggle -------- */
        .shimmer-title {
            font-size: 2.3rem;
            margin-bottom: 0;
            font-weight: 700;
            background: linear-gradient(100deg, #c9a227 0%, #f5e2a0 22%, #fff6da 32%, #f5e2a0 42%, #c9a227 60%, #8a6d1a 80%, #c9a227 100%);
            background-size: 250% auto;
            -webkit-background-clip: text;
            background-clip: text;
            -webkit-text-fill-color: transparent;
            color: transparent;
            animation: titleShimmer 5s linear infinite;
        }
        @keyframes titleShimmer {
            0% { background-position: 0% center; }
            100% { background-position: -250% center; }
        }
        .sparkle {
            display:inline-block;
            color: #f5e2a0;
            -webkit-text-fill-color: #f5e2a0;
            font-size: 1.15rem;
            vertical-align: middle;
            margin: 0 12px;
            text-shadow: 0 0 8px rgba(240,216,120,0.85);
            animation: sparkleTwinkle 1.8s ease-in-out infinite;
        }
        .sparkle-b { animation-delay: 0.7s; }
        @keyframes sparkleTwinkle {
            0%, 100% { opacity: 0.25; transform: scale(0.7) rotate(0deg); }
            50% { opacity: 1; transform: scale(1.2) rotate(20deg); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(title: str):
    st.markdown(
        f"""
        <div style="text-align:center; padding: 0.6rem 0 2rem 0;">
            <h1 class="shimmer-title">
                <span class="sparkle sparkle-a">&#10022;</span>{title}<span class="sparkle sparkle-b">&#10022;</span>
            </h1>
        </div>
        """,
        unsafe_allow_html=True,
    )


def section_label(text: str):
    st.markdown(f'<span class="section-label">{text}</span>', unsafe_allow_html=True)


def round_label(text: str):
    st.markdown(f'<span class="round-label">{text}</span>', unsafe_allow_html=True)


def back_button():
    """Fixed-height row: a real back button on session/result pages, or an
    invisible spacer of the same height on Home — so the title below always
    sits at the same vertical position on every page."""
    if st.button("← Back", key="back_btn"):
        go_to("home")
        st.rerun()


def top_spacer():
    """Invisible placeholder matching back_button's height, used on Home so
    the title aligns with the title on session/result pages."""
    st.markdown('<div style="height:2.9rem;"></div>', unsafe_allow_html=True)


def nav_card(label: str, target_page: str, key: str):
    """A bordered card (native Streamlit container) holding a full-width button.
    Uses st.container(border=True) rather than a CSS-class hack, so the card
    look shows up regardless of Streamlit version."""
    with st.container(border=True):
        if st.button(label, key=key, use_container_width=True):
            go_to(target_page)
            st.rerun()


def status_panel():
    st.markdown("**Status**")
    st.metric("Participants loaded", len(st.session_state.all_ids))
    st.metric("Remaining in pool", len(st.session_state.pool))


# --------------------------------------------------------------------------
# SPIN + REVEAL COMPONENT
# Wheel is built client-side as an SVG with one wedge per pool ID (like a
# real raffle wheel), spins, then reveals the winners as pretty cards.
# Plays once per round, then stays static on later reruns.
# --------------------------------------------------------------------------
_SPIN_TEMPLATE = """
<div id="stage">
  <div id="jarWrap" style="display:flex; flex-direction:column; align-items:center;">
    <div style="position:relative; width:220px; height:260px;">
      <div id="jarBase" style="position:absolute; top:0; left:0; width:220px; height:260px;"></div>
      <div id="fallLayer" style="position:absolute; top:0; left:0; width:220px; height:260px;"></div>
    </div>
    <p id="stageLabel" style="font-family:'Inter',sans-serif; color:#f0d878; margin-top:12px; font-size:0.95rem;">
      Putting the IDs in the jar...
    </p>
  </div>
  <div id="grid" class="winner-grid" style="display:none;"></div>
</div>

<style>
  body { margin:0; background:transparent; font-family:'Inter',sans-serif; }
  #jarBase.shaking { animation: shake 2.4s ease-in-out forwards; transform-origin: 50% 90%; }
  @keyframes shake {
    0%, 100% { transform: rotate(0deg); }
    8%  { transform: rotate(-9deg); }
    16% { transform: rotate(9deg); }
    24% { transform: rotate(-9deg); }
    32% { transform: rotate(9deg); }
    40% { transform: rotate(-7deg); }
    48% { transform: rotate(7deg); }
    56% { transform: rotate(-7deg); }
    64% { transform: rotate(7deg); }
    72% { transform: rotate(-4deg); }
    80% { transform: rotate(4deg); }
    88% { transform: rotate(-2deg); }
    94% { transform: rotate(2deg); }
  }
  .fall-slip {
    position:absolute;
    width:48px; height:24px;
    background: linear-gradient(135deg, #ffffff, #f2ecd9);
    border: 1.5px solid #2c4a63;
    border-radius: 3px;
    font-family:'Inter',sans-serif;
    font-size:10px;
    font-weight:700;
    color:#1a1a1a;
    display:flex; align-items:center; justify-content:center;
    opacity:0;
    animation: fallIn 0.8s ease-in forwards;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
  }
  @keyframes fallIn {
    0%   { opacity:0; transform: translate(0,0) rotate(0deg); }
    12%  { opacity:1; }
    75%  { opacity:1; }
    100% { opacity:0; transform: translate(var(--endx), var(--endy)) rotate(var(--rot)); }
  }
  .winner-grid {
    display:flex; flex-wrap:wrap; gap:12px; justify-content:center;
    margin-top:0.6rem; padding: 0 10px;
  }
  .wcard {
    background: linear-gradient(135deg, #ffffff, #e6edf3);
    border: 1.5px solid #c9a227;
    color:#1a1a1a;
    padding:12px 18px;
    border-radius:14px;
    font-weight:700;
    font-size:1.05rem;
    box-shadow: 0 3px 10px rgba(44,74,99,0.2);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    animation: popIn 0.4s ease both;
  }
  .wcard:hover {
    transform: translateY(-3px);
    box-shadow: 0 6px 16px rgba(44,74,99,0.3);
  }
  @keyframes popIn {
    0% { transform: scale(0); opacity:0;}
    70% { transform: scale(1.15); opacity:1;}
    100% { transform: scale(1);}
  }
</style>

<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.9.4/dist/confetti.browser.min.js"></script>
<script>
  const pool = __POOL_JSON__;
  const jarBase = document.getElementById('jarBase');
  const fallLayer = document.getElementById('fallLayer');
  const stageLabel = document.getElementById('stageLabel');

  function jarShell(bodyFill, bodyStroke) {
    return `
      <rect x="70" y="18" width="80" height="26" rx="8" fill="#c9a227"/>
      <rect x="70" y="18" width="80" height="8" rx="4" fill="#f0d878"/>
      <rect x="82" y="40" width="56" height="14" fill="#c9a227"/>
      <rect x="30" y="70" width="160" height="170" rx="22" fill="${bodyFill}" fill-opacity="0.55" stroke="${bodyStroke}" stroke-width="4"/>
    `;
  }

  function buildEmptyJarSVG() {
    return `<svg width="220" height="260" viewBox="0 0 220 260">${jarShell('#eef3f7', '#c9a227')}</svg>`;
  }

  function buildFullJarSVG(count) {
    const bodyX = 30, bodyY = 70, bodyW = 160, bodyH = 170, bodyRx = 22;
    const slipColors = ['#2c4a63', '#4a7096', '#6a8fab', '#1f3547'];
    const slipCount = Math.max(10, Math.min(34, count));
    let svg = `<svg width="220" height="260" viewBox="0 0 220 260">`;
    svg += `<rect x="70" y="18" width="80" height="26" rx="8" fill="#c9a227"/>`;
    svg += `<rect x="70" y="18" width="80" height="8" rx="4" fill="#f0d878"/>`;
    svg += `<rect x="82" y="40" width="56" height="14" fill="#c9a227"/>`;
    svg += `<clipPath id="jarClip"><rect x="${bodyX}" y="${bodyY}" width="${bodyW}" height="${bodyH}" rx="${bodyRx}"/></clipPath>`;
    svg += `<rect x="${bodyX}" y="${bodyY}" width="${bodyW}" height="${bodyH}" rx="${bodyRx}" fill="#eef3f7" fill-opacity="0.55" stroke="#c9a227" stroke-width="4"/>`;
    svg += `<g clip-path="url(#jarClip)">`;
    for (let i = 0; i < slipCount; i++) {
      const sx = bodyX + 14 + Math.random() * (bodyW - 50);
      const sy = bodyY + 30 + Math.random() * (bodyH - 55);
      const rot = Math.round(Math.random() * 70 - 35);
      const color = slipColors[i % slipColors.length];
      svg += `<rect x="${sx}" y="${sy}" width="30" height="16" rx="2" fill="${color}" transform="rotate(${rot} ${sx + 15} ${sy + 8})"/>`;
    }
    svg += `</g>`;
    svg += `<rect x="${bodyX}" y="${bodyY}" width="${bodyW}" height="${bodyH}" rx="${bodyRx}" fill="none" stroke="#c9a227" stroke-width="4"/>`;
    svg += `</svg>`;
    return svg;
  }

  // Phase 1 — show the empty jar, and a sample of real IDs on paper slips
  // falling down into it.
  jarBase.innerHTML = buildEmptyJarSVG();

  const sampleCount = Math.min(12, pool.length);
  const step = pool.length / sampleCount;
  let fallHtml = '';
  for (let i = 0; i < sampleCount; i++) {
    const id = pool[Math.floor(i * step)];
    const startX = 60 + Math.random() * 100;
    const startY = -40 - Math.random() * 50;
    const endX = 50 + Math.random() * 110;
    const endY = 110 + Math.random() * 70;
    const rot = Math.round(Math.random() * 50 - 25);
    const delay = i * 100;
    fallHtml += `<div class="fall-slip" style="left:${startX}px; top:${startY}px; animation-delay:${delay}ms; --endx:${endX - startX}px; --endy:${endY - startY}px; --rot:${rot}deg;">${id}</div>`;
  }
  fallLayer.innerHTML = fallHtml;

  const fallDuration = sampleCount * 100 + 900;

  // Phase 2 — swap in the full jar (slips now inside) and shake it.
  setTimeout(() => {
    fallLayer.style.display = 'none';
    jarBase.innerHTML = buildFullJarSVG(pool.length);
    jarBase.classList.add('shaking');
    stageLabel.textContent = 'Shaking the jar...';
  }, fallDuration);

  // Phase 3 — reveal the winners.
  setTimeout(() => {
    document.getElementById('jarWrap').style.display = 'none';
    const grid = document.getElementById('grid');
    grid.innerHTML = `__CARDS_HTML__`;
    grid.style.display = 'flex';
    if (window.confetti) {
      confetti({
        particleCount: 170,
        spread: 90,
        origin: { y: 0.5 },
        colors: ['#2c4a63', '#4a7096', '#c9a227', '#f0d878', '#ffffff']
      });
    }
  }, fallDuration + 2600);
</script>
"""


def render_spin_and_reveal(winners: list[str], pool_before: list[str]):
    cards_html = "".join(
        f'<div class="wcard" style="animation-delay:{i * 170}ms">{w}</div>'
        for i, w in enumerate(winners)
    )
    html = (
        _SPIN_TEMPLATE
        .replace("__POOL_JSON__", json.dumps(pool_before))
        .replace("__CARDS_HTML__", cards_html)
    )
    components.html(html, height=540, scrolling=False)


def render_static_grid(winners: list[str]):
    cards = "".join(f'<div class="wcard-s">{w}</div>' for w in winners)
    st.markdown(
        f"""
        <div style="display:flex; flex-wrap:wrap; justify-content:center; gap:12px; margin:0.5rem 0 1rem 0;">
          {cards}
        </div>
        <style>
          .wcard-s {{
            background: linear-gradient(135deg, #ffffff, #eaf1f8);
            border: 1.5px solid #c9a227;
            color:#1a1a1a;
            padding:11px 17px;
            border-radius:14px;
            font-family:'Inter',sans-serif;
            font-weight:700;
            font-size:1rem;
            box-shadow: 0 3px 10px rgba(44,74,99,0.15);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
          }}
          .wcard-s:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(44,74,99,0.25);
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_session_static_grid(winners: list[str]):
    """Centered flex layout (last row centers instead of staying left-aligned)
    — used on the Session pages, matching the spin-reveal's own card style."""
    cards = "".join(f'<div class="wcard-flex">{w}</div>' for w in winners)
    st.markdown(
        f"""
        <div style="display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin:0.5rem 0 1rem 0;">
          {cards}
        </div>
        <style>
          .wcard-flex {{
            background: linear-gradient(135deg, #ffffff, #eaf1f8);
            border: 1.5px solid #c9a227;
            color:#1a1a1a;
            padding:11px 17px;
            border-radius:14px;
            font-family:'Inter',sans-serif;
            font-weight:700;
            font-size:1rem;
            box-shadow: 0 3px 10px rgba(44,74,99,0.15);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
          }}
          .wcard-flex:hover {{
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(44,74,99,0.25);
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def open_winner_popup(round_title: str, winners: list[str], pool_before: list[str]):
    """Show the spin + reveal inside a modal dialog so the draw becomes the
    focus of the whole screen instead of appearing inline on the page."""

    @st.dialog(round_title, width="large")
    def _dialog():
        render_spin_and_reveal(winners, pool_before)

    _dialog()


def show_round(r: dict):
    """Render one round: draw button, then a focused popup with the spin+reveal
    the moment it's drawn. On later visits, shows the static winner grid inline."""
    st.subheader(f"Round {r['round']}")
    already_drawn = r["key"] in st.session_state.results
    can_draw = len(st.session_state.pool) >= 1

    if not already_drawn:
        if st.button(
            f"Spin & Draw {r['count']} Winners",
            key=f"btn_{r['key']}",
            disabled=not can_draw,
            type="primary",
        ):
            draw_round(r["key"], r["count"])
            winners = st.session_state.results[r["key"]]
            pool_before = st.session_state.pre_draw_pool.get(r["key"], winners)
            st.session_state.revealed.add(r["key"])
            open_winner_popup(f"Round {r['round']} Winners", winners, pool_before)
    else:
        winners = st.session_state.results[r["key"]]
        render_session_static_grid(winners)

    st.divider()
