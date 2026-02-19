import streamlit as st
import google.generativeai as genai
from PIL import Image

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(page_title="Estrattore Listini", page_icon="📄")
st.title("Estrattore Codici a Barre e Prezzi 🚀")
st.write("Carica la foto o lo screenshot del listino. L'Intelligenza Artificiale estrarrà i dati formattati pronti per l'uso.")

# Inserisci qui la tua chiave API
API_KEY = "AIzaSyAXSgzC4AyYsesK4Jb0QDyH_zYz4h_mZ7k" 
genai.configure(api_key=API_KEY)

# Configurazione del mio "cervello" (Gemini 1.5 Flash è veloce e ottimo per leggere immagini)
model = genai.GenerativeModel('gemini-1.5-flash')

# --- CARICAMENTO FILE ---
uploaded_file = st.file_uploader("Scegli un'immagine (JPG, PNG)", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    # Mostra l'immagine che il collega ha caricato
    image = Image.open(uploaded_file)
    st.image(image, caption="Immagine caricata", use_container_width=True)
    
    if st.button("Estrai Dati", type="primary"):
        with st.spinner("L'Intelligenza Artificiale sta leggendo l'immagine... attendi qualche secondo."):
            
            # --- IL SUPER PROMPT PER GEMINI ---
            prompt = """
            Sei un estrattore di dati professionale. Guarda questa immagine.
            Contiene codici a barre e prezzi.
            
            ISTRUZIONI TASSATIVE:
            1. Estrai tutte le coppie: Codice a barre (13 cifre) e Prezzo.
            2. Scrivi una coppia per riga usando il separatore | (es: 8058664165889|4.00)
            3. Correggi eventuali errori visivi (es. la stanghetta del cursore letta come '1').
            4. I codici devono essere lunghi ESATTAMENTE 13 cifre. Se sono più lunghi, taglia l'inizio.
            5. I prezzi devono usare il PUNTO per i decimali (es. 10.00, non 10,00). Se è intero (es. 4) scrivi 4.00.
            6. RESTITUISCI SOLO LA LISTA, nessuna frase introduttiva.
            """
            
            try:
                # Mando la foto direttamente a me (Gemini)
                response = model.generate_content([prompt, image])
                risultato = response.text.strip()
                risultato = risultato.replace("```text", "").replace("```", "").strip()
                
                st.success("Estrazione completata con successo!")
                
                # Mostra l'anteprima
                st.text_area("Anteprima Dati Estratti:", value=risultato, height=300)
                
                # Pulsante di Download per il collega
                st.download_button(
                    label="📥 Scarica File TXT",
                    data=risultato,
                    file_name="dati_estratti.txt",
                    mime="text/plain"
                )
                
            except Exception as e:
                st.error(f"Si è verificato un errore di connessione: {e}")
