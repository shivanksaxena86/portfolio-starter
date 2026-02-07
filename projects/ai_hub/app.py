import datetime
import os
from io import BytesIO

import requests
import streamlit as st
from core.provider_logic import generate_image, get_ai_response, load_model_garden
from core.safety import is_prompt_allowed
from dotenv import load_dotenv

# 1. Setup
load_dotenv()
st.set_page_config(page_title="AI Hub 2026", layout="wide", page_icon="🤖")

# 2. Session State Initialization
if "threads" not in st.session_state:
    st.session_state.threads = {}
if "active_thread_id" not in st.session_state:
    st.session_state.active_thread_id = None
if "password_correct" not in st.session_state:
    st.session_state.password_correct = False


# --- 3. SECURITY GATE ---
def check_password():
    if st.session_state.password_correct:
        return True
    st.title("🔐 AI Hub Secure Access")
    pwd = st.text_input("Enter Hub Password", type="password")
    if st.button("Unlock"):
        if pwd == os.getenv("APP_PASSWORD"):
            st.session_state.password_correct = True
            st.rerun()
        else:
            st.error("Incorrect password.")
    return False


if not check_password():
    st.stop()

# --- 4. DATA LOAD ---
garden = load_model_garden()

# --- 5. SIDEBAR: THREAD MANAGER ---
with st.sidebar:
    st.title("🧵 Chat Threads")

    if st.button("➕ New Chat", use_container_width=True):
        new_id = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        st.session_state.threads[new_id] = {
            "messages": [],
            "model_name": "Not Set",
            "model_id": None,
            "provider": None,
            "title": "New Conversation",
            "created": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
            "last_used": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        st.session_state.active_thread_id = new_id
        st.rerun()

    st.divider()

    for tid in list(st.session_state.threads.keys()):
        info = st.session_state.threads[tid]
        col_select, col_del = st.columns([4, 1])
        with col_select:
            if st.button(f"📄 {info['title'][:15]}...", key=f"sel_{tid}", use_container_width=True):
                st.session_state.active_thread_id = tid
                st.rerun()
        with col_del:
            if st.button("🗑️", key=f"del_{tid}"):
                del st.session_state.threads[tid]
                if st.session_state.active_thread_id == tid:
                    st.session_state.active_thread_id = None
                st.rerun()

    st.divider()
    st.header("⚙️ Settings")
    enable_safety = st.checkbox("Hard Safety Guardrail", value=True)
    show_raw = st.checkbox("Show Raw Models", value=False)
    temp = st.slider("Temperature", 0.0, 2.0, 0.7)
    tokens = st.number_input("Max Output Tokens", 100, 4000, 1000)

# --- 6. MAIN TABS ---
tabs = st.tabs(["💬 Universal Chat", "🎨 Image Studio", "📚 All Chats (Archive)"])

# --- TAB 1: UNIVERSAL CHAT ---
with tabs[0]:
    if st.session_state.active_thread_id:
        tid = st.session_state.active_thread_id
        active_thread = st.session_state.threads[tid]

        # UI: Thread Header with Rename Option
        col_title, col_rename = st.columns([3, 1])
        with col_title:
            st.subheader(f"Conversation: {active_thread['title']}")
        with col_rename:
            new_title = st.text_input(
                "Rename Thread", placeholder="Enter new title...", key=f"rename_{tid}"
            )
            if st.button("Update Title", key=f"upd_{tid}") and new_title.strip():
                active_thread["title"] = new_title
                st.rerun()

        # A. Model Assignment
        if not active_thread["model_id"]:
            chat_list = [
                m for m in garden["text_models"] if show_raw or m.get("safety", "").lower() != "raw"
            ]
            sel_model = st.selectbox(
                "Assign a model to start this thread", [m["name"] for m in chat_list]
            )
            if st.button("Confirm Model & Begin"):
                m_data = next(m for m in chat_list if m["name"] == sel_model)
                active_thread["model_id"] = m_data["model_id"]
                active_thread["model_name"] = m_data["name"]
                active_thread["provider"] = m_data["provider"]
                active_thread["title"] = f"Chat with {m_data['name']}"
                st.rerun()
            st.stop()

        # B. Render Messages
        for m in active_thread["messages"]:
            if m.get("role") == "system":
                continue
            with st.chat_message(m["role"]):
                label = (
                    f"**Assistant ({m.get('model_name')})**"
                    if m["role"] == "assistant"
                    else "**You**"
                )
                st.markdown(label)
                st.markdown(m["content"])
                st.caption(f"🕒 {m.get('timestamp', '')}")

        # C. Chat Input
        if prompt := st.chat_input("Type your message..."):
            if enable_safety:
                ok, reason = is_prompt_allowed(prompt)
                if not ok:
                    st.error(reason)
                    st.stop()

            now = datetime.datetime.now().strftime("%H:%M:%S")
            # --- BUG FIX: Consistent variable name ---
            user_msg = {"role": "user", "content": prompt, "timestamp": now}
            active_thread["messages"].append(user_msg)

            with st.chat_message("user"):
                st.markdown("**You**")
                st.markdown(prompt)

            with st.chat_message("assistant"):
                try:
                    sys_msg = "You are a helpful assistant." + (
                        " Strictly avoid NSFW." if enable_safety else " Mode: Raw."
                    )
                    # Pass the specific message list for this thread
                    api_payload = [{"role": "system", "content": sys_msg}] + active_thread[
                        "messages"
                    ]

                    with st.spinner(f"{active_thread['model_name']} is thinking..."):
                        res, usage = get_ai_response(
                            active_thread["model_id"], api_payload, temp, tokens
                        )

                    assistant_now = datetime.datetime.now().strftime("%H:%M:%S")
                    active_thread["messages"].append(
                        {
                            "role": "assistant",
                            "content": res,
                            "model_name": active_thread["model_name"],
                            "timestamp": assistant_now,
                        }
                    )
                    active_thread["last_used"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                    st.rerun()
                except Exception as e:
                    st.error(f"API Error: {str(e)}")
    else:
        st.info("👈 Create a 'New Chat' in the sidebar to begin.")

# --- TAB 2: IMAGE STUDIO ---
with tabs[1]:
    st.header("🎨 AI Image Studio")
    img_list = [
        m for m in garden["image_models"] if show_raw or m.get("safety", "").lower() != "raw"
    ]
    sel_img = st.selectbox("Select Generator", [m["name"] for m in img_list])
    img_data = next(m for m in img_list if m["name"] == sel_img)

    style = st.selectbox("Style Filter", ["None", "Cinematic", "Anime", "Cyberpunk"])
    prompt_img = st.text_area("Describe your image...")
    final_prompt = prompt_img if style == "None" else f"{prompt_img}, in the style of {style}"

    if st.button("🚀 Generate", type="primary"):
        with st.spinner("Creating..."):
            try:
                images = generate_image(img_data["model_id"], final_prompt)
                for idx, img in enumerate(images):
                    st.image(img)
                    buf = BytesIO()
                    if isinstance(img, str):
                        r = requests.get(img)
                        buf.write(r.content)
                    else:
                        img.save(buf, format="PNG")
                    st.download_button(
                        label=f"📥 Download Image {idx+1}",
                        data=buf.getvalue(),
                        file_name=f"ai_hub_{datetime.datetime.now().strftime('%H%M%S')}.png",
                        mime="image/png",
                        key=f"dl_{idx}",
                    )
            except Exception as e:
                st.error(str(e))

# --- TAB 3: ARCHIVE ---
with tabs[2]:
    st.header("📚 Conversation Archive")
    if st.session_state.threads:
        archive_table = []
        for _tid, info in st.session_state.threads.items():
            archive_table.append(
                {
                    "Title": info["title"],
                    "Model": info["model_name"],
                    "Created": info["created"],
                    "Last Active": info["last_used"],
                    "Msgs": len(info["messages"]),
                }
            )
        st.table(archive_table)
    else:
        st.info("No chat history found.")
