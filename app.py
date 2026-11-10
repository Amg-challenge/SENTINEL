"""Sentinel · demo del prototipo.

Responsabile: Utente 3 · branch `interfaccia`.
Avvio locale:  streamlit run app.py

Struttura della demo (vedi documento di progetto v6):
  1. Demo del flusso   -> persona protetta, sportello, contatto di fiducia (il cuore del pitch)
  2. Sotto il cofano   -> calibrazione della soglia e stima degli alert (appendice)
  3. Confronto profili -> i tre tipi di minaccia a confronto
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from sentinel.economics import (curva_costo, perdita_attesa_evitata, soglia_ottimale,
                                stima_alert)
from sentinel.model import adatta_baseline, punteggia
from sentinel.profiles import COLONNE, PROFILI, genera_storico, inietta_frode
from sentinel.workflow import instrada, richiesta_revoca

st.set_page_config(page_title="Sentinel", page_icon="🛡️", layout="wide")


# ---------------------------------------------------------------- dati
@st.cache_data
def dati_profilo(profilo: str, seed: int = 1) -> pd.DataFrame:
    storico = genera_storico(profilo, giorni=365, seed=seed)
    base = adatta_baseline(storico)
    return punteggia(inietta_frode(storico, profilo, n=1, seed=seed + 1), base)


@st.cache_data
def baseline_demo() -> dict:
    return adatta_baseline(genera_storico("truffa_esterna", giorni=365, seed=1))


def valuta_prelievo(importo: float) -> pd.Series:
    """Punteggia il prelievo allo sportello della demo rispetto alle abitudini della persona."""
    op = pd.DataFrame([dict(data=pd.Timestamp("2026-01-05"), canale="sportello", importo=importo,
                            beneficiario="", estero=False, avviato_da="titolare",
                            alert_banca=False, frode=True)], columns=COLONNE)
    return punteggia(op, baseline_demo()).iloc[0]


# ---------------------------------------------------------------- stato della demo
PASSI = [
    "Attivazione con consenso",
    "Prelievo insolito allo sportello",
    "Verifica",
    "Esito",
    "Colpo di scena: il truffatore chiede di disattivare Sentinel",
]
if "passo" not in st.session_state:
    st.session_state.passo = 0

st.sidebar.title("🛡️ Sentinel")
st.sidebar.caption("Quando la banca vede qualcosa di strano, chiama la persona giusta: "
                   "quella di cui ti fidi.")
vista = st.sidebar.radio("Vista", ["1 · Demo del flusso", "2 · Sotto il cofano",
                                   "3 · Confronto profili"])


# ================================================================ 1 · DEMO
def demo():
    scenario = st.radio("Scenario", ["Truffa del falso poliziotto",
                                     "Conflitto d'interesse (il contatto ha una procura)"],
                        horizontal=True)
    conflitto = scenario.startswith("Conflitto")
    contatto = {"nome": "Figlia" if not conflitto else "Nipote",
                "ha_procura": conflitto, "cointestatario": False}
    importo = 40_000.0
    valutazione = valuta_prelievo(importo)
    destinazione, motivo = instrada({"avviato_da": "titolare", "beneficiario": ""}, contatto)

    passo = st.session_state.passo
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        st.button("◀ Indietro", disabled=passo == 0, on_click=_vai, args=(-1,))
    with c2:
        st.markdown(f"**Passo {passo + 1} di {len(PASSI)}** · {PASSI[passo]}")
    with c3:
        st.button("Avanti ▶", disabled=passo == len(PASSI) - 1, on_click=_vai, args=(1,))
    st.progress((passo + 1) / len(PASSI))
    st.divider()

    persona, sportello, terzo = st.columns(3)
    with persona:
        st.subheader("👵 Persona protetta")
        st.caption("Papà, 81 anni, Mendrisio")
        if passo == 0:
            st.checkbox("Attivo Sentinel per scelta mia", value=True, disabled=True)
            st.write(f"Contatto di fiducia: **{contatto['nome']}**")
            st.write("Soglie concordate: prelievi oltre **CHF 2'000**, cassetta, "
                     "bonifici a conti nuovi o esteri.")
            st.info("Vedo sempre chi mi segue e posso chiedere di cambiare le regole.")
        elif passo in (1, 2):
            st.write(f"Allo sportello chiede **CHF {importo:,.0f}** in contanti.".replace(",", "'"))
        elif passo == 3:
            st.success("Il prelievo è stato fermato. Nessun denaro è uscito dal conto.")
        else:
            st.warning("Al telefono il “poliziotto” insiste: *«Disattivi subito quel servizio»*.")
            r = richiesta_revoca()
            st.write("Richiesta di disattivazione registrata.")
            st.error(f"Effettiva solo dopo **72 ore** "
                     f"({r['effettiva_dal']:%d.%m %H:%M}). Il contatto è stato avvisato.")

    with sportello:
        st.subheader("🏦 Sportello")
        if passo == 0:
            st.caption("Nessuna operazione in corso.")
        elif passo in (1, 2):
            st.metric("Prelievo richiesto", f"CHF {importo:,.0f}".replace(",", "'"))
            st.error("⏸️ Operazione in pausa: Sentinel attivo")
            st.caption(f"Punteggio {valutazione['punteggio']:.1f} · {valutazione['motivi']}")
            st.write("In attesa di verifica: "
                     + ("contatto di fiducia" if destinazione == "contatto" else "**ufficio della banca**"))
        elif passo == 3:
            st.success("Operazione annullata. Suggerito il contatto con la polizia.")
        else:
            st.caption("Le regole restano attive fino alla scadenza delle 72 ore.")

    with terzo:
        if destinazione == "contatto":
            st.subheader(f"📱 {contatto['nome']} (contatto)")
            if passo == 2:
                st.warning(f"Tuo padre sta prelevando **CHF {importo:,.0f}** allo sportello "
                           f"di Mendrisio. L'hai sentito?".replace(",", "'"))
                b1, b2 = st.columns(2)
                b1.button("✅ Approvo", disabled=True)
                b2.button("⛔ Blocca", type="primary", on_click=_vai, args=(1,))
                st.caption("Non vedi il saldo e non puoi muovere denaro.")
            elif passo == 3:
                st.success("Hai bloccato l'operazione. Chiama tuo padre.")
            elif passo == 4:
                st.warning("Avviso: è stata chiesta la disattivazione di Sentinel. "
                           "Hai 72 ore per parlarne con tuo padre.")
            else:
                st.caption("Nessuna richiesta.")
        else:
            st.subheader("🗂️ Ufficio della banca")
            if passo >= 2:
                st.error(f"Caso escalato: {motivo}.")
                st.caption(f"Il contatto ({contatto['nome']}) non può approvare.")
                if passo == 2:
                    st.button("⛔ Blocca e chiama il cliente", type="primary",
                              on_click=_vai, args=(1,))
                elif passo == 3:
                    st.success("Bloccato dalla banca dopo la verifica con il cliente.")
            else:
                st.caption("Coda casi vuota.")


def _vai(delta: int):
    st.session_state.passo = max(0, min(len(PASSI) - 1, st.session_state.passo + delta))


# ================================================================ 2 · SOTTO IL COFANO
def sotto_il_cofano():
    st.header("Sotto il cofano: quando coinvolgere il contatto")
    st.caption("Sentinel non sostituisce l'antifrode della banca: ne riceve gli alert e "
               "aggiunge soglie personali e canali fisici. La soglia bilancia due costi: "
               "disturbare troppo il contatto e lasciar passare una truffa.")
    profilo = st.selectbox("Profilo", list(PROFILI), format_func=lambda p: PROFILI[p])
    df = dati_profilo(profilo)
    curva = curva_costo(df)
    s_opt = soglia_ottimale(curva)
    soglia = st.slider("Soglia di coinvolgimento", 0.0, 12.0, float(s_opt), 0.5)

    k = stima_alert(df, soglia)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Alert per cliente/anno", f"{k['alert_per_cliente_anno']:.1f}")
    m2.metric("Risolti dal contatto", f"{k['quota_contatto']:.0%}")
    m3.metric("Escalati alla banca", f"{k['quota_banca']:.0%}")
    m4.metric("Cost to serve (CHF/anno)", f"{k['cost_to_serve']:.2f}")
    st.caption(f"Soglia ottimale: {s_opt}. Frode intercettata (beneficio per il cliente): "
               f"CHF {perdita_attesa_evitata(df, soglia):,.0f}".replace(",", "'"))

    g1, g2 = st.columns(2)
    with g1:
        st.markdown("**Punteggio delle operazioni nel tempo**")
        serie = df.set_index("data")[["punteggio"]].assign(soglia=soglia)
        st.line_chart(serie)
    with g2:
        st.markdown("**Costo atteso per soglia**")
        st.line_chart(curva.set_index("soglia")[["costo"]])

    st.markdown("**Operazioni sopra la soglia**")
    st.dataframe(df[df["punteggio"] >= soglia][["data", "canale", "importo", "avviato_da",
                                                "punteggio", "motivi", "frode"]],
                 use_container_width=True, hide_index=True)


# ================================================================ 3 · CONFRONTO
def confronto():
    st.header("Confronto tra i tre tipi di minaccia")
    righe = []
    for p, descrizione in PROFILI.items():
        df = dati_profilo(p)
        s = soglia_ottimale(curva_costo(df))
        k = stima_alert(df, s)
        righe.append({"Profilo": descrizione, "Soglia ottimale": s,
                      "Frodi fermate": int(((df["punteggio"] >= s) & df["frode"]).sum()),
                      "Frodi totali": int(df["frode"].sum()),
                      "Alert/anno": k["alert_per_cliente_anno"],
                      "Quota alla banca": f"{k['quota_banca']:.0%}",
                      "Cost to serve CHF": k["cost_to_serve"]})
    st.dataframe(pd.DataFrame(righe), use_container_width=True, hide_index=True)
    st.caption("Dati sintetici, un cliente per profilo. Le ipotesi del pitch (~1,5 alert/anno, "
               "~80% al contatto, cost to serve ~CHF 7) vanno verificate su un portafoglio "
               "simulato di molti clienti (compito di Utente 2).")


if vista.startswith("1"):
    demo()
elif vista.startswith("2"):
    sotto_il_cofano()
else:
    confronto()
