import streamlit as st
from google import genai
import os

# Konfigurasi halaman web
st.set_page_config(page_title="AI Chatbot Dokumen", page_icon="🤖")
st.title("🤖 AI Chatbot Berkembar (Mod Dokumen)")

# 1. Masukkan API Key anda
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# Latar belakang: Pastikan fail maklumat_kedai.txt wujud dalam folder yang sama
NAMA_FAIL = "maklumat_kedai.txt"

if not os.path.exists(NAMA_FAIL):
    st.error(f"Fail '{NAMA_FAIL}' tidak dijumpai! Sila cipta fail teks ini di dalam folder projek anda terlebih dahulu.")
    st.stop()

# 2. Muat naik fail ke Google Gemini API (Satu kali sahaja untuk mengelakkan muat naik berulang kali)
if "google_file_ref" not in st.session_state:
    with st.spinner("Sedang memuatkan dokumen rujukan ke sistem AI..."):
        try:
            # Muat naik fail dan simpan rujukannya dalam session_state
            st.session_state.google_file_ref = client.files.upload(file=NAMA_FAIL)
            st.success("Dokumen rujukan berjaya dimuatkan!")
        except Exception as e:
            st.error(f"Gagal memuat naik fail: {e}")
            st.stop()

# 3. Simpan SEJARAH sembang teks biasa dalam session_state
if "messages" not in st.session_state:
    st.session_state.messages = []

# 4. Bina semula sesi perbualan (chat history) untuk dihantar ke API
history_api = []
for msg in st.session_state.messages:
    role_api = "user" if msg["role"] == "user" else "model"
    history_api.append(
        genai.types.Content(
            role=role_api,
            parts=[genai.types.Part.from_text(text=msg["content"])]
        )
    )

# Cipta sesi chat dinamik dengan arahan sistem (System Instruction) khas RAG
chat_session = client.chats.create(
    model="gemini-2.5-flash",
    history=history_api,
    config=genai.types.GenerateContentConfig(
        system_instruction=(
            "Anda adalah pembantu khidmat pelanggan yang mesra. "
            "JAWAB SOALAN HANYA berdasarkan dokumen yang dilampirkan bersama mesej pengguna. "
            "Jika jawapan tiada dalam dokumen, katakan dengan sopan bahawa anda tidak mempunyai maklumat tersebut."
        )
    )
)

# 5. Paparkan semula mesej-mesej lama di skrin
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Kotak input untuk pengguna taip mesej
if user_input := st.chat_input("Tanya saya tentang maklumat kedai..."):
    # Paparkan mesej pengguna di UI
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    # Hantar mesej ke Gemini beserta lampiran fail rujukan
    with st.chat_message("assistant"):
        with st.spinner("Menyemak dokumen..."):
            try:
                # KUNCI UTAMA: Kita hantar rujukan fail bersama teks soalan pengguna
                kandungan_hantar = [st.session_state.google_file_ref, user_input]
                
                response = chat_session.send_message(kandungan_hantar)
                st.markdown(response.text)
                
                # Simpan mesej AI dalam sejarah
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ralat berlaku: {e}")
