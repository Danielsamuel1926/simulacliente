import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px

# ==============================
# CONFIGURAZIONE PAGINA
# ==============================
st.set_page_config(
    page_title="Simulatore Energia Alto Stile",
    layout="wide",
    initial_sidebar_state="expanded"  # Sidebar aperta all'avvio
)

# ==============================
# INIZIALIZZAZIONE DELLO STATO (PULIZIA CAMPI)
# ==============================
# Reset di campi come "Nome Cliente" che Streamlit tende a memorizzare al ricaricamento
if 'cliente_sb' not in st.session_state or st.session_state.cliente_sb is None:
    st.session_state.cliente_sb = "" 
# Gli altri campi numerici si resettano grazie all'argomento 'value' nel widget

# ==============================
# STILE GENERALE (CSS) - Correzione Mobile
# ==============================
st.markdown("""
<style>
/* Corpo */
body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* HEADER - Mantenuto e spostato */
.header-container {
    background: linear-gradient(90deg, #0b0c12, #253073);
    padding: 20px;
    text-align: center;
    border-radius: 12px;
    margin-bottom: 20px;
}

/* ---------------------------------- */
/* CORREZIONE VISIBILITÀ MOBILE (IMPORTANTE) */
/* ---------------------------------- */
/* Aumenta l'indice Z per il pulsante menu su schermi piccoli */
button[title="Open sidebar"], button[title="Close sidebar"] {
    z-index: 10000 !important; 
    position: fixed; 
    top: 5px; 
    left: 5px; 
}


/* ---------------------------------- */
/* STILE SIDEBAR SCURO */
/* ---------------------------------- */
section[data-testid="stSidebar"] {
    background-color: #1c1f26; /* Sfondo Sidebar scuro */
    padding: 10px;
    color: white; 
}

/* Titoli e Intestazioni nella Sidebar */
.st-emotion-cache-1wv9vyr, 
.st-emotion-cache-163w365 h3, 
.st-emotion-cache-1wv9vyr h2,
.st-emotion-cache-1wv9vyr label,
.st-emotion-cache-1wv9vyr .st-emotion-cache-10trblm {
    color: #f0f2f6 !important; 
}

/* Sidebar separatore */
.st-emotion-cache-10r0w1k {
    border-top: 1px solid #444444; 
}

/* Sidebar - Rimuove la dicitura "About" di Streamlit */
footer {
    visibility: hidden;
}


/* ---------------------------------- */
/* STILE METRICHE SCURE */
/* ---------------------------------- */
[data-testid="stMetric"] {
    background-color: #2c3038; /* Sfondo scuro per i container */
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #00BFFF; /* Linea colore brand */
    box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
}

/* Testo principale del valore */
.stMetric>div:nth-child(2)>div:nth-child(1) {
    font-size: 26px; 
    font-weight: bold;
    color: #00BFFF !important; /* Valore principale azzurro per risalto */
}

/* Etichetta (label) sopra il valore */
.stMetric>label {
    color: #f0f2f6 !important;
}

/* Delta / Testo piccolo sotto il valore */
.stMetric>div:nth-child(3)>div {
    color: #cccccc !important;
}


/* ---------------------------------- */
/* STILE TABELLE (st.table) E DATAFRAME (st.dataframe) SCURE */
/* ---------------------------------- */
.stTable, .stDataFrame {
    color: #f0f2f6; 
}

/* Intestazione della tabella (Header) */
.stTable tr:first-child th, .stDataFrame table th {
    background-color: #2c3038 !important; 
    color: #00BFFF !important; 
    font-weight: bold;
}

/* Righe della tabella (Dati) */
.stTable tr:not(:first-child) td, .stDataFrame table tr td {
    background-color: #3e4451 !important; 
    border-bottom: 1px solid #2c3038;
}

</style>
""", unsafe_allow_html=True)


# ==============================
# COSTANTI & FUNZIONI (Tutte le tue costanti)
# ==============================
QUOTA_FISSA_LUCE = 22.80 / 12
QUOTA_POTENZA = 2.10
DISPACCIAMENTO = 0.020
ONERI_SISTEMA = 1.90
ASOS = 0.03

PUN = [0, 0.14303, 0.15036, 0.12055, 0.09985, 0.09358, 0.11178,
       0.11313, 0.10879, 0.10908, 0.11104, 0.11709, 0.10800]

OFFERTE_LUCE = {"Fast":(0.010,10),"F&F":(0.008,8.5),"Sind":(0.005,7),"Smart":(0.010,12.5)}

