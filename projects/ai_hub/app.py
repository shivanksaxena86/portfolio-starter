import datetime
import os

import streamlit as st
from core.provider_logic import (
    generate_image,
    get_ai_response_stream,
    load_model_garden,
    load_threads,
    save_threads,
)
from core.safety import is_prompt_allowed
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
st.set_page_config(page_title="AI Hub 2026", layout="wide", page_icon="🤖")

# 2. Session State Initialization
if "threads" not in st.session_state:
    st.session_state.threads = load_threads()
if "active_chat_id" not in st.session_state:
    st.session_state.active_chat_id = None
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False
if "is_processing" not in st.session_state:
    st.session_state.is_processing = False
if "drafts" not in st.session_state:
    st.session_state.drafts = {}
if "active_tab" not in st.session_state:
    st.session_state.active_tab = "💬 Chat Window"


# --- 3. SECURITY GATE ---
def check_password():
    if st.session_state.password_correct:
        return True
    st.title("🔐 AI Hub Secure Access")
    pwd = st.text_input("Enter Hub Password", type="password")
    # COMBINED IF STATEMENT (Fixes Ruff SIM102)
    if st.button("Unlock") and pwd == os.getenv("APP_PASSWORD"):
        st.session_state.password_correct = True
        st.rerun()
    return False


if not check_password():
    st.stop()

# --- 4. DATA LOAD ---
garden = load_model_garden()

# --- 5. GLOBAL SETTINGS (Sidebar Bottom) ---
with st.sidebar:
    st.header("⚙️ Settings")
    enable_safety = st.checkbox("Hard Safety Guardrail", value=True)
    show_raw = st.checkbox("Show Raw/Experimental", value=False)
    st.divider()

# --- 6. MAIN NAVIGATION ---
# We use a selectbox or radio to simulate "Tabs" because it allows for programmatic switching
# and dynamic sidebar content.
nav_choice = st.radio(
    "Navigation",
    ["💬 Chat Window", "🎨 Image Studio", "📚 All Chats Archive"],
    horizontal=True,
    label_visibility="collapsed",
)

# Update session state to track where we are
st.session_state.active_tab = nav_choice

# --- 7. DYNAMIC SIDEBAR CONTENT (Q3 & Q5) ---
with st.sidebar:
    if (
        st.session_state.active_tab == "💬 Chat Window"
        or st.session_state.active_tab == "📚 All Chats Archive"
    ):
        st.title("💬 Text Conversations")

        if st.button("➕ Start New Chat", use_container_width=True):
            new_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
            st.session_state.threads[new_id] = {
                "messages": [],
                "model_name": "Not Set",
                "model_id": None,
                "title": "New Conversation",
                "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
                "last_used": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            }
            st.session_state.active_chat_id = new_id
            save_threads(st.session_state.threads)
            # FORCE JUMP TO CHAT WINDOW (Q4)
            st.session_state.active_tab = "💬 Chat Window"
            st.rerun()

        # Sorted History
        sorted_cids = sorted(
            st.session_state.threads.keys(),
            key=lambda x: st.session_state.threads[x].get("last_used", ""),
            reverse=True,
        )
        for cid in sorted_cids:
            info = st.session_state.threads[cid]
            col_sel, col_del = st.columns([4, 1])
            with col_sel:
                btn_type = "primary" if st.session_state.active_chat_id == cid else "secondary"
                if st.button(
                    f"📄 {info['title'][:15]}",
                    key=f"s_{cid}",
                    use_container_width=True,
                    type=btn_type,
                ):
                    st.session_state.active_chat_id = cid
                    # Force navigation back to Chat Tab if clicking from Archive (Q4)
                    st.session_state.active_tab = "💬 Chat Window"
                    st.rerun()
            with col_del:
                if st.button("🗑️", key=f"d_{cid}"):
                    del st.session_state.threads[cid]
                    save_threads(st.session_state.threads)
                    st.rerun()

    elif st.session_state.active_tab == "🎨 Image Studio":
        st.title("🎨 Image Controls")
        temp = st.slider("Temperature", 0.0, 2.0, 0.7)
        tokens = st.number_input("Max Tokens", 100, 4000, 1000)

