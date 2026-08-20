import streamlit as st
from datetime import datetime, timedelta
import json
from io import StringIO
import random

st.set_page_config(page_title="IT‑AI Flashcard SRS", layout="wide")

# Load word bank from separate data.json
with open("data.json", "r", encoding="utf‑8") as f:
    vocab_data = json.load(f)

BOX_INTERVALS = {1: 1, 2: 2, 3: 4, 4: 7, 5: 14}

# Sync logic: auto add any new card id from data.json into session state
if "card_states" not in st.session_state:
    st.session_state.card_states = {}

for card in vocab_data:
    cid = card["id"]
    if cid not in st.session_state.card_states:
        st.session_state.card_states[cid] = {
            "box": 1,
            "lastReviewed": None,
            "nextReview": datetime.utcnow()
        }

def get_due_cards():
    now = datetime.utcnow()
    due = []
    for card in vocab_data:
        cid = card["id"]
        s = st.session_state.card_states[cid]
        if s["nextReview"] <= now:
            due.append({"card": card, "state": s})
    return due

def handle_review(card_id: str, remembered_correct: bool):
    now = datetime.utcnow()
    state = st.session_state.card_states[card_id]
    state["lastReviewed"] = now
    if remembered_correct:
        state["box"] = min(state["box"] + 1, 5)
    else:
        state["box"] = 1
    interval_days = BOX_INTERVALS[state["box"]]
    state["nextReview"] = now + timedelta(days=interval_days)

st.title("🇨🇳🇬🇧 IT‑AI Flashcards | 5‑Box Leitner SRS")

with st.expander("💾 Save / Load review progress (export JSON file)"):
    col_a, col_b = st.columns(2)
    with col_a:
        json_str = json.dumps(st.session_state.card_states, default=str, indent=2)
        st.download_button(
            label="Export current progress (.json)",
            data=json_str,
            file_name="flashcard_progress.json",
            mime="application/json"
        )
    with col_b:
        uploaded_file = st.file_uploader("Load saved progress file", type="json")
        if uploaded_file is not None:
            file_content = StringIO(uploaded_file.getvalue().decode("utf‑8"))
            loaded_states = json.load(file_content)
            st.session_state.card_states = loaded_states
            st.success("Progress loaded ✔")

if st.button("⚠️ Reset ALL progress (test only)"):
    st.session_state.card_states = {}
    st.rerun()

st.divider()

due_list = get_due_cards()
random.shuffle(due_list)

with st.expander("🔍 Debug due list"):
    st.write(f"Total due: {len(due_list)}")
    for item in due_list:
        st.write(f"{item['card']['chinese']}, box:{item['state']['box']}, nextReview:{item['state']['nextReview']}")

with st.sidebar:
    st.subheader("📊 Box Status")
    for box_num in range(1, 6):
        count = sum(1 for s in st.session_state.card_states.values() if s["box"] == box_num)
        st.markdown(f"Box {box_num}  `{BOX_INTERVALS[box_num]}d` : **{count} cards**")
    st.markdown(f"Total words in bank: {len(vocab_data)}")
    st.warning("⚠️ Refresh / sleep loses progress, export JSON before close.")

if not due_list:
    st.success("✅ No cards due for review, come back later.")
else:
    current_item = due_list[0]
    card = current_item["card"]
    state = current_item["state"]
    st.markdown(f"**Cards remaining for review: {len(due_list)}**")
    st.markdown(f"Current Box: {state['box']} | Next interval: {BOX_INTERVALS[state['box']]} days")
    st.divider()

    st.subheader(f"中文：{card['chinese']}")
    st.caption(f"Domain: {card['context']}")

    show_ans = st.button("Show Answer")
    if show_ans:
        st.subheader(f"English: {card['english']}")
        st.markdown(f"Example sentence: *{card['example']}*")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Got it, correct"):
                handle_review(card["id"], True)
                st.rerun()
        with c2:
            if st.button("❌ Could not recall"):
                handle_review(card["id"], False)
                st.rerun()