PSV = [0,0.388,0.402,0.403,0.418,0.422,0.415,0.410,0.400,0.388,0.345,0.350,0.360]
OFFERTE_GAS = {"Fast":(0.10,10),"F&F":(0.08,8.5),"Sind":(0.05,7),"Smart":(0.10,12.5)}
QUOTA_FISSA_GAS = 15/12
QUOTA_CONSUMO_GAS = 0.025
QUOTA_COMM_GAS = 31 * 0.005452
QUOTA_DIST_GAS = 31 * 0.140658
QUOTA_VAR_DIST_GAS = 0.171530
ONERI_SISTEMA_GAS = 1.50

MESI = ["GENNAIO","FEBBRAIO","MARZO","APRILE","MAGGIO","GIUGNO",
        "LUGLIO","AGOSTO","SETTEMBRE","OTTOBRE","NOVEMBRE","DICEMBRE"]

def accisa_annua_gas(smc_annuo, regione="Centro-Nord"):
    if smc_annuo <= 120: return 0.044
    elif smc_annuo <= 480: return 0.175
    elif smc_annuo <= 1560: return 0.170 if regione=="Centro-Nord" else 0.120
    else: return 0.186 if regione=="Centro-Nord" else 0.150

def aliquota_iva_gas(smc_annuo):
    return 0.10 if smc_annuo <= 480 else 0.22

def format_currency(value):
    return f"€ {value:,.2f}".replace(',', '_').replace('.', ',').replace('_', '.')

# ==============================
# HEADER - Spostato nel Corpo Principale
# ==============================
st.markdown("""
<div class="header-container">
    <span style="font-size:30px; font-weight:bold; color:#fff; display:block;">
        Simulatore Luce & Gas 💡🔥
    </span>
    <span style="font-size:18px; font-weight:bold; color:#fff; display:block;">
        Daniele Lettera Consulenza
    </span>
</div>
""", unsafe_allow_html=True)


# ==============================
# SIDEBAR (Pannello di Controllo INPUT)
# ==============================