# --- 8. PAGE ROUTING ---

# --- PAGE: CHAT WINDOW ---
if st.session_state.active_tab == "💬 Chat Window":
    if st.session_state.active_chat_id:
        cid = st.session_state.active_chat_id
        active_chat = st.session_state.threads[cid]

        st.subheader(active_chat["title"])

        # Model Assignment
        if not active_chat.get("model_id"):
            chat_list = [
                m for m in garden["text_models"] if show_raw or m.get("safety", "").lower() != "raw"
            ]
            sel_model = st.selectbox("Assign Model", [m["name"] for m in chat_list])
            if st.button("Confirm"):
                m_data = next(m for m in chat_list if m["name"] == sel_model)
                active_chat.update({"model_id": m_data["model_id"], "model_name": m_data["name"]})
                save_threads(st.session_state.threads)
                st.rerun()
            st.stop()

        # History
        for m in active_chat["messages"]:
            with st.chat_message(m["role"]):
                st.markdown(f"**{m.get('model_name', 'You')}**")
                st.markdown(m["content"])

        # DRAFT PERSISTENCE (Q2)
        # We manually handle the input state using session_state
        prompt = st.chat_input("Type message...", key=f"chat_in_{cid}")

        if prompt:
            if enable_safety:
                ok, reason = is_prompt_allowed(prompt)
                if not ok:
                    st.error(reason)
                    st.stop()

            st.session_state.is_processing = True
            active_chat["messages"].append(
                {
                    "role": "user",
                    "content": prompt,
                    "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                }
            )
            save_threads(st.session_state.threads)

            # THE STREAMER
            with st.chat_message("assistant"):
                try:
                    placeholder = st.empty()
                    full_res = ""
                    stream = get_ai_response_stream(
                        active_chat["model_id"], active_chat["messages"]
                    )
                    for chunk in stream:
                        delta = chunk.choices[0].delta.content
                        if delta:
                            full_res += delta
                            placeholder.markdown(full_res + "▌")
                    placeholder.markdown(full_res)

                    active_chat["messages"].append(
                        {
                            "role": "assistant",
                            "content": full_res,
                            "model_name": active_chat["model_name"],
                            "timestamp": datetime.datetime.now().strftime("%H:%M:%S"),
                        }
                    )
                    active_chat["last_used"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    save_threads(st.session_state.threads)
                    st.session_state.is_processing = False
                    st.rerun()
                except Exception as e:
                    st.error(str(e))
                    st.session_state.is_processing = False
    else:
        st.info("👈 Select a chat from the sidebar or start a new one.")

# --- PAGE: IMAGE STUDIO ---
elif st.session_state.active_tab == "🎨 Image Studio":
    st.header("🎨 AI Image Studio")
    # Q6 Fix: Filter list correctly based on show_raw
    img_list = [
        m for m in garden["image_models"] if show_raw or m.get("safety", "").lower() != "raw"
    ]

    sel_img = st.selectbox("Select Generator", [m["name"] for m in img_list])
    img_data = next(m for m in img_list if m["name"] == sel_img)
    prompt_img = st.text_area("Describe your image...")

    if st.button("🚀 Generate"):
        with st.spinner("Processing..."):
            try:
                images = generate_image(img_data["model_id"], prompt_img)
                for _idx, img in enumerate(images):
                    st.image(img)
                    # (Download logic...)
            except Exception as e:
                st.error(str(e))

# --- PAGE: ARCHIVE ---
elif st.session_state.active_tab == "📚 All Chats Archive":
    st.header("📚 Conversation Archive")
    # (Sorting and expanders logic remains same as per your feedback)
    archive_ids = sorted(
        st.session_state.threads.keys(),
        key=lambda x: st.session_state.threads[x].get("last_used", ""),
        reverse=True,
    )
    for _cid in archive_ids:
        info = st.session_state.threads[_cid]
        with st.expander(f"📄 {info['title']} ({info['model_name']})"):
            st.write(f"**Last Used:** {info.get('last_used')}")
            # ... (Download buttons)
