import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- 1. IMPOSTAZIONI GRAFICHE DELLA PAGINA ---
st.set_page_config(page_title="Estrattore Dati", page_icon="📦", layout="wide")

# --- INTESTAZIONE GRAFICA CON BANNER CENTRATO ---
col_spazio_sx, col_banner, col_spazio_dx = st.columns([1, 2, 1])
with col_banner:
    st.image("imm.png", use_container_width=True)

st.title("📦 Estrattore Automazione: Listini e Bolle")
st.markdown("Carica un documento (PDF o Immagine) e scegli le tue impostazioni di estrazione.")
st.markdown("---")

# --- APRE LA CASSAFORTE SEGRETA ---
try:
    API_KEY = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=API_KEY)
except KeyError:
    st.error("🔒 Errore: Chiave API non trovata nei Secrets di Streamlit.")
    st.stop()

# --- FUNZIONE AUTO-SELEZIONE MODELLO ---
@st.cache_resource
def ottieni_modello():
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                if 'gemini-1.5' in m.name:
                    return genai.GenerativeModel(m.name)
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods and 'gemini' in m.name:
                return genai.GenerativeModel(m.name)
    except Exception as e:
        return None
    return genai.GenerativeModel('gemini-1.5-flash')

model = ottieni_modello()

# --- LAYOUT A DUE COLONNE (CARICAMENTO E RISULTATI) ---
col_sinistra, col_destra = st.columns(2)

with col_sinistra:
    st.subheader("📄 1. Carica il Documento")
    uploaded_file = st.file_uploader("Trascina qui un PDF, JPG o PNG", type=["jpg", "jpeg", "png", "pdf"])
    
    st.markdown("---")
    st.subheader("⚙️ 2. Impostazioni")
    
    # --- NUOVO: SELETTORE MODALITÀ (3 OPZIONI) ---
    modalita = st.radio(
        "Cosa vuoi estrarre?",
        (
            "EAN + Quantità",
            "Solo EAN",
            "Solo Codice Interno (6 cifre)"
        )
    )
    
    # --- NUOVO: SELETTORE FORMATO ESPORTAZIONE ---
    formato = st.radio(
        "Formato di esportazione:",
        ("TXT", "CSV")
    )
    
    if uploaded_file is not None:
        if uploaded_file.name.lower().endswith('.pdf'):
            st.info(f"✅ Documento PDF caricato: **{uploaded_file.name}**")
        else:
            image = Image.open(uploaded_file)
            st.image(image, caption="Anteprima", use_container_width=True)

with col_destra:
    st.subheader("⚡ 3. Estrazione Dati")
    
    if uploaded_file is None:
        st.info("👈 Inizia caricando un documento a sinistra.")
    else:
        if st.button("🚀 Avvia Estrazione", type="primary", use_container_width=True):
            if model is None:
                st.error("Errore critico: Nessun modello AI disponibile.")
            else:
                with st.spinner("🤖 L'IA sta leggendo il documento... attendi qualche secondo."):
                    
                    # --- GESTIONE DEI 3 DIVERSI "CERVELLI" IN BASE ALLA MODALITÀ ---
                    if modalita == "EAN + Quantità":
                        prompt = """
                        Sei un estrattore di dati professionale. Guarda questo documento.
                        Contiene codici a barre e relative quantità.
                        
                        ISTRUZIONI TASSATIVE:
                        1. Estrai tutte le coppie: Codice e Quantità.
                        2. Scrivi una coppia per riga usando il separatore | (es: 8058664165889|4.00)
                        3. Correggi eventuali errori visivi (es. la stanghetta del cursore letta come '1').
                        4. LUNGHEZZA CODICI: I codici validi possono avere 8, 9 o 13 cifre. SOLO se trovi un codice di 14 o 15 cifre, rimuovi i numeri in eccesso all'inizio. Ignora i codici interni di 6 cifre.
                        5. Le quantità devono usare il PUNTO per i decimali (es. 10.00). Se la quantità è un numero intero (es. 4) scrivi 4.00.
                        6. RESTITUISCI SOLO LA LISTA, nessuna frase introduttiva.
                        """
                        nome_base = "ean_quantita"
                        
                    elif modalita == "Solo EAN":
                        prompt = """
                        Sei un estrattore di dati professionale. Guarda questo documento.
                        
                        ISTRUZIONI TASSATIVE:
                        1. Estrai ESCLUSIVAMENTE i codici EAN/a barre (solitamente di 8, 9 o 13 cifre). IGNORA le quantità e i codici interni di 6 cifre.
                        2. Scrivi un solo codice per riga (es: 8058664165889). Nessun altro carattere o separatore.
                        3. Correggi errori visivi. Se trovi codici anomali di 14 o 15 cifre, rimuovi i numeri in eccesso all'inizio per riportarli a 13 cifre.
                        4. RESTITUISCI SOLO LA LISTA DEI CODICI, nessuna frase introduttiva.
                        """
                        nome_base = "solo_ean"
                        
                    else:
                        # Modalità 3: "Solo Codice Interno"
                        prompt = """
                        Sei un estrattore di dati professionale. Guarda questo documento.
                        
                        ISTRUZIONI TASSATIVE:
                        1. Estrai ESCLUSIVAMENTE i codici interni composti da ESATTAMENTE 6 cifre. IGNORA completamente i codici EAN (8, 9 o 13 cifre), le quantità e i prezzi.
                        2. Scrivi un solo codice per riga (es: 123456). Nessun altro carattere, nessuno spazio, niente separatori.
                        3. Correggi eventuali errori visivi di lettura.
                        4. RESTITUISCI SOLO LA LISTA DEI CODICI A 6 CIFRE, nessuna frase introduttiva.
                        """
                        nome_base = "codici_interni"
                    
                    # --- CREAZIONE NOME FILE IN BASE AL FORMATO SCELTO ---
                    estensione = formato.lower() # diventa "txt" o "csv"
                    nome_file_download = f"{nome_base}.{estensione}"
                    mime_type = "text/csv" if formato == "CSV" else "text/plain"
                    
                    try:
                        if uploaded_file.name.lower().endswith('.pdf'):
                            document_part = {
                                "mime_type": "application/pdf",
                                "data": uploaded_file.getvalue()
                            }
                            input_dati = [prompt, document_part]
                        else:
                            input_dati = [prompt, image]
                            
                        response = model.generate_content(input_dati)
                        risultato = response.text.strip()
                        risultato = risultato.replace("```text", "").replace("```csv", "").replace("```", "").strip()
                        
                        st.success("✅ Estrazione completata con successo!")
                        
                        st.text_area("Anteprima Dati Estratti:", value=risultato, height=350)
                        
                        # --- PULSANTE DOWNLOAD DINAMICO ---
                        st.download_button(
                            label=f"📥 Scarica in formato {formato}",
                            data=risultato,
                            file_name=nome_file_download,
                            mime=mime_type,
                            use_container_width=True
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Si è verificato un errore durante l'estrazione: {e}")
