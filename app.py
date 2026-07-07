import streamlit as st
from google import genai
import os
from pypdf import PdfReader  # Tambah pustaka pembaca PDF

# Konfigurasi halaman web
st.set_page_config(page_title="AI Chatbot Dokumen V2", page_icon="🤖")
st.title("🤖 AI Chatbot Berkembar (Mod PDF & Teks)")

# 1. Ambil API Key daripada Secrets Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 2. Fungsi pintar untuk membaca fail teks ATAU fail PDF
def baca_dokumen_rujukan():
    # Sistem akan cari fail PDF dahulu, jika tiada baru cari fail .txt
    if os.path.exists("maklumat_kedai.pdf"):
        try:
            reader = PdfReader("maklumat_kedai.pdf")
            teks_pdf = ""
            for page in reader.pages:
                teks_pdf += page.extract_text() + "\n"
            return teks_pdf
        except Exception as e:
            st.error(f"Gagal membaca fail PDF: {e}")
            st.stop()
            
    elif os.path.exists("maklumat_kedai.txt"):
        try:
            with open("maklumat_kedai.txt", "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            st.error(f"Gagal membaca fail teks: {e}")
            st.stop()
    else:
        st.error("Fail dokumen rujukan ('maklumat_kedai.pdf' atau 'maklumat_kedai.txt') tidak dijumpai di GitHub anda!")
        st.stop()

# Jalankan fungsi pembacaan fail
kandungan_dokumen = baca_dokumen_rujukan()

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

# Masukkan dokumen rujukan terus ke dalam System Instruction
arahan_sistem = (
    "Anda adalah pembantu khidmat pelanggan yang mesra. "
    "JAWAB SOALAN HANYA berdasarkan dokumen rujukan yang diberikan di bawah ini. "
    "Jika jawapan tiada dalam dokumen rujukan, katakan dengan sopan bahawa anda tidak mempunyai maklumat tersebut.\n\n"
    f"--- DOKUMEN RUJUKAN KEDAI ---\n{kandungan_dokumen}"
)

# Cipta sesi chat dinamik
chat_session = client.chats.create(
    model="gemini-2.5-flash",
    history=history_api,
    config=genai.types.GenerateContentConfig(
        system_instruction=arahan_sistem
    )
)

# 5. Paparkan semula mesej-mesej lama di skrin
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 6. Kotak input untuk pengguna taip mesej
if user_input := st.chat_input("Tanya saya tentang maklumat dokumen..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Menyemak dokumen..."):
            try:
                response = chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ralat berlaku: {e}")
