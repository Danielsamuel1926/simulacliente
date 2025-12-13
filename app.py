import streamlit as st
import pandas as pd
from streamlit_option_menu import option_menu
import plotly.express as px

# ==============================
# CONFIGURAZIONE PAGINA
# ==============================
st.set_page_config(
    page_title="Simulatore Energia Daniele Lettera",
    layout="wide",
    initial_sidebar_state="collapsed" # La sidebar è inutile, la nascondiamo
)

# ==============================
# INIZIALIZZAZIONE DELLO STATO
# ==============================
# Stato per mostrare il form di input
if 'app_started' not in st.session_state:
    st.session_state.app_started = False
# Stato per mostrare i risultati
if 'calc_hidden' not in st.session_state:
    st.session_state.calc_hidden = False
# Pulizia campi
if 'cliente_main' not in st.session_state:
    st.session_state.cliente_main = "" 

# Funzione per passare da input a risultati
def start_calculation():
    """Funzione callback per avviare il calcolo."""
    st.session_state.calc_hidden = True

# ==============================
# STILE GENERALE (CSS)
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

/* Nasconde completamente la sidebar (non necessaria in questo layout) */
section[data-testid="stSidebar"] {
    visibility: hidden;
}

/* ---------------------------------- */
/* STILE BOTTONE (Azzurro) */
/* ---------------------------------- */

div.stButton > button {
    background-color: #00BFFF; /* Azzurro luminoso (Colore primario) */
    color: white !important; /* Testo bianco */
    font-weight: bold;
    border: none;
    border-radius: 8px;
    padding: 10px 20px;
    transition: background-color 0.2s; 
}

div.stButton > button:active {
    background-color: #3e4451 !important; 
    color: #00BFFF !important; 
}

div.stButton > button:hover {
    background-color: #009ACD; 
    color: white !important;
}

/* Stili per il contenitore del form di input */
.form-container {
    background-color: #1c1f26; 
    padding: 25px;
    border-radius: 10px;
    border: 1px solid #3e4451;
    margin-bottom: 30px;
}

/* Stile per i sottotitoli interni al form */
.form-container h3 {
    color: #00BFFF;
    border-bottom: 2px solid #3e4451;
    padding-bottom: 5px;
}

