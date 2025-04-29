# -*- coding: utf-8 -*-

from PIL import Image
import streamlit as st
import google.generativeai as genai
import os

# --- Importa Configurazioni ---
# Assicurati di avere un file 'configs.py' con le costanti appropriate.
try:
    from configs import SYSTEM_PROMPT, SAFETY_SETTINGS, GENERATION_CONFIG, MODEL_NAME
    # Assicurati che SYSTEM_PROMPT in configs.py chieda risposte in ITALIANO
    # Esempio: SYSTEM_PROMPT = "Sei un assistente AI... Rispondi sempre in ITALIANO..."
except ImportError:
    st.warning("File 'configs.py' non trovato. Utilizzo valori predefiniti in ITALIANO.")
    MODEL_NAME = 'gemini-1.5-flash'
    SYSTEM_PROMPT = "Analizza l'immagine/immagini radiografica fornita. **Rispondi sempre e solo in ITALIANO.** Descrivi eventuali anomalie o punti di interesse visibili in modo strutturato. Sii cauto e ricorda esplicitamente alla fine della risposta che questa è un'analisi AI preliminare, puramente informativa e non una diagnosi medica, e che è necessario consultare un medico radiologo."
    SAFETY_SETTINGS = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    GENERATION_CONFIG = {
        "temperature": 0.45,
        "top_p": 1,
        "top_k": 32,
        "max_output_tokens": 4096,
    }

# --- Configura Modello Gemini ---
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    if not api_key:
        st.error("Chiave API Gemini ('GEMINI_API_KEY') vuota trovata nei segreti. Impostala correttamente.")
        st.stop()
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        safety_settings=SAFETY_SETTINGS,
        generation_config=GENERATION_CONFIG,
        system_instruction=SYSTEM_PROMPT
    )
except KeyError:
    st.error("Chiave API Gemini ('GEMINI_API_KEY') non trovata nei segreti di Streamlit.")
    st.error("Vai su 'Manage app' -> 'Settings' -> 'Secrets' e aggiungi: \nGEMINI_API_KEY = \"LA_TUA_CHIAVE_API\"")
    st.stop()
except Exception as e:
    st.error(f"Errore durante la configurazione dell'API Gemini: {e}")
    st.stop()


