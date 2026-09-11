import json
import random

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# --------------------------------------------------------------------------
# DRAW STRUCTURE
# Edit COUNT here if the event details change.
# --------------------------------------------------------------------------
ROUNDS = [
    {"key": "s1r1", "session": 1, "round": 1, "count": 41},
    {"key": "s1r2", "session": 1, "round": 2, "count": 40},
    {"key": "s2r1", "session": 2, "round": 1, "count": 33},
    {"key": "s2r2", "session": 2, "round": 2, "count": 30},
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
        "confirmed": set(),
        "paste_text": "",
        "page": "home",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def parse_ids(text: str) -> list[str]:
    """Accepts any non-empty entry, comma- or newline-separated — no format
    restriction, so worker IDs, names, or any other identifier all work."""
    if not text or not text.strip():
        return []
    raw = text.replace(",", "\n").splitlines()
    return [x.strip() for x in raw if x.strip()]


def _normalize_header(value) -> str:
    """'No.KT', 'NO KT', 'no.kt' etc. all become 'nokt' for comparison."""
    if value is None:
        return ""
    return str(value).strip().lower().replace(".", "").replace(" ", "")


def parse_ids_from_file(uploaded_file) -> list[str]:
    """Reads worker IDs out of an uploaded CSV or Excel file.

    Specifically looks for a "No.KT" column header (spacing/punctuation
    don't matter — "NO KT", "No.KT", "no kt" all match) and collects every
    value listed beneath it, stopping at two blank cells in a row. This is
    built for registration sheets that have multiple sections (e.g. "with
    partner" / "without partner"), each with its own header row, running
    numbers, and extra columns — all of that gets ignored, only the actual
    No.KT values are collected, from every section found.

    If no "No.KT" header exists anywhere in the file, falls back to treating
    every non-empty cell as an ID — for plain files that are just a bare
    list with no header at all.

    Any internal spaces inside a value are stripped (e.g. "S 827" becomes
    "S827"), since ID numbers are sometimes typed with a stray space after
    a prefix letter. Raises on a genuine read failure (bad file, missing
    engine, etc.) so the caller can show what went wrong.
    """
    if uploaded_file is None:
        return []
    uploaded_file.seek(0)  # in case this same upload was already read earlier this run
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        df = pd.read_csv(uploaded_file, header=None, dtype=str)
    else:
        df = pd.read_excel(uploaded_file, header=None, dtype=str)

    def clean(value) -> str:
        return str(value).strip().replace(" ", "")

    n_rows, n_cols = df.shape
    ids: list[str] = []
    found_header = False

    for r in range(n_rows):
        for c in range(n_cols):
            if _normalize_header(df.iat[r, c]) == "nokt":
                found_header = True
                blank_streak = 0
                rr = r + 1
                while rr < n_rows:
                    val = df.iat[rr, c]
                    if val is None or str(val).strip() == "" or str(val).strip().lower() == "nan":
                        blank_streak += 1
                        if blank_streak >= 2:
                            break
                    else:
                        blank_streak = 0
                        ids.append(clean(val))
                    rr += 1

    if found_header:
        return ids

    # Fallback — no "No.KT" header anywhere, so treat every non-empty cell as an ID.
    for value in df.values.flatten().tolist():
        if value is None:
            continue
        text = clean(value)
        if text and text.lower() != "nan":
            ids.append(text)
    return ids


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
    st.session_state.confirmed = set()
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
                radial-gradient(ellipse 900px 500px at 50% -8%, rgba(201,162,39,0.10), transparent 60%),
                #143f69;
        }
        /* Gold dashed frame around the whole page, matching the Tentatif poster */
        .stApp::before {
            content: "";
            position: fixed;
            top: 14px; left: 14px; right: 14px; bottom: 14px;
            border: 2.5px dashed #e2aa3b;
            border-radius: 22px;
            pointer-events: none;
            z-index: 9999;
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
        /* Hide the dialog's built-in close "X". It can't be detected
           server-side (Streamlit has no callback for it), which is exactly
           what let the winner numbers leak early before — see
           open_winner_popup()'s docstring. The "Close & reveal on page"
           button inside the dialog is now the only way to close it. */
        button[aria-label="Close"] {
            display: none !important;
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
        /* The dialog otherwise inherits config.toml's backgroundColor directly
           (Streamlit's native modal styling, not our .stApp CSS) — so it was
           quietly following the page's denim blue instead of staying its own
           dark navy. Forcing it explicitly here decouples the two. */
        div[data-testid="stDialog"] {
            background-color: #0b1224 !important;
        }
        /* Hide the winner grid completely while the draw popup is open — the
           popup's backdrop (data-testid="stDialog") doesn't cover the full
           page width, so without this the grid rendered underneath was
           peeking through at the edges before the popup was even closed.
           This is pure CSS: it reacts instantly the moment the dialog is
           opened or closed, no rerun needed. */
        body:has([data-testid="stDialog"]) .round-winner-grid {
            visibility: hidden !important;
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


def render_id_list(ids: list[str]):
    """Scrollable box of small chips — one per loaded ID — so the whole
    list can be eyeballed at a glance instead of just trusting the count."""
    chips = "".join(f'<div class="id-chip">{i}</div>' for i in ids)
    st.markdown(
        f"""
        <div class="id-list-box">{chips}</div>
        <style>
          .id-list-box {{
            max-height: 260px;
            overflow-y: auto;
            display:flex; flex-wrap:wrap; gap:8px;
            padding: 12px;
            background: #131c33;
            border: 1px solid rgba(201,162,39,0.3);
            border-radius: 10px;
          }}
          .id-chip {{
            background:#0f1830;
            color:#f0d878;
            border:1px solid rgba(201,162,39,0.4);
            padding:5px 12px;
            border-radius:8px;
            font-size:0.85rem;
            font-weight:600;
          }}
        </style>
        """,
        unsafe_allow_html=True,
    )


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

  // Phase 3 — reveal the winners inside the popup too.
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
        <div class="round-winner-grid" style="display:flex; flex-wrap:wrap; gap:12px; justify-content:center; margin:0.5rem 0 1rem 0;">
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


def open_winner_popup(round_key: str, round_title: str, winners: list[str], pool_before: list[str]):
    """Show the spin + reveal inside a modal dialog so the draw becomes the
    focus of the whole screen instead of appearing inline on the page.

    Deliberately does NOT rely on the dialog's built-in "X" to close it —
    Streamlit has no way to detect that click server-side, so nothing could
    react to it. Instead there's a real button inside the dialog; clicking
    it is what marks this round "confirmed" and reruns the script, which is
    also the moment the winner grid is first allowed to render on the page
    underneath. Until that happens, the page shows nothing for this round —
    so there's no way for the real numbers to flash on screen before the
    popup has fully covered it.
    """

    @st.dialog(round_title, width="large")
    def _dialog():
        render_spin_and_reveal(winners, pool_before)
        if st.button("Close & reveal on page", key=f"confirm_{round_key}", type="primary", use_container_width=True):
            st.session_state.confirmed.add(round_key)
            st.rerun()

    _dialog()


def show_round(r: dict):
    """Render one round: draw button, then a focused popup with the spin+reveal
    the moment it's drawn. On later visits, shows the static winner grid inline.

    Drawing triggers an immediate st.rerun() BEFORE opening the popup — this
    matters because status_panel() (participants/pool counts) is rendered in
    the left column earlier in the same script pass than this function. Without
    the rerun, the counts shown would still reflect the pool *before* this
    round's draw until some later, unrelated interaction refreshed the page.
    Rerunning immediately makes the whole page — including those counts —
    reflect the new pool size right away.
    """
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
            st.rerun()
    else:
        winners = st.session_state.results[r["key"]]
        if r["key"] in st.session_state.confirmed:
            # Only reachable after the person clicked the in-popup button —
            # safe to show the real numbers now.
            render_session_static_grid(winners)
        elif r["key"] not in st.session_state.revealed:
            # First time seeing this round drawn: open the popup, and show
            # NOTHING on the page yet — nothing to leak before the popup has
            # fully covered the screen.
            st.session_state.revealed.add(r["key"])
            pool_before = st.session_state.pre_draw_pool.get(r["key"], winners)
            open_winner_popup(r["key"], f"Round {r['round']} Winners", winners, pool_before)
        else:
            # Popup already shown once but not yet confirmed (e.g. the person
            # dismissed it with the native X instead of the button) — offer a
            # way back in rather than leaving the round stuck with nothing.
            st.info("Winners drawn — reopen to reveal them.")
            if st.button("Reopen", key=f"reopen_{r['key']}"):
                pool_before = st.session_state.pre_draw_pool.get(r["key"], winners)
                open_winner_popup(r["key"], f"Round {r['round']} Winners", winners, pool_before)

    st.divider()