/* Stili per le metriche (rimanenti come prima) */
[data-testid="stMetric"] {
    background-color: #2c3038; 
    padding: 15px;
    border-radius: 10px;
    border-left: 5px solid #00BFFF; 
    box-shadow: 0 4px 8px rgba(0,0,0,0.2); 
}
/* ... (altri stili come prima) ... */
</style>
""", unsafe_allow_html=True)


# ==============================
# COSTANTI & FUNZIONI (IDEM)
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

def create_price_chart(prices, avg_price, mesi_idx, titolo, nome_indice):
    # ... (Funzione di creazione grafico identica) ...
    df_prices = pd.DataFrame({
        'Mese': MESI,
        nome_indice: prices[1:] 
    })
    
    df_avg = pd.DataFrame({
        'Mese': [MESI[m - 1] for m in mesi_idx],
        'Prezzo Medio Contratto': [avg_price] * len(mesi_idx)
    })

    fig = px.line(
        df_prices, 
        x='Mese', 
        y=nome_indice, 
        title=titolo,
        markers=True,
        color_discrete_sequence=['#00BFFF']
    )
    
    fig.add_trace(
        px.line(
            df_avg, 
            x='Mese', 
            y='Prezzo Medio Contratto', 
            line_dash='dash', 
            color_discrete_sequence=['#FFD700']
        ).data[0]
    )
    
    fig.data[0].name = nome_indice
    fig.data[1].name = 'Media Periodo Scelto'

    fig.update_layout(
        showlegend=True, 
        margin=dict(t=30, b=0, l=0, r=0), 
        legend_title_text=''
    )
    
    for i in mesi_idx:
        fig.add_vrect(
            x0=MESI[i-1], x1=MESI[i-1],
            fillcolor="#00BFFF", opacity=0.1, line_width=0
        )

    return fig

# ==============================
# HEADER
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
# CORPO PRINCIPALE (LOGICA DI VISUALIZZAZIONE)
# ==============================

if not st.session_state.app_started:
    # --- FASE 1: Pulsante "Inizia Simulazione" ---
    
    st.markdown("## Benvenuto nel Simulatore")
    st.info("Clicca il pulsante qui sotto per inserire i dati e avviare la simulazione.")

    col_c1, col_c2, col_c3 = st.columns([1, 1, 1])
    with col_c2:
        if st.button("▶️ Inizia Simulazione", key="start_app_button", use_container_width=True):
            st.session_state.app_started = True
            st.rerun() # Forza il refresh per mostrare il form
            
elif not st.session_state.calc_hidden:
    # --- FASE 2: Form di Input Dati ---
    st.markdown("## 1. 🛠️ Configurazione Dati")
    st.markdown("---")
    
    # Inizializza un contenitore per il form con lo stile scuro
    with st.container(border=False):
        st.markdown('<div class="form-container">', unsafe_allow_html=True)

        col_t1, col_t2 = st.columns([1, 3])
        with col_t1:
             tipo = option_menu(
                menu_title=None,
                options=["Luce", "Gas"],
                icons=["bolt", "fire"],
                default_index=0,
                orientation="horizontal",
                styles={
                    "container": {"padding": "5!important", "background-color": "#1c1f26", "border-radius": "5px"},
                    "nav-link": {"font-size": "14px", "color": "#f0f2f6", "padding": "5px"},
                    "nav-link-selected": {"background-color": "#00BFFF", "color": "white"},
                }
            )
        
        with col_t2:
            offerta = "F&F" 
            st.markdown(f"""
            <div style="background-color: #3e4451; padding: 5px; border-radius: 5px; text-align: center; margin-top: 10px; margin-left: 10px;">
                <span style="font-weight: bold; color: #00BFFF;">Offerta Fissa Selezionata: {offerta}</span>
            </div>
            """, unsafe_allow_html=True)


        # --- DATI BASE ---
        st.markdown("### Dati Cliente e Periodo")
        col_c1, col_c2, col_c3, col_c4 = st.columns(4)
        
        with col_c1:
            cliente = st.text_input("Nome Cliente", key="cliente_main", value=st.session_state.cliente_main)
        with col_c2:
            periodo = st.selectbox("Periodo Bolletta", ["Mensile","Bimestrale"], key="periodo_main")
        with col_c3:
            mese1 = st.selectbox("Mese 1", MESI, key="mese1_main")
        with col_c4:
            mese2 = st.selectbox("Mese 2", MESI, key="mese2_main") if periodo=="Bimestrale" else None

        st.markdown("---")
        
        # --- DATI DI CONSUMO ---
        st.markdown("### Dati di Consumo")
        col_d1, col_d2, col_d3 = st.columns(3)
        
        if tipo == "Luce":
            with col_d1:
                kwh = st.number_input("Consumo Luce (kWh)", min_value=0.0, value=300.0, key="kwh_main")
            with col_d2:
                kw = st.selectbox("Potenza impegnata (kW)", [1,1.5,2,2.5,3,4.5,5,5.5,6], key="kw_main")
            smc = 0
            smc_annuo = 0
        else:
            with col_d1:
                smc = st.number_input("Consumo Gas (m³)", min_value=0.0, value=150.0, key="smc_main")
            with col_d2:
                smc_annuo = st.number_input("Consumo annuo Gas (m³)", min_value=0.0, value=1800.0, key="smc_annuo_main")
            kwh = 0
            kw = 3 
        
        st.markdown("---")
        
        # --- DATI CONFRONTO ---
        st.markdown("### Dati Fattura Attuale e Oneri Extra")
        col_f1, col_f2, col_f3 = st.columns(3)
        
        with col_f1:
            fatt_attuale = st.number_input("Importo Fattura Attuale (€)", min_value=0.0, value=250.0, key="fatt_attuale_main")
        with col_f2:
            bonus = st.number_input("Bonus Sociale (€)", min_value=0.0, value=0.0, key="bonus_main")
            ricalcoli = st.number_input("Ricalcoli (€)", min_value=0.0, value=0.0, key="ricalcoli_main")
        with col_f3:
            altre = st.number_input("Altre Partite (€)", min_value=0.0, value=0.0, key="altre_main")
            canone_tv = st.number_input("Canone TV (€) (Solo Luce)", min_value=0.0, value=0.0, key="canone_tv_main")
        
        if tipo == "Luce":
            st.caption("ℹ️ **NOTA:** Inserisci qui l'importo del Canone Rai TV presente nella fattura del cliente se applicabile in questo periodo di calcolo.")
        elif canone_tv > 0:
            st.warning("⚠️ Il Canone TV non è applicabile alle bollette Gas. Controlla il valore.")
            
        st.markdown('</div>', unsafe_allow_html=True) # Chiusura form-container

    st.markdown("---")
    
    # Pulsante per avviare il CALCOLO e passare al DASHBOARD
    col_b1, col_b2, col_b3 = st.columns([1, 2, 1])
    with col_b2:
        st.button("🚀 Avvia Calcolo & Visualizza Risultati", key="calculate_button", use_container_width=True, on_click=start_calculation)

else:
    # --- FASE 3: Dashboard dei Risultati ---
    
    # Recupera i dati dal session_state per il calcolo
    tipo = st.session_state.tipo_main
    offerta = "F&F" # Fissa
    cliente = st.session_state.cliente_main
    periodo = st.session_state.periodo_main
    mese1 = st.session_state.mese1_main
    mese2 = st.session_state.get('mese2_main')
    kwh = st.session_state.get('kwh_main', 0.0)
    kw = st.session_state.get('kw_main', 3)
    smc = st.session_state.get('smc_main', 0.0)
    smc_annuo = st.session_state.get('smc_annuo_main', 0.0)
    fatt_attuale = st.session_state.fatt_attuale_main
    bonus = st.session_state.bonus_main
    ricalcoli = st.session_state.ricalcoli_main
    altre = st.session_state.altre_main
    canone_tv = st.session_state.canone_tv_main

    try:
        # 1. LOGICA DI CALCOLO (Identica a prima)
        mesi_list = [mese1] if periodo=="Mensile" else [mese1, mese2]
        mesi_idx = [MESI.index(m)+1 for m in mesi_list]
        num_mesi = len(mesi_idx)
        
        materia, sp_rete, quota_pot, oneri, comm_tot, accise_luce, iva_luce, accise_gas, iva_gas = 0,0,0,0,0,0,0,0,0
        pun_medio_base = 0.0
        psv_avg = 0.0
        prezzo_medio_calcolato = 0.0
        
        if tipo=="Luce":
            SPREAD, COMM = OFFERTE_LUCE[offerta] 
            pun_medio_base = sum([PUN[m] for m in mesi_idx])/num_mesi
            prezzo_medio = pun_medio_base + SPREAD + DISPACCIAMENTO + ASOS
            prezzo_medio_calcolato = prezzo_medio
            
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
            prezzo_medio_calcolato = psv_avg + SPREAD + QUOTA_CONSUMO_GAS
            
            materia = smc*(prezzo_medio_calcolato)
            sp_rete = QUOTA_VAR_DIST_GAS*smc + QUOTA_DIST_GAS * num_mesi
            oneri = ONERI_SISTEMA_GAS*num_mesi + (0.07*smc)+(0.12*smc)
            comm_tot = COMM*num_mesi
            
            accise_gas = accisa_annua_gas(smc_annuo)*smc
            aliquota = aliquota_iva_gas(smc_annuo)
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

        # 3. VISUALIZZAZIONE RISULTATI (Dashboard)
        st.header(f"2. Risultati Simulazione Offerta {offerta} ({num_mesi} Mesi)")
        st.markdown("---")

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
        
        # --- GRAFICI E DETTAGLI ---
        st.markdown("## 📈 Andamento Prezzi all'Ingrosso")
        col_price1, col_price2 = st.columns([2, 1])

        with col_price1:
            if tipo == "Luce":
                fig_prices = create_price_chart(PUN, pun_medio_base, mesi_idx, 
                                                "Andamento PUN (€/kWh) - Indice Prezzo all'Ingrosso", 
                                                "PUN (€/kWh)")
                st.plotly_chart(fig_prices, use_container_width=True)
            else:
                fig_prices = create_price_chart(PSV, psv_avg, mesi_idx, 
                                                "Andamento PSV (€/Smc) - Indice Prezzo all'Ingrosso", 
                                                "PSV (€/Smc)")
                st.plotly_chart(fig_prices, use_container_width=True)
                
        with col_price2:
            st.markdown("#### Riepilogo Prezzi Base")
            if tipo == "Luce":
                st.metric(label="PUN Medio del Periodo", value=f"{pun_medio_base:.4f} €/kWh")
                st.metric(label="Costo Materia Prima Finale", value=f"{prezzo_medio_calcolato:.4f} €/kWh")
            else:
                st.metric(label="PSV Medio del Periodo", value=f"{psv_avg:.4f} €/Smc")
                st.metric(label="Costo Materia Prima Finale", value=f"{prezzo_medio_calcolato:.4f} €/Smc")
                
        st.markdown("---")

        col_g1, col_g2 = st.columns([2, 3])
        
        # Confronto
        with col_g1:
            st.markdown("#### 📊 Confronto Attuale vs. Simulato")
            df_comparison = pd.DataFrame({
                'Scenario': ['Fattura Attuale', f'Offerta {offerta}'],
                'Costo (€)': [fatt_attuale, totale_simulato]
            })
            fig_bar = px.bar(df_comparison, x='Scenario', y='Costo (€)', color='Scenario',
                             color_discrete_map={'Fattura Attuale': 'lightcoral', f'Offerta {offerta}': '#00BFFF'},
                             text='Costo (€)')
            fig_bar.update_layout(xaxis_title="", yaxis_title="Costo (€)", showlegend=False, margin=dict(t=30, b=0, l=0, r=0))
            fig_bar.update_traces(texttemplate='€%{text:.0f}', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)

        # Breakdown
        with col_g2:
            st.markdown(f"#### 🍩 Composizione del Costo Simulato ({offerta})")
            voci_breakdown = [(k, v) for k, v in dati_simulati.items()]
            if canone_tv > 0: voci_breakdown.append(("Canone TV", canone_tv))
            if bonus > 0: voci_breakdown.append(("Bonus Sociale", bonus))
            if ricalcoli > 0: voci_breakdown.append(("Ricalcoli", ricalcoli))
            if altre > 0: voci_breakdown.append(("Altre Partite", altre))
            df_breakdown = pd.DataFrame(voci_breakdown, columns=['Voce di Costo', 'Importo'])
            df_breakdown['Importo'] = df_breakdown['Importo'].abs() 

            fig_pie = px.pie(df_breakdown, values='Importo', names='Voce di Costo', hole=0.4, 
                             color_discrete_sequence=px.colors.sequential.Teal)
            fig_pie.update_traces(textinfo='percent+label', marker=dict(line=dict(color='#000000', width=1)))
            fig_pie.update_layout(showlegend=False, uniformtext_minsize=12, uniformtext_mode='hide', margin=dict(t=30, b=0, l=0, r=0))
            st.plotly_chart(fig_pie, use_container_width=True)

        st.markdown("---")
        
        # Tabella Dettaglio
        with st.expander(f"🔍 Dettaglio Tecnico Bolletta Simulazione {offerta}"):
            righe_tabella = []
            for voce, importo in dati_simulati.items():
                 righe_tabella.append({"Voce": voce, "Importo (€)": format_currency(importo)})
            if canone_tv > 0: righe_tabella.append({"Voce": "Canone TV", "Importo (€)": format_currency(canone_tv)})
            if bonus > 0: righe_tabella.append({"Voce": "Bonus Sociale", "Importo (€)": format_currency(bonus)})
            if ricalcoli > 0: righe_tabella.append({"Voce": "Ricalcoli", "Importo (€)": format_currency(ricalcoli)})
            if altre > 0: righe_tabella.append({"Voce": "Altre Partite", "Importo (€)": format_currency(altre)})
            df_tabella = pd.DataFrame(righe_tabella)
            st.table(df_tabella.set_index("Voce")) 
            st.markdown(f"**Totale Bolletta Stimata: {format_currency(totale_simulato)}**")

    except Exception as e:
        st.error(f"⚠️ Errore nel calcolo. Controlla i dati inseriti: {e}")
        
    st.markdown("---")
    
    # Pulsante per tornare al form di input
    col_r1, col_r2, col_r3 = st.columns([1, 2, 1])
    with col_r2:
        if st.button("⬅️ Torna alla Configurazione", key="reset_button", use_container_width=True):
            st.session_state.calc_hidden = False
            st.rerun() # Forza il refresh per tornare alla fase 2 (Input)