# --- Funzione Principale dell'App ---
if __name__ == '__main__':

    # --- Impostazione Pagina ---
    st.set_page_config(page_title='Assistente AI per Radiografie', layout="wide")

    # --- IMMAGINE INTESTAZIONE / LANDING PAGE ---
    header_image_url = "https://cdn.leonardo.ai/users/b9c4238e-d77c-4148-bef5-4a02da79edff/generations/c75c937c-f984-4904-8a7f-e0449604d70b/Leonardo_Phoenix_10_Create_an_image_for_a_mobile_apps_landing_3.jpg"
    try:
        st.image(header_image_url, use_container_width=True)
    except Exception as img_err:
        st.warning(f"Avviso: Impossibile caricare l'immagine di intestazione. ({img_err})", icon="🖼️")

    st.title('🩺 Assistente AI per Radiografie')
    st.markdown("Carica le tue immagini radiografiche per un'analisi preliminare basata su IA.")
    st.markdown("---")

    # --- Disclaimer Medico ESSENZIALE ---
    st.error("""
    **⚠️ ATTENZIONE: Strumento AI NON Diagnostico! ⚠️**
    *   Questa applicazione fornisce un'analisi preliminare automatica e **NON sostituisce** il parere di un **medico radiologo qualificato**.
    *   L'IA può commettere errori. **NON utilizzare** questo strumento per autodiagnosi o decisioni mediche.
    *   Consulta **SEMPRE** un medico per l'interpretazione ufficiale delle tue radiografie e per qualsiasi consiglio sulla tua salute.
    """)
    st.markdown("---")


    # --- PASSO 1: CARICAMENTO IMMAGINI ---
    st.subheader("1. Carica le Radiografie 📤")
    st.markdown("Puoi caricare uno o più file di immagine (PNG, JPG, JPEG).")

    uploaded_files = st.file_uploader(
        'Clicca per selezionare o trascina qui le immagini:',
        type=['png', 'jpg', 'jpeg'],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

    # --- Area Visualizzazione Immagini Caricate e Pulsante Analisi (inferiore) ---
    images_data = [] # Lista per conservare gli oggetti PIL Image
    analysis_button_placeholder = st.empty() # Placeholder per il secondo pulsante
    preview_placeholder = st.empty() # Placeholder per l'anteprima e il pulsante post-upload

    if uploaded_files:
        with preview_placeholder.container(): # Mostra le anteprime nel loro contenitore
            st.markdown("---")
            st.markdown("**Immagini Caricate:**")
            # Usiamo colonne per un layout più compatto se ci sono poche immagini
            cols = st.columns(min(len(uploaded_files), 4)) # Max 4 colonne di anteprime
            col_idx = 0
            for uploaded_file in uploaded_files:
                try:
                    img = Image.open(uploaded_file)
                    images_data.append(img)
                    with cols[col_idx % len(cols)]: # Cicla tra le colonne
                        st.image(img, caption=f"{uploaded_file.name[:20]}..." if len(uploaded_file.name)>20 else uploaded_file.name , use_column_width=True)
                    col_idx += 1
                except Exception as e:
                    st.error(f"Errore apertura immagine '{uploaded_file.name}': {e}")
            st.markdown("---")

            # Mostra il *secondo* pulsante dopo le anteprime
            submit_btn_2 = st.button(
                '🔬 Analizza Ora le Immagini Caricate!',
                key='analyze_button_2',
                use_container_width=True,
                type="primary"
            )
    else:
        # Se non ci sono file, mostra solo il primo pulsante
         with analysis_button_placeholder.container():
              st.markdown("---") # Separatore
              st.markdown("☝️ Carica una o più immagini per iniziare.")
              # Non mostrare il pulsante qui se non ci sono file, l'utente deve prima caricare

    # --- PASSO 2: ANALIZZA (Logica + Pulsante Superiore/Inferiore) ---

    # Controlla se uno dei due pulsanti è stato premuto
    # Nota: Se 'submit_btn_2' non è stato ancora creato (perché nessun file è caricato), darà errore.
    # Gestiamo questo verificando se 'submit_btn_2' esiste nello scope locale.
    submit_btn_1_pressed = analysis_button_placeholder.button(
         '🔬 Avvia Analisi!',
         key='analyze_button_1',
         use_container_width=True,
         type="primary",
         disabled=not images_data # Disabilita se non ci sono immagini caricate valide
     )

    # Verifica se il secondo pulsante esiste ed è stato premuto
    submit_btn_2_pressed = False
    if 'submit_btn_2' in locals(): # Controlla se la variabile esiste
        submit_btn_2_pressed = submit_btn_2 # Usa il valore del bottone

    analysis_triggered = submit_btn_1_pressed or submit_btn_2_pressed

    # Placeholder per la risposta dell'AI
    response_placeholder = st.empty()

    if analysis_triggered and images_data:
        # Nascondi i pulsanti di analisi e mostra lo spinner/risposta
        analysis_button_placeholder.empty()
        preview_placeholder.empty() # Nasconde anche le anteprime e il secondo bottone durante/dopo l'analisi

        with response_placeholder.container():
            st.subheader("2. Analisi IA 🤖")
            with st.spinner("Analisi delle immagini in corso..."):
                try:
                    content_to_send = [
                        "Analizza le seguenti immagini radiografiche in ITALIANO, fornendo osservazioni per ciascuna se possibile, o un'analisi complessiva:",
                    ]
                    content_to_send.extend(images_data)

                    response = model.generate_content(content_to_send)

                    # Mostra Risposta
                    st.markdown("**Risultato Analisi Preliminare:**")
                    # Usiamo st.markdown per una migliore resa del testo generato
                    st.markdown(response.text)

                except Exception as e:
                     st.error(f"Errore durante l'analisi AI: {e}")
                     st.error("Impossibile completare l'analisi.")

    elif analysis_triggered and not images_data:
        st.warning("Per favore, carica almeno un'immagine valida prima di premere 'Analizza'.")

    # --- IMMAGINE FINALE IN BASSO ---
    st.markdown("---")
    footer_image_url = "https://cdn.leonardo.ai/users/b9c4238e-d77c-4148-bef5-4a02da79edff/generations/e7758e5e-ed2e-487c-9c55-382ed6d28106/Leonardo_Phoenix_10_Create_a_modern_welldefined_and_illustrati_3.jpg"
    try:
        st.image(footer_image_url, use_container_width=True) # Adatta alla larghezza
    except Exception as img_err:
        st.warning(f"Avviso: Impossibile caricare l'immagine finale. ({img_err})", icon="🖼️")

    st.caption("Applicazione sviluppata con Streamlit e Google Gemini. Ricorda: consulta sempre un medico qualificato.")
