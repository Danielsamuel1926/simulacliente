# calculation_engine.py

# Moduli necessari
import numpy as np 
import pandas as pd 

# --- COEFFICIENTI E COSTANTI (DA PERSONALIZZARE) ---
ONERI_SISTEMA_FISSO_RES = 100.00  # €/anno
ONERI_SISTEMA_VARIABILE_RES = 0.015 # €/kWh o Smc
ACCISA_LUCE_BASE = 0.022          # €/kWh
PREZZO_MATERIA_RIF_LUCE = 0.12   # €/kWh
PREZZO_MATERIA_RIF_GAS = 0.45    # €/Smc

# --- FUNZIONE 1: CALCOLO LUCE ---
def calculate_electricity_cost(client_type, consumo_annuo, tariff_type):
    """Calcola il costo annuale della fornitura ELETTRICA."""
    
    # 1. Materia Energia
    prezzo_materia_unitario = 0.165 if tariff_type == 'Fissa' else PREZZO_MATERIA_RIF_LUCE + 0.02
    costo_materia_energia = consumo_annuo * prezzo_materia_unitario

    # 2. Trasporto e Gestione Contatore
    costo_trasporto = 0.08 * consumo_annuo + 70.0  

    # 3. Oneri di Sistema
    costo_oneri = (ONERI_SISTEMA_FISSO_RES + (consumo_annuo * ONERI_SISTEMA_VARIABILE_RES)) 

    # 4. Imposte (Accise e IVA)
    costo_accise = consumo_annuo * ACCISA_LUCE_BASE
    sub_totale = costo_materia_energia + costo_trasporto + costo_oneri + costo_accise
    
    # Logica IVA (Residenziale vs Business)
    iva = 0.10 if client_type == 'Residenziale' else 0.22 
    costo_imposte = sub_totale * iva

    costo_totale = sub_totale + costo_imposte
    
    return {
        'costo_totale': costo_totale,
        'Materia Prima': costo_materia_energia,
        'Trasporto e Gestione': costo_trasporto,
        'Oneri di Sistema': costo_oneri,
        'Imposte e IVA': costo_imposte,
        'riferimento': costo_totale * 1.15
    }

# --- FUNZIONE 2: CALCOLO GAS ---
def calculate_gas_cost(client_type, consumo_annuo, tariff_type, location):
    """Calcola il costo annuale della fornitura GAS."""
    
    # 1. Materia Gas
    prezzo_materia_unitario = 0.60 if tariff_type == 'Fissa' else PREZZO_MATERIA_RIF_GAS + 0.05
    coefficiente_P = 1.05 if location in ['Nord Italia'] else 1.0 # Esempio di gestione Location
    consumo_annuo_corretto = consumo_annuo * coefficiente_P

    costo_materia_gas = consumo_annuo_corretto * prezzo_materia_unitario

    # 2. Trasporto e Distribuzione
    costo_trasporto = (0.2 * consumo_annuo) + 50.0 

    # 3. Oneri di Sistema
    costo_oneri = 45.0 + (consumo_annuo * 0.005) 

    # 4. Imposte (Accise e IVA)
    accisa_gas = 0.05 * consumo_annuo_corretto 
    
    sub_totale = costo_materia_gas + costo_trasporto + costo_oneri + accisa_gas
    
    # Logica IVA (Residenziale vs Business)
    iva = 0.10 if client_type == 'Residenziale' else 0.22 
    costo_imposte = sub_totale * iva

    costo_totale = sub_totale + costo_imposte

    return {
        'costo_totale': costo_totale,
        'Materia Prima': costo_materia_gas,
        'Trasporto e Gestione': costo_trasporto,
        'Oneri di Sistema': costo_oneri,
        'Imposte e IVA': costo_imposte,
        'riferimento': costo_totale * 1.10
    }

# --- FUNZIONE MASTER (Chiamata da app.py) ---
def calculate_energy_cost(client_type, service, consumo_annuo, tariff_type, location):
    """
    Funzione principale che instrada la richiesta al calcolo corretto 
    e formattare l'output per l'interfaccia Streamlit.
    """
    # Pulizia stringhe
    # Esempio: "🏡 Residenziale" diventa "Residenziale"
    tipo_cliente = client_type.split(' ')[1] 
    tipo_servizio = service.split(' ')[1]
    
    if tipo_servizio == 'Luce':
        raw_results = calculate_electricity_cost(tipo_cliente, consumo_annuo, tariff_type)
        
    elif tipo_servizio == 'Gas':
        raw_results = calculate_gas_cost(tipo_cliente, consumo_annuo, tariff_type, location)
        
    else:
        raise ValueError(f"Servizio non supportato: {tipo_servizio}")

    # Formatta l'output finale
    costo_totale_annuo = raw_results['costo_totale']
    risparmio_vs_riferimento = raw_results['riferimento'] - costo_totale_annuo

    # Restituisce l'output richiesto da app.py
    return {
        'costo_totale_annuo': costo_totale_annuo,
        'breakdown': {
            'Materia Prima': raw_results['Materia Prima'],
            'Trasporto e Gestione': raw_results['Trasporto e Gestione'],
            'Oneri di Sistema': raw_results['Oneri di Sistema'],
            'Imposte e IVA': raw_results['Imposte e IVA']
        },
        'risparmio_vs_riferimento': risparmio_vs_riferimento
    }