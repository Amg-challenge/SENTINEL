"""Sentinel - protection flow demo (Streamlit).

Owner: Utente 3 · branch `interfaccia`.  Run:  streamlit run app.py

Based on the prototype built by Stefano, aligned with document v6 and work plan v2.
The demo follows the pitch order: first the FLOW (protected person, bank counter,
trusted contact, bank queue), then the analysis as an appendix.

Guiding principle: Sentinel does not detect fraud in place of the bank. It sits on
top of the existing antifraud system and decides WHEN to involve someone and WHO:
the trusted contact or, when there is a conflict of interest, the bank itself.

Note: internal data keys (canale, importo, beneficiario...) stay in Italian because
they match the columns of the sentinel package; all text shown to the user is English.
"""
from __future__ import annotations

import altair as alt
import pandas as pd
import streamlit as st

from sentinel import economics, model, profiles
from sentinel.workflow import (ATTESA_REVOCA_ORE, FINESTRA_RISPOSTA_MIN, Contatto, decidi,
                               destinazione_finale)

st.set_page_config(page_title="Sentinel", page_icon="🛡️", layout="wide")

st.markdown("""
<style>
#MainMenu, footer {visibility: hidden;}
.phone {max-width: 380px; background:#12233a; border-radius:26px;
        padding:16px 16px 22px; color:#e9eef5;
        box-shadow:0 12px 30px rgba(0,0,0,.22);}
.phone .bar {display:flex; justify-content:space-between; font-size:11px;
             opacity:.55; margin-bottom:14px;}
.phone .app {font-size:10px; letter-spacing:.10em; text-transform:uppercase;
             opacity:.65; margin-bottom:6px;}
.phone .bubble {background:#1f3a5f; border-radius:18px; padding:14px 16px;
                line-height:1.5; font-size:14px;}
.phone .amount {font-size:19px; font-weight:700; color:#ff9c7a;}
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------- scenarios
# The first one is the hero story of the pitch (v6, page 1).
SCENARI = {
    "Fake police officer: cash at the counter": dict(
        canale="sportello", importo=40000.0, beneficiario="", nuovo_beneficiario=False,
        estero=False, avviata_da="titolare", alert_banca=False,
        etichetta="cash withdrawal at the counter",
        messaggio="is withdrawing <span class='amount'>CHF 40,000</span> in cash at the Mendrisio branch.",
        racconto=("A man claiming to be a police officer has been on the phone with the client "
                  "for an hour: his savings are 'at risk' and must be handed over for safekeeping."),
    ),
    "Fake grandchild: transfer abroad": dict(
        canale="bonifico", importo=18000.0, beneficiario="Foreign IBAN LT62 …",
        nuovo_beneficiario=True, estero=True, avviata_da="titolare", alert_banca=False,
        etichetta="transfer to a new foreign account",
        messaggio=("is sending a transfer of <span class='amount'>CHF 18,000</span> to a "
                   "foreign account he has never used before."),
        racconto=("A distressing call from a 'grandchild' in trouble: an urgent payment "
                  "is needed today, to an account abroad."),
    ),
    "Safe deposit box opened": dict(
        canale="cassetta", importo=0.0, beneficiario="", nuovo_beneficiario=False,
        estero=False, avviata_da="titolare", alert_banca=False,
        etichetta="safe deposit box access",
        messaggio=("is opening his <b>safe deposit box</b> at the Mendrisio branch. "
                   "He has not opened it in over a year."),
        racconto=("Fake police officers often ask victims to empty the safe deposit box "
                  "first: gold and cash leave no trace in the payment systems."),
    ),
    "Internal abuse: the contact initiated it": dict(
        canale="bancomat", importo=12000.0, beneficiario="", nuovo_beneficiario=False,
        estero=False, avviata_da="__contatto__", alert_banca=False,
        etichetta="cash withdrawal",
        messaggio="is withdrawing <span class='amount'>CHF 12,000</span> in cash.",
        racconto=("The withdrawal was initiated by the trusted contact. They cannot verify "
                  "themselves, so the case goes straight to the bank."),
    ),
    "Flagged by the bank's antifraud": dict(
        canale="bancomat", importo=200.0, beneficiario="", nuovo_beneficiario=False,
        estero=False, avviata_da="titolare", alert_banca=True,
        etichetta="cash withdrawal",
        messaggio="is withdrawing <span class='amount'>CHF 200</span> at an ATM.",
        racconto=("An ordinary withdrawal, below Sentinel's own threshold. The bank's antifraud "
                  "system flags it because it sees patterns a personal baseline cannot: "
                  "Sentinel works on top of that system."),
    ),
}

DEST = {"contatto": "trusted contact", "banca": "bank"}

# ----------------------------------------------------------------- state
if "config" not in st.session_state:
    st.session_state.config = dict(attivo=False, contatto="Anna",
                                   ha_procura=False, cotitolare=False)
if "esiti" not in st.session_state:
    st.session_state.esiti = {}
if "richiesta" not in st.session_state:
    st.session_state.richiesta = None       # pending revocation or change
if "ore_trascorse" not in st.session_state:
    st.session_state.ore_trascorse = 0      # demo clock (72h delay)
if "minuti" not in st.session_state:
    st.session_state.minuti = 0             # demo clock (response window)

cfgs = st.session_state.config


def ore_restanti() -> int:
    if not st.session_state.richiesta:
        return 0
    return max(0, ATTESA_REVOCA_ORE - int(st.session_state.ore_trascorse))


def applica_se_scaduta() -> None:
    """Once the 72 hours have elapsed, the request takes effect."""
    r = st.session_state.richiesta
    if r and ore_restanti() == 0:
        if r["tipo"] == "disattivazione":
            st.session_state.config["attivo"] = False
        elif r["tipo"] == "cambio_contatto":
            st.session_state.config["contatto"] = r["nuovo_contatto"]
        st.session_state.richiesta = None
        st.session_state.ore_trascorse = 0
        st.session_state.ultima_applicata = r["tipo"]


applica_se_scaduta()

# ----------------------------------------------------------------- engine
SEED_PADRE = 7   # the protected person of the demo: a typical senior, no box visit last year


@st.cache_data(show_spinner="Learning the client's habits...")
def baseline_padre() -> model.Baseline:
    return model.adatta_baseline(profiles.genera_storico("anziano", seed=SEED_PADRE))


@st.cache_data(show_spinner="Calibrating the threshold on a simulated portfolio...")
def calibrazione(n_clienti: int = 150) -> dict:
    """Threshold, curves and operational load from a simulated book of seniors.

    Frauds are oversampled (15% of clients) and re-weighted to a 1% real prevalence.
    """
    port = profiles.genera_portafoglio(n_clienti=n_clienti, prob_frode=0.15, seed=11)
    scored = economics.punteggia_portafoglio(port)
    curva, soglia = economics.calibra_soglia(scored)
    in_scope = scored[scored["canale"] != "carta"]       # card payments are out of scope
    roc, auc = economics.curva_roc(in_scope.loc[~in_scope["frode_reale"], "punteggio"],
                                   in_scope.loc[in_scope["frode_reale"], "punteggio"])
    carico = economics.stima_alert(scored[~scored["frode_reale"]], soglia)
    protetto = economics.importo_protetto(scored, soglia)
    return dict(curva=curva, soglia=soglia, roc=roc, auc=auc, carico=carico, protetto=protetto)


@st.cache_data(show_spinner="Calibrating the three populations...")
def confronto_profili(n_clienti: int = 60) -> pd.DataFrame:
    """The same engine, calibrated separately on each population."""
    righe = []
    for chiave, cfg_p in profiles.PRESET.items():
        port = profiles.genera_portafoglio(n_clienti=n_clienti, mix_popolazione={chiave: 1.0},
                                           prob_frode=0.2, seed=21)
        sc = economics.punteggia_portafoglio(port)
        _, s = economics.calibra_soglia(sc)
        ins = sc[sc["canale"] != "carta"]
        _, auc_p = economics.curva_roc(ins.loc[~ins["frode_reale"], "punteggio"],
                                       ins.loc[ins["frode_reale"], "punteggio"])
        carico = economics.stima_alert(sc[~sc["frode_reale"]], s)
        prot = economics.importo_protetto(sc, s)
        righe.append({
            "population": cfg_p.nome,
            "threshold": round(s, 2),
            "AUC": round(auc_p, 3),
            "fraud episodes caught": f"{100 * prot['episodi_intercettati']:.0f}%",
            "fraud money protected": f"{100 * prot['importo_protetto']:.0f}%",
            "alerts per client per year": round(carico["alert_per_cliente_anno"], 2),
        })
    return pd.DataFrame(righe)


base = baseline_padre()
cal = calibrazione()
soglia = cal["soglia"]


def operazione(nome_scenario: str) -> dict:
    sc = dict(SCENARI[nome_scenario])
    if sc["avviata_da"] == "__contatto__":
        sc["avviata_da"] = cfgs["contatto"]
    return sc


def valuta(nome_scenario: str):
    """Score and decision for one scenario, under the current configuration."""
    sc = operazione(nome_scenario)
    contatto = Contatto(cfgs["contatto"], ha_procura=cfgs["ha_procura"],
                        cotitolare=cfgs["cotitolare"])
    punteggio = model.punteggio(sc, base)
    dec = decidi(sc, punteggio, soglia, contatto, alert_esterno=sc["alert_banca"])
    return sc, punteggio, dec


def motivi_testo(sc: dict) -> str:
    righe = [m for m, _ in model.spiega(sc, base)]
    if sc["alert_banca"]:
        righe.append("flagged by the bank's antifraud system")
    return "; ".join(righe) if righe else "no anomaly"


# ----------------------------------------------------------------- sidebar
with st.sidebar:
    st.markdown("### 🛡️ Sentinel")
    st.caption("When the bank sees something strange, it calls the right person: "
               "the one you trust.")
    vista = st.radio("Screen", [
        "1 · Protected person",
        "2 · Bank counter",
        "3 · Trusted contact",
        "4 · Bank case queue",
        "Appendix · Analysis",
    ])
    st.divider()
    scenario = st.selectbox("Current scenario", list(SCENARI.keys()))
    if st.button("Reset decisions", width="stretch"):
        st.session_state.esiti = {}
    st.divider()
    with st.expander("Demo controls"):
        st.caption("Clocks are simulated: on stage you cannot wait 30 minutes, "
                   "let alone 72 hours.")
        st.slider("Minutes since the notification", 0, 60, key="minuti")
        st.slider("Hours since the revocation request", 0, ATTESA_REVOCA_ORE,
                  key="ore_trascorse")


def stato(nome_scenario):
    """Scenario state, including escalation when the response window expires."""
    sc_, punteggio_, dec_ = valuta(nome_scenario)
    esito_ = st.session_state.esiti.get(nome_scenario, "pending")
    contatto_ = Contatto(cfgs["contatto"], ha_procura=cfgs["ha_procura"],
                         cotitolare=cfgs["cotitolare"])
    if dec_.in_pausa:
        dest_, motivo_ = destinazione_finale(
            sc_, contatto_, risponde=(esito_ != "pending"),
            minuti_trascorsi=int(st.session_state.minuti))
    else:
        dest_, motivo_ = None, dec_.motivo
    scaduta_ = dec_.in_pausa and dec_.destinazione == "contatto" and dest_ == "banca"
    return sc_, punteggio_, dec_, esito_, dest_, motivo_, scaduta_


sc, punteggio, dec, esito, dest_eff, motivo_eff, scaduta = stato(scenario)

# ================================================================= 1
if vista.startswith("1"):
    st.title("The protected person")
    st.caption("Sentinel is switched on by the person's own choice. It is never imposed.")

    col1, col2 = st.columns([2, 3])
    with col1:
        st.subheader("Activation")
        attivo = st.checkbox(
            "I consent to activating Sentinel on my account",
            value=cfgs["attivo"],
            help="Without this consent the service does not start.")
        contatto = st.text_input("Trusted contact", value=cfgs["contatto"])
        st.markdown("**The contact's relationship with the account**")
        proc = st.checkbox("Holds a power of attorney on my account", value=cfgs["ha_procura"])
        cot = st.checkbox("Is a co-holder of the account", value=cfgs["cotitolare"])
        st.session_state.config.update(attivo=attivo, contatto=contatto,
                                       ha_procura=proc, cotitolare=cot)

    with col2:
        st.subheader("What the contact sees, and what they can do")
        if attivo:
            st.success(f"Sentinel is active. Your trusted contact is **{contatto}**.")
        else:
            st.warning("Sentinel is not active: without your consent it does not intervene.")
        st.markdown(
            f"""
- **{contatto}** is notified only for cash at the counter, safe deposit box visits and
  transfers to new or foreign accounts that fall outside your normal pattern.
- They cannot see your balance, cannot see your history, cannot move money.
- They can only **approve** or **block** the flagged transaction.
- If {contatto} has an interest in the transaction, the case goes to the bank instead.
- If {contatto} does not answer within {FINESTRA_RISPOSTA_MIN} minutes, the bank takes over.
- You can switch Sentinel off or change the rules at any time, with a
  {ATTESA_REVOCA_ORE}-hour safety delay.
            """)
        if proc or cot:
            st.info(f"Because {contatto} has access to your account, every flagged case will "
                    "go to the bank, never to them. You may prefer a contact without access.")
        st.caption(f"Intervention threshold, calibrated on simulated habits: {soglia:.2f}")

    st.divider()
    st.subheader(f"Revocation and changes · {ATTESA_REVOCA_ORE}-hour safety delay")
    if st.session_state.pop("ultima_applicata", None):
        st.info(f"The {ATTESA_REVOCA_ORE}-hour delay has elapsed: the request has been applied.")

    r = st.session_state.richiesta
    if r is None:
        st.caption(f"Switching Sentinel off, or changing the contact, does not take effect "
                   f"immediately: it requires a {ATTESA_REVOCA_ORE}-hour delay and the contact "
                   "is notified straight away. This is what stops a fraudster from having "
                   "the protection switched off during a phone call.")
        a, b = st.columns(2)
        with a:
            if st.button("Request deactivation", width="stretch"):
                st.session_state.richiesta = {"tipo": "disattivazione"}
                st.session_state.ore_trascorse = 0
                st.rerun()
        with b:
            nuovo = st.text_input("New trusted contact", value="")
            if st.button("Request contact change", width="stretch"):
                if nuovo.strip():
                    st.session_state.richiesta = {"tipo": "cambio_contatto",
                                                  "nuovo_contatto": nuovo.strip()}
                    st.session_state.ore_trascorse = 0
                    st.rerun()
    else:
        descr = ("deactivation of Sentinel" if r["tipo"] == "disattivazione"
                 else "change of trusted contact to " + r.get("nuovo_contatto", ""))
        st.warning(f"Pending: **{descr}**. It will take effect in "
                   f"**{ore_restanti()} hours**. Protection stays active meanwhile, "
                   f"and **{cfgs['contatto']}** has already been notified.")
        if st.button("Cancel the request"):
            st.session_state.richiesta = None
            st.session_state.ore_trascorse = 0
            st.rerun()

# ================================================================= 2
elif vista.startswith("2"):
    st.title("The bank counter")
    st.caption("The teller sees the status of the transaction in real time.")
    st.markdown(f"*{sc['racconto']}*")

    if not cfgs["attivo"]:
        st.warning("Sentinel is not active on this account: the transaction proceeds "
                   "without verification. (Activate it on screen 1.)")
    else:
        c1, c2, c3 = st.columns(3)
        c1.metric("Operation", f"CHF {sc['importo']:,.0f}" if sc["importo"] else "Box access")
        c2.metric("Anomaly score", f"{punteggio:.2f}", f"threshold {soglia:.2f}",
                  delta_color="off")
        c3.metric("Verification sent to", DEST.get(dest_eff, "nobody"))

        st.divider()
        if not dec.in_pausa:
            st.success("Within normal behaviour: no verification needed, proceed.")
        elif esito == "approved":
            st.success(f"✅ Approved by {cfgs['contatto']}. The teller may proceed.")
        elif esito == "blocked":
            st.error("⛔ Blocked. The teller does not execute the transaction and "
                     "suggests contacting the police.")
        else:
            st.warning("⏸️ **Transaction on hold** — awaiting verification.")
            st.markdown(f"**Why:** {motivi_testo(sc)}.")
            if scaduta:
                st.info(f"**{cfgs['contatto']}** did not answer within "
                        f"{FINESTRA_RISPOSTA_MIN} minutes: the case has been escalated "
                        "to the bank's internal review (screen 4). A transaction is "
                        "never left hanging.")
            elif dest_eff == "banca":
                st.info(f"Escalated to the bank's internal review (screen 4), not to the "
                        f"trusted contact: {motivo_eff}.")
            else:
                st.info(f"Notification sent to **{cfgs['contatto']}** (screen 3).")

# ================================================================= 3
elif vista.startswith("3"):
    st.title("The trusted contact")
    st.caption("Receives the notification on their phone. Never sees the account.")

    _r = st.session_state.richiesta
    if _r:
        _descr = ("switch Sentinel off" if _r["tipo"] == "disattivazione"
                  else "change the trusted contact to " + _r.get("nuovo_contatto", ""))
        st.error(f"Warning: a request to **{_descr}** has been made. It takes effect in "
                 f"**{ore_restanti()} hours**. If you know nothing about it, speak to "
                 "the person or alert the bank.")

    if not cfgs["attivo"]:
        st.warning("Sentinel is not active: no notification.")
    elif not dec.in_pausa:
        st.success("Nothing to verify at the moment.")
    elif scaduta:
        st.warning(f"The {FINESTRA_RISPOSTA_MIN}-minute window has expired without an "
                   "answer. The case has gone to the bank's internal review.")
    elif dest_eff == "banca":
        st.error("This case was **not** forwarded to you.")
        st.markdown(f"Reason: {motivo_eff}.")
        st.caption("Sentinel never asks for confirmation from someone who has an "
                   "interest in the transaction: that case goes to the bank.")
    else:
        st.markdown(f"""
<div class="phone">
  <div class="bar"><span>09:41</span><span>●●● ▮</span></div>
  <div class="app">Sentinel · notification</div>
  <div class="bubble">
    Your father {sc['messaggio']}<br><br>
    Have you spoken to him? Do you approve?
  </div>
</div>
""", unsafe_allow_html=True)
        st.caption("You see neither the balance nor the history: only this transaction.")
        restanti = max(0, FINESTRA_RISPOSTA_MIN - int(st.session_state.minuti))
        st.info(f"You have **{restanti} minutes** left to answer. After that the case "
                "goes to the bank's internal review.")
        b1, b2 = st.columns(2)
        if b1.button("✅ Approve", width="stretch"):
            st.session_state.esiti[scenario] = "approved"
            st.rerun()
        if b2.button("🛑 Block", type="primary", width="stretch"):
            st.session_state.esiti[scenario] = "blocked"
            st.rerun()
        if esito != "pending":
            st.info(f"You have already answered: transaction **{esito}**.")

# ================================================================= 4
elif vista.startswith("4"):
    st.title("Case queue · bank internal review")
    st.caption("Conflict-of-interest cases and unanswered notifications land here. "
               "They never reach a contact who has an interest in the transaction.")

    righe = []
    if cfgs["attivo"]:
        for nome in SCENARI:
            s, p, d, e, dest_n, motivo_n, scad_n = stato(nome)
            if d.in_pausa and dest_n == "banca":
                righe.append({
                    "scenario": nome,
                    "transaction": (f"{s['etichetta']} CHF {s['importo']:,.0f}" if s["importo"]
                                    else s["etichetta"]),
                    "score": round(p, 2),
                    "why it was paused": motivi_testo(s),
                    "why it came to the bank": motivo_n,
                    "status": e if e != "pending" else "to review",
                })
    if righe:
        st.dataframe(pd.DataFrame(righe), width="stretch", hide_index=True)
    elif not cfgs["attivo"]:
        st.warning("Sentinel is not active (screen 1).")
    else:
        st.success("No cases in the queue under the current configuration.")
        st.caption("Tip: on screen 1 tick \"holds a power of attorney\", or pick the "
                   "internal-abuse scenario.")

# ================================================================= appendix
else:
    st.title("Appendix · how the engine is calibrated")
    st.caption("The technical detail belongs here, not in the main flow. All data are "
               "synthetic: the real test is a pilot with a bank.")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Where to put the threshold")
        curva = cal["curva"]
        linea = (alt.Chart(curva).mark_line(color="#1f3a5f")
                 .encode(x=alt.X("soglia", title="intervention threshold"),
                         y=alt.Y("costo", title="expected cost per client per year (CHF)",
                                 scale=alt.Scale(type="log"))))
        regola = (alt.Chart(pd.DataFrame({"soglia": [soglia]}))
                  .mark_rule(color="#e4572e", strokeDash=[6, 4]).encode(x="soglia"))
        st.altair_chart(linea + regola, width="stretch")
        st.caption(f"Cost-optimal threshold: **{soglia:.2f}**. It balances two costs: "
                   "disturbing the contact with false alarms, and letting money go before "
                   "the first pause. The threshold is an economic decision, not a statistical one.")
    with c2:
        st.subheader("How well the score separates")
        diag = (alt.Chart(pd.DataFrame({"x": [0, 1], "y": [0, 1]}))
                .mark_line(color="#bbbbbb", strokeDash=[4, 4])
                .encode(x=alt.X("x", title="false positive rate"),
                        y=alt.Y("y", title="true positive rate")))
        curva_roc_ch = (alt.Chart(cal["roc"]).mark_line(color="#e4572e")
                        .encode(x=alt.X("fpr", title="false positive rate"),
                                y=alt.Y("tpr", title="true positive rate")))
        st.altair_chart(diag + curva_roc_ch, width="stretch")
        st.caption(f"AUC = **{cal['auc']:.3f}** on synthetic data (cash, box and transfers). "
                   "High, but it mostly reflects how clean the generator is.")

    st.subheader("Operational load · the bridge to the business model")
    k, prot = cal["carico"], cal["protetto"]
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Alerts per client per year", f"{k['alert_per_cliente_anno']:.1f}")
    m2.metric("Resolved by the contact", f"{k['quota_contatto']:.0%}")
    m3.metric("Escalated to the bank", f"{k['quota_banca']:.0%}")
    m4.metric("Cost to serve (CHF/year)", f"{k['cost_to_serve']:.2f}")
    st.caption(f"Simulated book of seniors. Fraud money protected: "
               f"{prot['importo_protetto']:.0%} (episodes caught: {prot['episodi_intercettati']:.0%}). "
               "Full results and sensitivity: results/simulation_report.md. "
               "The money protected is a benefit for the client and the family; the bank pays "
               "for trust, retention of senior clients and fewer complaints.")

    st.subheader("Scenario scores")
    dati = [{"scenario": n, "score": round(valuta(n)[1], 2),
             "paused": "yes" if valuta(n)[2].in_pausa else "no",
             "why": motivi_testo(operazione(n))} for n in SCENARI]
    st.dataframe(pd.DataFrame(dati), width="stretch", hide_index=True)
    st.caption("The bank-flagged scenario sits below the threshold: Sentinel still steps in, "
               "because it relies on the bank's antifraud system.")

    st.divider()
    st.subheader("The same engine across three populations")
    st.dataframe(confronto_profili(), width="stretch", hide_index=True)
    st.caption("Seniors are the first market; people under guardianship are the expansion; "
               "the prudent adult is the long-term vision (anyone who opts in).")
