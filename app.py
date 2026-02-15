import streamlit as st
import pandas as pd
import io
import os

# Configuración de página: Mantenemos wide pero los elementos internos se adaptarán
st.set_page_config(page_title="BCRA Entidades Financieras", layout="wide")

# --- FUNCIONES DE SOPORTE ---
def formato_ar(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")

@st.cache_data(ttl=60)
def cargar_datos():
    col_names = ["ID", "Banco", "Fecha", "Codigo", "Cuenta", "Debe", "Haber"]
    
    # LINKS ACTUALIZADOS (Asegúrate de que terminen en dl=1)
    urls_dropbox = [
        "https://www.dropbox.com/scl/fo/29qrx2lsucpd3b8lr9xbw/AA8ZyYq_US-a5fK2-t6ypyo?rlkey=bqnn5koqn7bk3g0hvi7tzldeg&st=ot3xmvxm&dl=1"
    ]
    
    lista_df = []
    for url in urls_dropbox:
        try:
            temp_df = pd.read_csv(url, sep='\t', names=col_names, encoding='latin-1', on_bad_lines='skip')
            lista_df.append(temp_df)
        except Exception as e:
            st.error(f"Error al descargar desde Dropbox: {e}")
    
    if not lista_df: 
        return pd.DataFrame(columns=col_names + ["Año", "Mes", "Nivel_0", "Nivel_1", "Saldo_Act"])
        
    df = pd.concat(lista_df, ignore_index=True)
    
    for col in ['Banco', 'Cuenta', 'Fecha', 'ID', 'Codigo']:
        df[col] = df[col].astype(str).str.replace('"', '').str.strip()

    df = df[df['Fecha'].str.len() == 6]
    df = df.drop_duplicates()
    
    df['Año'] = df['Fecha'].str[:4]
    df['Mes'] = df['Fecha'].str[4:]
    df['Debe'] = pd.to_numeric(df['Debe'], errors='coerce').fillna(0)
    df['Haber'] = pd.to_numeric(df['Haber'], errors='coerce').fillna(0)
    df['Saldo_Act'] = df['Debe'] - df['Haber']
    
    def clasificar_nivel_0(codigo):
        if not codigo: return "Otros"
        p = codigo[0]
        if p in ['1', '2']: return "Activo"
        elif p == '3': return "Pasivo"
        elif p in ['4', '5', '6']: return "Patrimonio Neto"
        elif p == '7': return "Partidas fuera del balance"
        else: return "Otros"

    def clasificar_nivel_1(codigo):
        if not codigo: return "Otro"
        if codigo.endswith("00000"): return "Totalizador_1"
        elif codigo.endswith("0000"): return "Totalizador_2"
        elif codigo.endswith("000"): return "Totalizador_3"
        else: return "Otro"

    df['Nivel_0'] = df['Codigo'].apply(clasificar_nivel_0)
    df['Nivel_1'] = df['Codigo'].apply(clasificar_nivel_1)
    return df

# --- CARGA DE DATOS ---
df = cargar_datos()

if df.empty:
    st.error("No hay datos disponibles.")
    st.stop()

# --- SIDEBAR: BOTÓN LIMPIAR ---
with st.sidebar:
    if st.button("🔄 Limpiar Todos los Filtros"):
        st.rerun()

# --- SECCIÓN DE FILTROS (OPTIMIZADA PARA MÓVIL) ---
st.header(f"📊 Detalle de Cuentas y Variaciones")

bancos_sel = st.multiselect("🏢 Seleccionar Entidades:", 
                            options=sorted(df["Banco"].unique()), 
                            default=[sorted(df["Banco"].unique())[0]])

# Filtros en 2 columnas para iPhone (en lugar de 4 amontonadas)
c_f1, c_f2 = st.columns(2)
with c_f1:
    año_sel = st.selectbox("Año:", sorted(df["Año"].unique(), reverse=True))
with c_f2:
    mes_sel = st.selectbox("Mes:", sorted(df[df["Año"] == año_sel]["Mes"].unique()))

c_f3, c_f4 = st.columns(2)
with c_f3:
    nivel0_sel = st.selectbox("Masa Patrimonial:", ["Todos"] + sorted(df["Nivel_0"].unique().tolist()))
with c_f4:
    nivel1_sel = st.selectbox("Nivel de Detalle:", ["Todos"] + sorted(df["Nivel_1"].unique().tolist()))

# Filtro de Cuentas (Full width para touch)
df_opc = df.copy()
if nivel0_sel != "Todos": df_opc = df_opc[df_opc["Nivel_0"] == nivel0_sel]
if nivel1_sel != "Todos": df_opc = df_opc[df_opc["Nivel_1"] == nivel1_sel]
lista_cuentas_fmt = sorted((df_opc["Codigo"] + " - " + df_opc["Cuenta"]).unique())
cuentas_sel_list = st.multiselect("🔢 Seleccionar Cuenta(s):", options=lista_cuentas_fmt)

# --- LÓGICA DE COMPARATIVO ---
try:
    mes_num, año_num = int(mes_sel), int(año_sel)
    if mes_num == 1: mes_ant, año_ant = "12", str(año_num - 1)
    else: mes_ant, año_ant = str(mes_num - 1).zfill(2), año_sel
except:
    mes_ant, año_ant = None, None

df_actual = df[(df["Año"] == año_sel) & (df["Mes"] == mes_sel) & (df["Banco"].isin(bancos_sel))].copy()
df_anterior = df[(df["Año"] == año_ant) & (df["Mes"] == mes_ant) & (df["Banco"].isin(bancos_sel))].copy()

df_comp = pd.merge(df_actual, df_anterior[['Banco', 'Codigo', 'Saldo_Act']], on=['Banco', 'Codigo'], how='left', suffixes=('', '_Ant')).fillna(0)
df_comp['Var. Absoluta'] = df_comp['Saldo_Act'] - df_comp['Saldo_Act_Ant']
df_comp['Var. %'] = df_comp.apply(lambda x: ((x['Saldo_Act'] - x['Saldo_Act_Ant']) / abs(x['Saldo_Act_Ant']) * 100) if x['Saldo_Act_Ant'] != 0 else 0, axis=1)

# --- TABLA RESUMEN ---
st.divider()
df_res = df_comp.copy()
if nivel0_sel != "Todos": df_res = df_res[df_res["Nivel_0"] == nivel0_sel]
if nivel1_sel != "Todos": df_res = df_res[df_res["Nivel_1"] == nivel1_sel]
if cuentas_sel_list:
    codigos_sel = [c.split(" - ")[0] for c in cuentas_sel_list]
    df_res = df_res[df_res["Codigo"].isin(codigos_sel)]

def color_variacion(val):
    if val < 0: return 'color: #ff4b4b;'
    elif val > 0: return 'color: #008000;'
    return 'color: black;'

st.subheader("📝 Detalle por Cuenta")
df_styled = (df_res[["Banco", "Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]]
             .style.format({"Saldo_Act": "{:,.2f}", "Var. Absoluta": "{:,.2f}", "Var. %": "{:.2f}%"})
             .map(color_variacion, subset=['Var. Absoluta', 'Var. %']))

st.dataframe(df_styled, use_container_width=True, hide_index=True)

# --- RATIOS DE SALUD BANCARIA (OPTIMIZADO MÓVIL) ---
st.divider()
st.subheader("🏥 Ratios de Salud Bancaria")
try:
    # (Lógica de cálculos que ya tenías...)
    disp_act = df_comp[df_comp['Codigo'] == "110000"]['Saldo_Act'].sum()
    depo_act = abs(df_comp[df_comp['Codigo'] == "210000"]['Saldo_Act'].sum())
    prest_act = df_comp[df_comp['Codigo'] == "120000"]['Saldo_Act'].sum()
    act_act = df_comp[df_comp['Codigo'] == "100000"]['Debe'].sum()
    pn_act = act_act - df_comp[df_comp['Codigo'] == "300000"]['Haber'].sum()

    disp_ant = df_comp[df_comp['Codigo'] == "110000"]['Saldo_Act_Ant'].sum()
    depo_ant = abs(df_comp[df_comp['Codigo'] == "210000"]['Saldo_Act_Ant'].sum())
    prest_ant = df_comp[df_comp['Codigo'] == "120000"]['Saldo_Act_Ant'].sum()
    act_ant = df_comp[df_comp['Codigo'] == "100000"]['Saldo_Act_Ant'].sum()
    pn_ant = act_ant - df_comp[df_comp['Codigo'] == "300000"]['Saldo_Act_Ant'].sum()

    r_liq_act, r_liq_ant = (disp_act/depo_act*100 if depo_act!=0 else 0), (disp_ant/depo_ant*100 if depo_ant!=0 else 0)
    r_solv_act, r_solv_ant = (pn_act/act_act*100 if act_act!=0 else 0), (pn_ant/act_ant*100 if act_ant!=0 else 0)
    
    # En iPhone, estas 3 columnas se verán una debajo de otra
    m1, m2, m3 = st.columns([1, 1, 1])
    m1.metric("Liquidez", f"{r_liq_act:.2f}%", f"{r_liq_act - r_liq_ant:.2f}%")
    m2.metric("Solvencia", f"{r_solv_act:.2f}%", f"{r_solv_act - r_solv_ant:.2f}%")
    m3.metric("Préstamos/Activo", f"{(prest_act/act_act*100):.2f}%")
except:
    st.info("Datos insuficientes para ratios.")





# --- MARKET SHARE REAL CON MULTI-SELECCIÓN, EVOLUTIVO Y TABLA DE CRECIMIENTO ---
st.divider()
st.header("🍰 Análisis de Participación de Mercado (Market Share)")
st.write("Analice la cuota de mercado y el volumen total del sistema para las cuentas elegidas.")

# --- BLOQUE DE FILTROS PARA EL SHARE ---
col_sh1, col_sh2, col_sh3 = st.columns([1, 1, 2])

with col_sh1:
    n0_share = st.selectbox("Filtrar por Masa Patrimonial:", ["Todos"] + sorted(df["Nivel_0"].unique().tolist()), key="n0_sh")
with col_sh2:
    n1_share = st.selectbox("Filtrar por Nivel de Detalle:", ["Todos"] + sorted(df["Nivel_1"].unique().tolist()), key="n1_sh")

df_opciones = df.copy()
if n0_share != "Todos":
    df_opciones = df_opciones[df_opciones["Nivel_0"] == n0_share]
if n1_share != "Todos":
    df_opciones = df_opciones[df_opciones["Nivel_1"] == n1_share]

opciones_cuentas = sorted((df_opciones["Codigo"] + " - " + df_opciones["Cuenta"]).unique())

with col_sh3:
    cuentas_share_multi = st.multiselect(
        "Seleccione Cuenta(s) para el análisis:", 
        options=opciones_cuentas,
        default=[opciones_cuentas[0]] if opciones_cuentas else [],
        key="ms_share_real"
    )

if cuentas_share_multi:
    codigos_sh = [c.split(" - ")[0] for c in cuentas_share_multi]
    
    # --- LÓGICA DE CÁLCULO ACTUAL ---
    df_universo_act = df[(df["Fecha"] == año_sel + mes_sel) & (df["Codigo"].isin(codigos_sh))]
    total_por_banco_sistema = df_universo_act.groupby("Banco")["Saldo_Act"].apply(lambda x: x.abs().sum()).reset_index()
    total_sistema_act = total_por_banco_sistema["Saldo_Act"].sum()
    
    if total_sistema_act > 0:
        st.subheader(f"📊 Situación al {mes_sel}/{año_sel}")
        
        df_share_sel_act = total_por_banco_sistema[total_por_banco_sistema["Banco"].isin(bancos_sel)].copy()
        df_share_sel_act['% Share'] = (df_share_sel_act['Saldo_Act'] / total_sistema_act) * 100
        
        c_g1, c_g2 = st.columns([2, 1])
        with c_g1:
            st.bar_chart(df_share_sel_act.set_index('Banco')['% Share'], horizontal=True)
        
        with c_g2:
            st.metric("Saldo Total Sistema", f"$ {formato_ar(total_sistema_act)}")
            suma_p = df_share_sel_act['% Share'].sum()
            st.metric("Share Combinado Bancos Sel.", f"{suma_p:.2f}%")

        # --- LÓGICA EVOLUTIVA ---
        df_solo_cuentas = df[df["Codigo"].isin(codigos_sh)]
        totales_sistema_hist = {}
        df_hist_share = []
        
        for fecha, grupo_fecha in df_solo_cuentas.groupby("Fecha"):
            total_mkt_periodo = grupo_fecha['Saldo_Act'].abs().sum()
            totales_sistema_hist[fecha] = total_mkt_periodo
            
            if total_mkt_periodo > 0:
                bancos_en_fecha = grupo_fecha[grupo_fecha["Banco"].isin(bancos_sel)].groupby("Banco")["Saldo_Act"].apply(lambda x: x.abs().sum()).reset_index()
                for _, fila in bancos_en_fecha.iterrows():
                    df_hist_share.append({
                        "Periodo": fecha,
                        "Banco": fila["Banco"],
                        "Market Share %": (fila["Saldo_Act"] / total_mkt_periodo) * 100
                    })
        
        if df_hist_share:
            st.subheader("📈 Tendencias del Mercado")
            
            # 1. Gráfico de Participación (%)
            df_evol_share = pd.DataFrame(df_hist_share).sort_values("Periodo")
            df_plot_share = df_evol_share.pivot(index="Periodo", columns="Banco", values="Market Share %")
            st.write("**Evolución de Participación Bancaria (%)**")
            st.line_chart(df_plot_share)
            
            # 2. Gráfico de Volumen del Sistema
            st.write("**Evolución del Volumen Total del Sistema ($)**")
            df_total_sys_series = pd.Series(totales_sistema_hist).sort_index()
            st.bar_chart(df_total_sys_series)

            # --- TABLA DE DATOS FINAL (Incluye Crecimiento MoM) ---
            with st.expander("📄 Ver Reporte Detallado y Crecimiento", expanded=False):
                # Calculamos el crecimiento MoM solo para la tabla
                df_growth = df_total_sys_series.pct_change() * 100
                
                df_tabla_final = df_plot_share.copy()
                df_tabla_final["Total Sistema ($)"] = df_total_sys_series
                df_tabla_final["Crecimiento MoM (%)"] = df_growth
                
                # Formateo de la tabla
                format_dict = {col: "{:.2f}%".format for col in df_plot_share.columns}
                format_dict["Total Sistema ($)"] = lambda x: f"$ {formato_ar(x)}"
                format_dict["Crecimiento MoM (%)"] = "{:.2f}%".format
                
                st.dataframe(
                    df_tabla_final.style.format(format_dict),
                    use_container_width=True
                )
                st.caption("MoM (%) = Month-over-Month: Tasa de crecimiento porcentual del volumen total respecto al mes anterior.")
    else:
        st.warning("No hay datos para la selección actual.")
else:
    st.info("Seleccione al menos una cuenta para iniciar el análisis.")



    # --- MÓDULO DE ALERTAS TEMPRANAS (RADAR GLOBAL DEL SISTEMA) ---
st.divider()
st.header("⚠️ Radar Global de Alertas (Todo el Sistema)")
st.caption("Análisis de riesgos sobre el universo completo de entidades basándose en saldos nominales.")

# 1. Definimos todos los bancos disponibles en el periodo actual
todos_los_bancos = df[df["Fecha"] == año_sel + mes_sel]["Banco"].unique()

alertas_globales = []

for b in todos_los_bancos:
    b_datos_act = df[(df["Banco"] == b) & (df["Año"] == año_sel) & (df["Mes"] == mes_sel)]
    b_datos_ant = df[(df["Banco"] == b) & (df["Año"] == año_ant) & (df["Mes"] == mes_ant)]
    
    if not b_datos_act.empty and not b_datos_ant.empty:
        # --- A. RIESGO DE FONDEO (Depósitos) ---
        depo_act = abs(b_datos_act[b_datos_act["Codigo"].str.startswith("21")]["Saldo_Act"].sum())
        depo_ant = abs(b_datos_ant[b_datos_ant["Codigo"].str.startswith("21")]["Saldo_Act"].sum())
        
        if depo_ant > 0:
            var_depo = ((depo_act / depo_ant) - 1) * 100
            if var_depo < -15:
                alertas_globales.append({
                    "Entidad": b, 
                    "Riesgo": "Fuga de Depósitos", 
                    "Indicador %": f"{var_depo:.1f}%",
                    "Numerador (Mes Act)": depo_act,
                    "Denominador (Mes Ant)": depo_ant,
                    "Detalle": "Variación MoM de Depósitos Totales"
                })

        # --- B. RIESGO DE LIQUIDEZ ---
        disp = b_datos_act[b_datos_act['Codigo'] == "110000"]['Saldo_Act'].sum()
        r_liq = (disp / depo_act * 100) if depo_act > 0 else 0
        if r_liq < 12:
            alertas_globales.append({
                "Entidad": b, 
                "Riesgo": "Liquidez Crítica", 
                "Indicador %": f"{r_liq:.1f}%",
                "Numerador (Disp)": disp,
                "Denominador (Depo)": depo_act,
                "Detalle": "Disponibilidades s/ Depósitos"
            })

        # --- C. RIESGO DE SOLVENCIA ---
        act_total = b_datos_act[b_datos_act['Codigo'] == "100000"]['Debe'].sum()
        pas_total = b_datos_act[b_datos_act['Codigo'] == "300000"]['Haber'].sum()
        pn = act_total - pas_total
        r_solv = (pn / act_total * 100) if act_total > 0 else 0
        if r_solv < 7:
            alertas_globales.append({
                "Entidad": b, 
                "Riesgo": "Solvencia", 
                "Indicador %": f"{r_solv:.1f}%",
                "Numerador (PN)": pn,
                "Denominador (Activo)": act_total,
                "Detalle": "Patrimonio Neto s/ Activo Total"
            })

# --- MOSTRAR RESULTADOS DEL RADAR ---
if alertas_globales:
    df_alertas = pd.DataFrame(alertas_globales)
    
    st.error(f"Se han detectado {len(alertas_globales)} alertas de riesgo en el sistema:")
    
    # Formateo de saldos para que la tabla sea legible
    columnas_saldos = [col for col in df_alertas.columns if "Numerador" in col or "Denominador" in col]
    
    st.dataframe(
        df_alertas.style.format({col: "{:,.2f}" for col in columnas_saldos}),
        use_container_width=True, 
        hide_index=True
    )
    st.caption("💡 Los montos están expresados en la moneda original de los archivos TXT.")
else:
    st.success("✅ Estabilidad detectada: No hay anomalías en el universo completo de entidades.")



# Preparar datos para el gráfico
matriz_data = []
for b in bancos_sel:
    sub = df_actual[df_actual["Banco"] == b]
    if not sub.empty:
        # Cálculos de ratios
        activo = sub[sub['Codigo'] == "100000"]['Debe'].sum()
        pasivo = sub[sub['Codigo'] == "300000"]['Haber'].sum()
        disp = sub[sub['Codigo'] == "110000"]['Saldo_Act'].sum()
        depo = abs(sub[sub['Codigo'] == "210000"]['Saldo_Act'].sum())
        
        liq = (disp / depo * 100) if depo > 0 else 0
        solv = ((activo - pasivo) / activo * 100) if activo > 0 else 0
        
        matriz_data.append({"Banco": b, "Liquidez (%)": liq, "Solvencia (%)": solv})

if matriz_data:
    df_matriz = pd.DataFrame(matriz_data)
    
    # Usamos st.scatter_chart para una visualización rápida y limpia
    st.scatter_chart(
        df_matriz,
        x="Liquidez (%)",
        y="Solvencia (%)",
        color="Banco",
        size=50
    )
    st.caption("Eje X: Liquidez (Disponibilidades/Depósitos) | Eje Y: Solvencia (PN/Activo)")