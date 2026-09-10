import pandas as pd
import streamlit as st

from core import (
    all_results_rows,
    back_button,
    init_state,
    inject_theme,
    load_participants,
    nav_card,
    page_header,
    parse_ids,
    render_static_grid,
    reset_all,
    round_label,
    rounds_for_session,
    section_label,
    show_round,
    status_panel,
    top_spacer,
)

st.set_page_config(
    page_title="Annual Dinner Lucky Draw",
    page_icon="🎟️",
    layout="wide",
)

init_state()
inject_theme()

page = st.session_state.page


# --------------------------------------------------------------------------
# HOME
# --------------------------------------------------------------------------
def render_home():
    top_spacer()
    page_header("Annual Dinner Lucky Draw")

    left, right = st.columns([2, 1], gap="large")

    with left:
        if not st.session_state.loaded:
            text = st.text_area(
                "Paste Worker ID here",
                key="paste_text",
                height=260,
                placeholder="1123, 1145, 1187 ...",
                label_visibility="collapsed",
            )
            entry_count = len(parse_ids(text))
            st.markdown(f'<span class="entries-pill">Entries: {entry_count}</span>', unsafe_allow_html=True)

            b1, b2 = st.columns([1, 1])
            with b1:
                if st.button("Load Participant", key="load_btn", disabled=entry_count == 0, use_container_width=True):
                    load_participants(parse_ids(text))
                    st.rerun()
            with b2:
                def _clear():
                    st.session_state.paste_text = ""
                st.button("Clear", on_click=_clear, key="clear_btn", use_container_width=True)
        else:
            st.success(f"{len(st.session_state.all_ids)} participants loaded")
            status_panel()
            st.divider()
            if st.button("Reset", key="reset_btn"):
                reset_all()
                st.rerun()

    with right:
        top_spacer()
        nav_card("Session 1", "session1", key="nav_s1")
        nav_card("Session 2", "session2", key="nav_s2")
        nav_card("Result", "result", key="nav_result")


# --------------------------------------------------------------------------
# SESSION PAGES
# --------------------------------------------------------------------------
def render_session(session_num: int):
    back_button()
    page_header("Annual Dinner Lucky Draw")
    section_label(f"Session {session_num}")

    if not st.session_state.loaded:
        st.warning("Go back and load your participant list first.")
        return

    left, right = st.columns([1, 3])
    with left:
        status_panel()
    with right:
        for r in rounds_for_session(session_num):
            show_round(r)


# --------------------------------------------------------------------------
# RESULT PAGE
# --------------------------------------------------------------------------
def render_result():
    back_button()
    page_header("Annual Dinner Lucky Draw")
    section_label("Result")

    rows = all_results_rows()
    if not rows:
        st.info("No draws yet. Results will appear here as you draw each round.")
        return

    df = pd.DataFrame(rows)

    for session_num in (1, 2):
        section_label(f"Session {session_num}")
        for r in rounds_for_session(session_num):
            round_label(f"Round {r['round']}")
            winners = st.session_state.results.get(r["key"])
            if winners:
                st.caption(f"{len(winners)} winners")
                render_static_grid(winners)
            else:
                st.caption("Not drawn yet.")
        st.divider()

    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download all results as CSV",
        data=csv,
        file_name="lucky_draw_results.csv",
        mime="text/csv",
    )


# --------------------------------------------------------------------------
# ROUTER
# --------------------------------------------------------------------------
if page == "home":
    render_home()
elif page == "session1":
    render_session(1)
elif page == "session2":
    render_session(2)
elif page == "result":
    render_result()
else:
    render_home()