with st.sidebar:
    st.header("1. 🛠️ Configura la Simulazione")
    
    tipo = option_menu(
        menu_title=None,
        options=["Luce", "Gas"],
        icons=["bolt", "fire"],
        default_index=0,
        orientation="horizontal",
        styles={
            "container": {"padding": "5!important", "background-color": "#1c1f26"},
            "nav-link": {"font-size": "14px", "color": "#f0f2f6"},
            "nav-link-selected": {"background-color": "#00BFFF", "color": "white"},
        }
    )

    offerta = "F&F" 
    st.markdown(f"""
    <div style="background-color: #3e4451; padding: 5px; border-radius: 5px; text-align: center; margin-top: 10px;">
        <span style="font-weight: bold; color: #00BFFF;">Offerta Fissa: {offerta}</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    # DATI BASE
    st.subheader("Dati Cliente e Periodo")
    cliente = st.text_input("Nome Cliente", key="cliente_sb", value=st.session_state.cliente_sb)
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        periodo = st.selectbox("Periodo", ["Mensile","Bimestrale"], key="periodo_sb")
    with col_p2:
        mese1 = st.selectbox("Mese Inizio", MESI, key="mese1_sb")
    
    mese2 = st.selectbox("Mese Fine", MESI, key="mese2_sb") if periodo=="Bimestrale" else None
    
    st.markdown("---")
    
    # DATI DI CONSUMO
    st.subheader("Dati di Consumo")

    if tipo == "Luce":
        kwh = st.number_input("Consumo Luce (kWh)", min_value=0.0, value=300.0)
        kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6])
        smc = 0
        smc_annuo = 0
    else:
        smc = st.number_input("Consumo Gas (m³)", min_value=0.0, value=150.0)
        smc_annuo = st.number_input("Consumo annuo Gas (m³)", min_value=0.0, value=1800.0)
        kwh = 0
        kw = 3 
    
    st.markdown("---")
    
    # DATI CONFRONTO
    st.subheader("Dati Fattura Attuale")
    fatt_attuale = st.number_input("Importo Fattura Attuale (€)", min_value=0.0, value=250.0)
    
    col_b1, col_b2 = st.columns(2)
    with col_b1:
        bonus = st.number_input("Bonus Sociale (€)", min_value=0.0, value=0.0)
        ricalcoli = st.number_input("Ricalcoli (€)", min_value=0.0, value=0.0)
    with col_b2:
        altre = st.number_input("Altre Partite (€)", min_value=0.0, value=0.0)
        
        # Canone TV impostato sempre a 0.0 di default e lasciato all'input del cliente
        canone_tv = st.number_input("Canone TV (€) (Solo Luce)", min_value=0.0, value=0.0) 
        
    if tipo == "Luce":
        st.caption("ℹ️ **NOTA:** Inserisci qui l'importo del Canone Rai TV presente nella fattura del cliente se applicabile in questo periodo di calcolo.")
    elif canone_tv > 0:
        st.warning("⚠️ Il Canone TV non è applicabile alle bollette Gas. Controlla il valore.")

    st.markdown("---")
    
    st.button("🚀 Avvia Simulazione", key="calc_hidden")


# ==============================
# CORPO PRINCIPALE (RISULTATI DASHBOARD)
# ==============================

if st.session_state.get("calc_hidden"):
    
    # 1. LOGICA DI CALCOLO
    try:
        # 1. PREPARAZIONE DATI
        mesi_list = [mese1] if periodo=="Mensile" else [mese1, mese2]
        mesi_idx = [MESI.index(m)+1 for m in mesi_list]
        num_mesi = len(mesi_idx)
        
        materia, sp_rete, quota_pot, oneri, comm_tot, accise_iva, accise_luce, iva_luce, accise_gas, iva_gas = 0,0,0,0,0,0,0,0,0,0
        
        if tipo=="Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta] 
            prezzo_medio = sum([PUN[m] for m in mesi_idx])/num_mesi + SPREAD + DISPACCIAMENTO + ASOS
            materia = kwh * prezzo_medio
            sp_rete = kwh * 0.0445
            quota_pot = kw * QUOTA_POTENZA * num_mesi
            oneri = ONERI_SISTEMA * num_mesi
            comm_tot = COMM * num_mesi
            
            accise_luce = max(0, kwh-150*num_mesi)*0.0227
            base_imponibile_luce = materia + sp_rete + quota_pot + oneri + comm_tot + accise_luce
            iva_luce = base_imponibile_luce * 0.10 
            
            dati_simulati = {
                "Materia Energia": materia,
                "Spese rete & Trasporto": sp_rete,
                "Quota potenza": quota_pot,
                "Oneri di sistema": oneri,
                "Commercializ. & Quota Fissa": comm_tot,
                "Accise (Imposte)": accise_luce,
                "IVA (10%)": iva_luce
            }

        else: # Tipo Gas
            SPREAD, COMM = OFFERTE_GAS[offerta] 
            psv_avg = sum([PSV[m] for m in mesi_idx])/num_mesi
            materia = smc*(psv_avg+SPREAD+QUOTA_CONSUMO_GAS)
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS * num_mesi
            oneri = ONERI_SISTEMA_GAS*num_mesi + (0.07*smc)+(0.12*smc)
            comm_tot = COMM*num_mesi
            
            accise_gas = accisa_annua_gas(smc_annuo)*smc
            aliquota = aliquota_iva_gas(smc_annuo)
            base_imponibile_gas = materia + sp_rete + oneri + comm_tot + accise_gas
            base_imponibile_gas_tot = materia + sp_rete + oneri + comm_tot + accise_gas
            iva_gas = base_imponibile_gas_tot * aliquota
            
            dati_simulati = {
                "Materia Gas / PSV": materia,
                "Spese rete (Distribuz.)": sp_rete,
                "Oneri di sistema": oneri,
                "Commercializ. & Quota Fissa": comm_tot,
                "Accise (Imposte)": accise_gas,
                f"IVA ({aliquota*100:.0f}%)": iva_gas
            }

        # 2. CALCOLO TOTALE
        totale_imposte_simulato = sum([v for k, v in dati_simulati.items() if "Imposte" in k or "IVA" in k])
        costo_base_simulato = sum(dati_simulati.values()) - totale_imposte_simulato 
        
        totale_extra = bonus + ricalcoli + altre + canone_tv
        totale_simulato = sum(dati_simulati.values()) + totale_extra

        # 3. VISUALIZZAZIONE RISULTATI
        st.subheader(f"Risultati Simulazione Offerta {offerta} ({num_mesi} Mesi)")
        st.markdown("---")

        # --- SEZIONE METRICHE CHIAVE (ALTO STILE) ---
        
        col_m1, col_m2, col_m3 = st.columns(3)
        
        risparmio_reale = fatt_attuale - totale_simulato
        
        col_m1.metric(
            label="💰 RISPARMIO POTENZIALE",
            value=format_currency(risparmio_reale),
            delta=f"vs. {format_currency(fatt_attuale)} Attuali",
            delta_color="inverse" if risparmio_reale < 0 else "normal"
        )
        
        col_m2.metric(
            label="Costo Simulato Totale",
            value=format_currency(totale_simulato),
            delta=f"Base Imponibile: {format_currency(costo_base_simulato)}",
            delta_color="off"
        )
        
        col_m3.metric(
            label="Costo Fattura Attuale",
            value=format_currency(fatt_attuale),
            delta=f"Cliente: {cliente if cliente else 'Non Specificato'}",
            delta_color="off"
        )

        st.markdown("---")

        # --- CONFRONTO GRAFICO (Barre) ---
        col_g1, col_g2 = st.columns([2, 3])
        
        with col_g1:
            st.markdown("#### 📊 Confronto Attuale vs. Simulato")
            df_comparison = pd.DataFrame({
                'Scenario': ['Fattura Attuale', f'Offerta {offerta}'],
                'Costo (€)': [fatt_attuale, totale_simulato]
            })
            
            # Grafico a barre di confronto
            fig_bar = px.bar(
                df_comparison, 
                x='Scenario', 
                y='Costo (€)',
                color='Scenario',
                color_discrete_map={
                    'Fattura Attuale': 'lightcoral', 
                    f'Offerta {offerta}': '#00BFFF' 
                },
                text='Costo (€)'
            )
            fig_bar.update_layout(xaxis_title="", yaxis_title="Costo (€)", showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
            fig_bar.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
            


        # --- BREAKDOWN DEI COSTI (GRAFICO A CIAMBELLA) ---
        with col_g2:
            st.markdown(f"#### 🍩 Composizione del Costo Simulato ({offerta})")
            
            voci_breakdown = [(k, v) for k, v in dati_simulati.items()]
            
            if canone_tv > 0: voci_breakdown.append(("Canone TV", canone_tv))
            if bonus > 0: voci_breakdown.append(("Bonus Sociale", bonus))
            if ricalcoli > 0: voci_breakdown.append(("Ricalcoli", ricalcoli))
            if altre > 0: voci_breakdown.append(("Altre Partite", altre))
            
            df_breakdown = pd.DataFrame(voci_breakdown, columns=['Voce di Costo', 'Importo'])
            df_breakdown['Importo'] = df_breakdown['Importo'].abs() 

            # Grafico a ciambella della composizione dei costi
            fig_pie = px.pie(
                df_breakdown, 
                values='Importo', 
                names='Voce di Costo', 
                hole=0.4, 
                color_discrete_sequence=px.colors.sequential.Teal
            )
            
            fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
            fig_pie.update_layout(showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=30, b=0, l=0, r=0))
            
            st.plotly_chart(fig_pie, use_container_width=True)
            

        st.markdown("---")

        # --- TABELLA DETTAGLIO (Nascosta) ---
        with st.expander(f"🔍 Dettaglio Tecnico Bolletta Simulazione {offerta}"):
            
            righe_tabella = []
            
            for voce, importo in dati_simulati.items():
                 righe_tabella.append({"Voce": voce, "Importo (€)": format_currency(importo)})
            
            if canone_tv > 0: righe_tabella.append({"Voce": "Canone TV", "Importo (€)": format_currency(canone_tv)})
            if bonus > 0: righe_tabella.append({"Voce": "Bonus Sociale", "Importo (€)": format_currency(bonus)})
            if ricalcoli > 0: righe_tabella.append({"Voce": "Ricalcoli", "Importo (€)": format_currency(ricalcoli)})
            if altre > 0: righe_tabella.append({"Voce": "Altre Partite", "Importo (€)": format_currency(altre)})
            
            df_tabella = pd.DataFrame(righe_tabella)
            
            # Visualizza la tabella senza l'indice numerico predefinito
            st.table(df_tabella.set_index("Voce")) 
            
            st.markdown(f"**Totale Bolletta Stimata: {format_currency(totale_simulato)}**")


    except Exception as e:
        st.error(f"⚠️ Errore nel calcolo. Controlla i dati inseriti o la logica interna: {e}")

else:
    # Messaggio iniziale
    st.info(f"Per iniziare la simulazione dell'offerta {offerta}, inserisci i parametri richiesti nel pannello di controllo laterale (Sidebar) e clicca 'Avvia Simulazione'.")