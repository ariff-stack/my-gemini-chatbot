import streamlit as st
from google import genai
import os
from pypdf import PdfReader

# Konfigurasi halaman web
st.set_page_config(page_title="AI Chatbot multi-PDF", page_icon="🤖")
st.title("🤖 AI Chatbot Berkembar (Mod Multi-PDF)")

# 1. Ambil API Key daripada Secrets Streamlit
API_KEY = st.secrets["GEMINI_API_KEY"]
client = genai.Client(api_key=API_KEY)

# 2. Fungsi pintar untuk membaca dan mencantumkan TEKS daripada BANYAK FAIL PDF
def baca_semua_pdf():
    # Senaraikan semua nama fail PDF yang anda ada di GitHub
    senarai_fail = ["maklumat_kedai1.pdf", "maklumat_kedai2.pdf"]
    teks_keseluruhan = ""
    fail_dijumpai = False

    for nama_fail in senarai_fail:
        if os.path.exists(nama_fail):
            fail_dijumpai = True
            try:
                reader = PdfReader(nama_fail)
                # Ekstrak teks bagi setiap halaman dalam fail ini
                for page in reader.pages:
                    teks_keseluruhan += page.extract_text() + "\n"
                teks_keseluruhan += "\n--- TAMAT FAIL " + nama_fail + " ---\n\n"
            except Exception as e:
                st.error(f"Gagal membaca fail {nama_fail}: {e}")
                st.stop()
        else:
            st.warning(f"Nota: Fail '{nama_fail}' tidak dijumpai di GitHub.")

    # Jika langsung tiada fail yang wujud
    if not fail_dijumpai:
        st.error("Tiada satu pun fail PDF dijumpai di GitHub anda!")
        st.stop()

    return teks_keseluruhan

# Jalankan fungsi cantuman PDF
kandungan_dokumen = baca_semua_pdf()

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

# Masukkan dokumen rujukan gabungan terus ke dalam System Instruction
arahan_sistem = (
    "Anda adalah pembantu khidmat pelanggan yang mesra. "
    "JAWAB SOALAN HANYA berdasarkan dokumen rujukan yang diberikan di bawah ini. "
    "Jika jawapan tiada dalam dokumen rujukan, katakan dengan sopan bahawa anda tidak mempunyai maklumat tersebut.\n\n"
    f"--- DOKUMEN RUJUKAN GABUNGAN ---\n{kandungan_dokumen}"
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
if user_input := st.chat_input("Tanya saya apa-apa tentang kandungan dokumen..."):
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.chat_message("assistant"):
        with st.spinner("Menyemak semua dokumen rujukan..."):
            try:
                response = chat_session.send_message(user_input)
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})
            except Exception as e:
                st.error(f"Ralat berlaku: {e}")
