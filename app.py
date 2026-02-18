import streamlit as st
import pandas as pd
import io
import os
import plotly.express as px

# Configuración de página: Mantenemos wide pero los elementos internos se adaptarán
st.set_page_config(page_title="BCRA Entidades Financieras", layout="wide", page_icon="📊")

st.markdown("""
    <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    </style>
    """, unsafe_allow_html=True)


st.markdown("""
    <style>
        /* 1. Achica la letra de las celdas de la tabla */
        [data-testid="stDataFrame"] td {
            font-size: 7px !important;
        }
        /* 2. Achica la letra de los encabezados de la tabla */
        [data-testid="stDataFrame"] th {
            font-size: 7px !important;
        }
        /* 3. Opcional: Reduce el espacio entre filas para que sea más compacta */
        [data-testid="stDataFrame"] div[role="gridcell"] {
            padding: 2px 4px !important;
        }
    </style>
    """, unsafe_allow_html=True)


# --- FUNCIONES DE SOPORTE ---
def formato_ar(valor):
    return "{:,.2f}".format(valor).replace(",", "X").replace(".", ",").replace("X", ".")


# --- CARGA DE DATOS CORREGIDA ---
@st.cache_data(ttl=300) # Se actualiza cada 5 min
def cargar_datos():
    col_names = ["ID", "Banco", "Fecha", "Codigo", "Cuenta", "Debe", "Haber"]
    
    # LINKS ACTUALIZADOS (Asegúrate de que terminen en dl=1)
    urls_dropbox = [
        "https://www.dropbox.com/scl/fi/2thtj89g9cjmad8uscgc0/COMPLETO_012024.TXT?rlkey=dtw65whie2ziy8x53sqfei092&st=33i8rpi8&dl=1",
        "https://www.dropbox.com/scl/fi/oejvpyqqnqkm0fe03xo2u/COMPLETO_012025.TXT?rlkey=r9jr18xgglsghdtvo6hzuyncw&st=204zs88q&dl=1",
        "https://www.dropbox.com/scl/fi/jwu9e9o03azraun5btjr3/COMPLETO_022024.TXT?rlkey=rse0pblnigca10yrzx9fubt2b&st=xgw0ydvz&dl=1",
        "https://www.dropbox.com/scl/fi/phaay4tqo6k9cl7tmmv7w/COMPLETO_022025.TXT?rlkey=guf8wvclj2dfi11rg38ngs3jy&st=mt7t0twd&dl=1",
        "https://www.dropbox.com/scl/fi/aqmv3summh1qvu5eui630/COMPLETO_032024.TXT?rlkey=yly86q1ggh6ls6g5lttcqild9&st=r9qmx42i&dl=1",
        "https://www.dropbox.com/scl/fi/2yxg3e88ldidszijj6h14/COMPLETO_032025.TXT?rlkey=qxkdybcetym19wy98t1kfwm0e&st=sgdp8ql5&dl=1",
        "https://www.dropbox.com/scl/fi/xh626k6froeqt5nf2bmdm/COMPLETO_042024.TXT?rlkey=vq4pk6l7r1yltz81vrs86rdyg&st=e30dg962&dl=1",
        "https://www.dropbox.com/scl/fi/rktfcui7v763abd0uklqj/COMPLETO_042025.TXT?rlkey=lc1bsy5iu3lazqozegvs0jht5&st=6v0a0ndk&dl=1",
        "https://www.dropbox.com/scl/fi/jb6t1kf34ds2o7r37s5nt/COMPLETO_052024.TXT?rlkey=v521r07u5zo2xm51baki541s5&st=t4qzlv95&dl=1",
        "https://www.dropbox.com/scl/fi/dml1so4mlihqyemltrurw/COMPLETO_052025.TXT?rlkey=ut4kzind6ehq1kciaebish2bc&st=k6qgw4u0&dl=1",
        "https://www.dropbox.com/scl/fi/9assg4wabgga0pp1w7ev1/COMPLETO_062024.TXT?rlkey=dylywpzow96cjhfiseabhq6dl&st=09tdxg6y&dl=1",
        "https://www.dropbox.com/scl/fi/36af4oulc0u17ir0ff5bq/COMPLETO_062025.TXT?rlkey=8w5o6ccpasdyd1ei0e3wf5ivk&st=08i7mf4a&dl=1",
        "https://www.dropbox.com/scl/fi/untycpf8v73rdwjpuhmuc/COMPLETO_072024.TXT?rlkey=yfdtqhawmgfb3lreh7eyozn8v&st=wvzzqwty&dl=1",
        "https://www.dropbox.com/scl/fi/10o1tzwkw10g74ij3aj9k/COMPLETO_072025.TXT?rlkey=jjwxxzd7etj05hfafltsqdto4&st=5feidyil&dl=1",
        "https://www.dropbox.com/scl/fi/mrefw1v12sse84ubgrs4g/COMPLETO_082024.TXT?rlkey=gvkqqfjlgkszbuhfgj2doru8t&st=4sx2gcg8&dl=1",
        "https://www.dropbox.com/scl/fi/im8wu9yogq1k8do4uqnki/COMPLETO_082025.TXT?rlkey=063f4008n9zr9iw662zymbz51&st=bnupulsy&dl=1",
        "https://www.dropbox.com/scl/fi/ahdi9acnjazu6vc1lwq8s/COMPLETO_092024.TXT?rlkey=txzt1vf8tciwfjq8zh6opwl8c&st=7ug09y6m&dl=1",
        "https://www.dropbox.com/scl/fi/z9ekxx4aj9lnavfcs6x30/COMPLETO_092025.TXT?rlkey=3w2ouxmvpb2rzmkq3whq4j4yr&st=fbvgc228&dl=1",
        "https://www.dropbox.com/scl/fi/9s8m2jfkeisvdat98r69h/COMPLETO_102024.TXT?rlkey=n9tuh48jg7kjcyj6fy5ad0tpt&st=xl9049aw&dl=1",
        "https://www.dropbox.com/scl/fi/v6zuzso37koc1cjevjkyi/COMPLETO_102025.TXT?rlkey=9a565f1ichtuih2b35ysdekbo&st=ybzb24eb&dl=1",
        "https://www.dropbox.com/scl/fi/40jvychhch3j5twcjs6gt/COMPLETO_112024.TXT?rlkey=bu2yrb6m73a7lisj7jj5q2bw8&st=01wt51nr&dl=1",
        "https://www.dropbox.com/scl/fi/oahhtuelswvw502m7vwcx/COMPLETO_122024.TXT?rlkey=bafcwn7agyrrzva7wdu062ziz&st=de1nxxc2&dl=1"


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


    
    # 1. NORMALIZAR NOMBRES DE BANCOS (Tomar el último según la Fecha)
    # Ordenamos por fecha para que el más reciente quede al final
    df = df.sort_values("Fecha")
    
    # Creamos un mapeo: ID -> Último Nombre conocido
    mapeo_bancos = df.drop_duplicates('ID', keep='last').set_index('ID')['Banco'].to_dict()
    # Aplicamos el nombre más nuevo a todos los registros con ese ID
    df['Banco'] = df['ID'].map(mapeo_bancos)

    # 2. NORMALIZAR NOMBRES DE CUENTAS (Tomar el último según la Fecha)
    # Hacemos lo mismo para el Codigo de cuenta
    mapeo_cuentas = df.drop_duplicates('Codigo', keep='last').set_index('Codigo')['Cuenta'].to_dict()
    df['Cuenta'] = df['Codigo'].map(mapeo_cuentas)
    
    for col in ['Banco', 'Cuenta', 'Fecha', 'ID', 'Codigo']:
        df[col] = df[col].astype(str).str.replace('"', '').str.strip()

    df = df[df['Fecha'].str.len() == 6]
    df = df.drop_duplicates()
    
    df['Año'] = df['Fecha'].str[:4]
    df['Mes'] = df['Fecha'].str[4:]
    df['Debe'] = pd.to_numeric(df['Debe'], errors='coerce').fillna(0)
    df['Haber'] = pd.to_numeric(df['Haber'], errors='coerce').fillna(0)
    df['Saldo_Act'] = df['Debe'] + df['Haber']  df['Debe'] 
    df["Periodo_DT"] = pd.to_datetime(df["Fecha"], format='%Y%m', errors='coerce')
    # Periodo para mostrar (MM-AAAA)
    df["Periodo"] = df["Fecha"].str[4:] + "-" + df["Fecha"].str[:4]
    #df["Periodo"] = df["Mes"] + "-" + df["Año"]
    
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
        # 1. Casos específicos para Totalizador_1
        if codigo.endswith("00000") or codigo == "650000": return "Totalizador_1"
        # 2. Casos para Totalizador_2 (terminan en 0000 pero no son el 650000)
        elif codigo.endswith("0000"):return "Totalizador_2"
        # 3. Casos para Totalizador_3
        elif codigo.endswith("000"): return "Totalizador_3"
        # 4. Casos específicos para Totalizador_4 (Agrupados en una lista)
        elif codigo in ["511100", "511500", "515500", "521100", "521900", 
                        "525100", "525900", "515100", "521500"]:return "Totalizador_4"
        # 5. Todo lo demás
        else: return "Otro"

    def clasificar_vista(codigo):
        if not codigo: return "Otro"
        # El 650000 y los terminados en 00000 son MACRO
        if codigo == "650000" or codigo.endswith("00000"):
            return "Vista Macro"
        # Los terminados en 0000 (que no sean el anterior) son SUBTOTALES
        elif codigo.endswith("0000"):
            return "Vista Subtotales"
        else:
            return "Otro"  

    mapeo_n2 = {
        "11": "Efectivo y depósitos en bancos",
        "12": "Títulos públicos y privados",
        "13": "Préstamos",
        "14": "Otros créditos por intermediación financiera",
        "15": "Créditos por arrendamientos financieros",
        "16": "Participaciones en otras sociedades",
        "17": "Créditos diversos",
        "18": "Propiedad, planta y equipo",
        "19": "Bienes diversos",
        "21": "Activos intangibles",
        "22": "Filiales en el exterior",
        "23": "Partidas pendientes de imputación (deudores)",
        "31": "Depósitos",
        "32": "Otras obligaciones por intermediación financiera",
        "33": "Obligaciones diversas",
        "34": "Provisiones",
        "35": "Partidas pendientes de imputación (acreedores)",
        "36": "Obligaciones subordinadas",
        "41": "Capital social",
        "42": "Aportes no capitalizado",
        "43": "Ajustes al patrimonio",
        "44": "Reserva de utilidades",
        "45": "Resultados no asignados",
        "46": "Otros resultados integrales acumulados",
        "51": "Ingresos financieros",
        "52": "Egresos financieros",
        "53": "Cargos por incobrabilidad",
        "54": "Ingresos por servicios",
        "55": "Egresos por servicios",
        "56": "Gastos de administración",
        "57": "Utilidades diversas",
        "58": "Perdidas diversas",
        "59": "Resultado de filiales en el exterior",
        "61": "Impuesto a las ganancias",
        "62": "Resultado monetario",
        "65": "Otros resultados integrales (ORI)",
        "71": "PFB - Deudoras",
        "72": "PFB - Acreedoras"
    }


    
    
    
    df['Nivel_0'] = df['Codigo'].apply(clasificar_nivel_0)
    df['Nivel_1'] = df['Codigo'].apply(clasificar_nivel_1)
    df['Nivel_2'] = df['Codigo'].str[:2].map(mapeo_n2)
    df['Vista'] = df['Codigo'].apply(clasificar_vista)
    

    return df

# --- CARGA DE DATOS ---
df = cargar_datos()

if df.empty:
    st.error("No hay datos disponibles.")
    st.stop()


# --------------------- SECCION TABLA ENTIDADES FINANCIERAS ---------------------#
# --- SECCIÓN: FILTROS DE ENTIDADES Y CUENTAS ---
st.divider()
st.subheader("📊 **Entidades Financieras**")
with st.sidebar:
#with st.expander("🎯 **Configurar Filtros**", expanded=True):
    lista_bancos_master = sorted(df["Banco"].unique())
    bancos_sel = st.multiselect("🏢 Entidades Financieras:", options=lista_bancos_master, default=[lista_bancos_master[0]] if lista_bancos_master else [])

    
    lista_periodos = df.sort_values("Periodo_DT", ascending=False)["Periodo"].unique().tolist()
    periodo_sel = st.selectbox("📅 Periodo de Tabla (MM-AAAA):", options=lista_periodos)
    
    # CAMBIO: Multiselect para Masa Patrimonial
    opciones_n0 = sorted(df["Nivel_0"].unique().tolist())
    nivel0_sel = st.multiselect("Masa Patrimonial:", opciones_n0, default=opciones_n0)


    # CAMBIO: Lógica .isin() para evitar error
    df_n2_opc = df[df["Nivel_0"].isin(nivel0_sel)] if nivel0_sel else df
    opciones_n2 = sorted([str(x) for x in df_n2_opc["Nivel_2"].dropna().unique().tolist()])
    nivel2_sel = st.selectbox("Rubro (Nivel 2):", ["Todos"] + opciones_n2)
    
    nivel1_sel = st.selectbox("Nivel de Detalle:", ["Todos"] + sorted(df["Nivel_1"].unique().tolist()))

    # Filtro para el Multiselect de Cuentas
    df_opc = df[df["Periodo"] == periodo_sel].copy()

    # 2. Aplicamos los filtros de Masa, Rubro y Detalle para que la lista sea corta y útil
    if nivel0_sel:  df_opc = df_opc[df_opc["Nivel_0"].isin(nivel0_sel)]
    if nivel2_sel != "Todos": df_opc = df_opc[df_opc["Nivel_2"] == nivel2_sel]
    if nivel1_sel != "Todos":  df_opc = df_opc[df_opc["Nivel_1"] == nivel1_sel]

    # 3. Creamos la lista única de etiquetas "Código - Cuenta"
    lista_cuentas_master = sorted((df_opc["Codigo"] + " - " + df_opc["Cuenta"]).unique())
    # 4. Única instancia del multiselect
    cuentas_sel_list = st.multiselect(
        "🔢 Seleccionar Cuentas:", 
        options=lista_cuentas_master,
        help="Seleccione las cuentas que desea comparar en el gráfico de líneas al final de la página."
    )

# --- COMPARATIVO ---
try:
    mes_sel, año_sel = periodo_sel.split("-")
    mes_num, año_num = int(mes_sel), int(año_sel)
    if mes_num == 1: mes_ant, año_ant = "12", str(año_num - 1)
    else: mes_ant, año_ant = str(mes_num - 1).zfill(2), str(año_num)
except:
    mes_ant, año_ant = None, None

df_actual = df[(df["Año"] == año_sel) & (df["Mes"] == mes_sel) & (df["Banco"].isin(bancos_sel))].copy()
df_anterior = df[(df["Año"] == año_ant) & (df["Mes"] == mes_ant) & (df["Banco"].isin(bancos_sel))].copy()

df_comp = pd.merge(df_actual, df_anterior[['Banco', 'Codigo', 'Saldo_Act']], on=['Banco', 'Codigo'], how='left', suffixes=('', '_Ant')).fillna(0)
df_comp['Var. Absoluta'] = df_comp['Saldo_Act'] - df_comp['Saldo_Act_Ant']
df_comp['Var. %'] = df_comp.apply(lambda x: ((x['Saldo_Act'] - x['Saldo_Act_Ant']) / abs(x['Saldo_Act_Ant']) * 100) if x['Saldo_Act_Ant'] != 0 else 0, axis=1)

# --- SELECTOR DE VISTA ---
opcion_vista = st.radio("🧐 **Seleccione nivel de análisis:**", options=["Vista Macro", "Vista Subtotales", "Todo"], horizontal=True)

df_res = df_comp.copy()

# Filtrado por Vista (Lógica corregida)
if opcion_vista == "Vista Macro":
    df_res = df_res[df_res["Vista"] == "Vista Macro"]
elif opcion_vista == "Vista Subtotales":
    df_res = df_res[(df_res["Vista"] == "Vista Subtotales") | (df_res["Codigo"] == "650000")]

# Filtros adicionales
if nivel0_sel: df_res = df_res[df_res["Nivel_0"].isin(nivel0_sel)]
if nivel2_sel != "Todos": df_res = df_res[df_res["Nivel_2"] == nivel2_sel]
if nivel1_sel != "Todos": df_res = df_res[df_res["Nivel_1"] == nivel1_sel]
if cuentas_sel_list:
    codigos_sel = [c.split(" - ")[0] for c in cuentas_sel_list]
    df_res = df_res[df_res["Codigo"].isin(codigos_sel)]

# --- TABLA Y TOTALES ---
def color_variacion(val):
    if val < 0: return 'color: #ff4b4b; font-weight: bold;'
    elif val > 0: return 'color: #008000; font-weight: bold;'
    return 'color: black;'

st.subheader(f"📝 Balance contable ({opcion_vista}) de {bancos_sel}")
df_res=df_res.sort_values("Codigo", ascending=True)

# --- AJUSTE DE COLUMNAS DINÁMICAS PARA VISTA SLIM ---
# Columnas que SIEMPRE se muestran
cols_a_mostrar = ["Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]

# Columnas que se muestran SOLO si no hay un filtro específico (para evitar redundancia)
# --- AJUSTE DE COLUMNAS DINÁMICAS (LÓGICA PERSONALIZADA) ---

# 1. Definimos la base de columnas según la vista y cantidad de bancos
if len(bancos_sel) == 1:
    if opcion_vista == "Vista Macro":
        # Solo Cuenta y datos numéricos (Sin Código)
        cols_a_mostrar = ["Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]
    elif opcion_vista == "Vista Subtotales":
        # Se agrega el Código a la visión macro
        cols_a_mostrar = ["Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]
    else:
        # Para "Todo" mantenemos el estándar
        cols_a_mostrar = ["Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]
else:
    # Si hay más de un banco, siempre mostramos Banco y Código
    cols_a_mostrar = ["Banco", "Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]

# 2. Agregamos Nivel_0 y Nivel_2 solo si el usuario no los filtró (para evitar redundancia)
if nivel2_sel == "Todos" and opcion_vista == "Todo":
    cols_a_mostrar.insert(1, "Nivel_2")

if nivel0_sel == "Todos" and opcion_vista == "Todo":
    cols_a_mostrar.insert(1, "Nivel_0")

# --- RENDERIZADO DE TABLA ---

# Ordenamos antes de aplicar el estilo
df_res = df_res.sort_values("Codigo", ascending=True)

df_styled = (df_res[cols_a_mostrar]
             .style.format({
                 "Saldo_Act": "{:,.0f}", 
                 "Var. Absoluta": "{:,.0f}", 
                 "Var. %": "{:.2f}%"
             })
             .map(color_variacion, subset=['Var. Absoluta', 'Var. %']))

# Altura automática para evitar scroll interno
st.dataframe(df_styled, use_container_width=True, hide_index=True, height="auto")



# --- TABLA LADO DERECHO ---

st.markdown(f"##### 📊 Composición por Cuenta ({opcion_vista})")
    
   # Preparamos los datos para el gráfico
   # Usamos df_res que ya tiene aplicados los filtros de arriba
df_graf = df_res.copy()
    
# Creamos el gráfico de barras agrupadas/apiladas
fig = px.bar(
    df_graf, 
    x="Banco", 
    y="Saldo_Act", 
    color="Cuenta",  # Esto crea el apilamiento por cuenta
    title=None,
    labels={"Saldo_Act": "Saldo Actual ($)", "Banco": "Entidad"},
    text_auto='.2s', # Muestra el valor abreviado sobre las barras
    template="plotly_white"
)

# Ajustes estéticos para que se vea bien en media pantalla
fig.update_layout(
    margin=dict(l=0, r=0, t=20, b=0),
    height=450,
    showlegend=True,
    legend=dict(
    orientation="h",
    yanchor="bottom",
    y=-0.5,
    xanchor="center",
    x=0.5,
    font=dict(size=10)
    )
)

# Mostramos el gráfico en Streamlit
st.plotly_chart(fig, use_container_width=True)



#height=True

# st.markdown("---")
# total_s = df_res["Saldo_Act"].sum()
# total_v = df_res["Var. Absoluta"].sum()
# c_t1, c_t2, c_t3 = st.columns([2, 1, 1])
# with c_t1: st.metric("💰 Total Saldo Actual", f"$ {formato_ar(total_s)}")
# with c_t2: st.metric("📈 Var. Absoluta Total", f"$ {formato_ar(total_v)}", delta=formato_ar(total_v))
# with c_t3:
#     den = abs(total_s - total_v)
#     v_pct = (total_v / den * 100) if den != 0 else 0
#     st.metric("📊 Var. % Total", f"{v_pct:.2f}%", delta=f"{v_pct:.2f}%")



# --- PROCESAMIENTO DEL GRÁFICO EVOLUTIVO ---

st.markdown("---")
st.subheader("📅 Evolución Histórica")

# --- SELECTOR DE MODO DE GRÁFICO (El "Botón") ---
modo_grafico = st.radio(
    "Seleccione visualización:",
    options=["Sumar Cuentas (Consolidado)", "Detallar por Cuenta y Banco"],
    horizontal=True
)

# (Mantenemos la lógica del slicer de periodos igual)
lista_periodos_slicer = df.sort_values("Periodo_DT")["Periodo"].unique().tolist()
rango_slicer = st.select_slider("Rango de análisis:", options=lista_periodos_slicer, value=(lista_periodos_slicer[0], lista_periodos_slicer[-1]))
p_inicio, p_fin = rango_slicer

if bancos_sel and cuentas_sel_list:
    # ... (Filtrado de fechas y códigos igual que antes) ...
    codigos_comp = [c.split(" - ")[0] for c in cuentas_sel_list]
    fecha_inf = df[df["Periodo"] == p_inicio]["Periodo_DT"].min()
    fecha_sup = df[df["Periodo"] == p_fin]["Periodo_DT"].max()
    
    mask = (df["Banco"].isin(bancos_sel)) & (df["Codigo"].isin(codigos_comp)) & \
           (df["Periodo_DT"] >= fecha_inf) & (df["Periodo_DT"] <= fecha_sup)
    df_ev_final = df[mask].copy()

    if not df_ev_final.empty:
        # --- LÓGICA DINÁMICA SEGÚN EL BOTÓN SELECCIONADO ---
        if modo_grafico == "Sumar Cuentas (Consolidado)":
            # Agrupamos solo por Banco y Periodo (Suma cuentas)
            df_plot_ev = df_ev_final.groupby(["Periodo", "Periodo_DT", "Banco"])["Saldo_Act"].sum().reset_index()
            color_param = "Banco"
            titulo_graf = "Evolución Consolidada (Suma de Cuentas)"
        else:
            # Agrupamos por Banco, Cuenta y Periodo (Detalle total)
            df_ev_final["Etiqueta"] = df_ev_final["Banco"] + " - " + df_ev_final["Cuenta"]
            df_plot_ev = df_ev_final.groupby(["Periodo", "Periodo_DT", "Etiqueta"])["Saldo_Act"].sum().reset_index()
            color_param = "Etiqueta"
            titulo_graf = "Evolución Detallada por Banco y Cuenta"

        # Orden cronológico
        df_plot_ev = df_plot_ev.sort_values("Periodo_DT")

        # Crear Gráfico
        fig_ev = px.line(
            df_plot_ev, 
            x="Periodo", 
            y="Saldo_Act", 
            color=color_param,
            markers=True,
            template="plotly_white",
            title=titulo_graf,
            labels={"Saldo_Act": "Saldo ($)"}
        )
        
        st.plotly_chart(fig_ev, use_container_width=True)
    else:
        st.warning("No hay datos para los filtros seleccionados.")


# ----------------MARKET SHARE -------------------------------------------------
st.markdown("---")
st.subheader("📈 Participación de Mercado (Market Share)")

# --- 1. PREPARACIÓN DE DATOS DE MERCADO ---
# Usamos el DF original sin filtrar por banco para tener el 'Total Sistema'
if cuentas_sel_list and p_inicio and p_fin:
    codigos_ms = [c.split(" - ")[0] for c in cuentas_sel_list]
    fecha_inf_ms = df[df["Periodo"] == p_inicio]["Periodo_DT"].min()
    fecha_sup_ms = df[df["Periodo"] == p_fin]["Periodo_DT"].max()

    # Filtramos solo por Cuentas y Fechas (Incluye a todos los bancos del sistema)
    mask_sistema = (
        (df["Codigo"].isin(codigos_ms)) & 
        (df["Periodo_DT"] >= fecha_inf_ms) & 
        (df["Periodo_DT"] <= fecha_sup_ms)
    )
    df_sistema = df[mask_sistema].copy()

    if not df_sistema.empty:
        # Calculamos el Total del Sistema por cada Periodo
        total_sistema = df_sistema.groupby(["Periodo", "Periodo_DT"])["Saldo_Act"].sum().reset_index()
        total_sistema.rename(columns={"Saldo_Act": "Total_Sistema"}, inplace=True)

        # Filtramos los bancos seleccionados por el usuario
        df_bancos_ms = df_sistema[df_sistema["Banco"].isin(bancos_sel)].copy()
        
        # Sumamos las cuentas por Banco y Periodo
        df_bancos_sum = df_bancos_ms.groupby(["Periodo", "Periodo_DT", "Banco"])["Saldo_Act"].sum().reset_index()

        # Unimos los datos de los bancos con el total del sistema
        df_ms_final = pd.merge(df_bancos_sum, total_sistema, on=["Periodo", "Periodo_DT"])

        # Calculamos el % de participación
        df_ms_final["Market_Share"] = (df_ms_final["Saldo_Act"] / df_ms_final["Total_Sistema"]) * 100
        df_ms_final = df_ms_final.sort_values(["Periodo_DT", "Market_Share"], ascending=[True, False])

        # --- 2. GRÁFICO DE MARKET SHARE ---
        fig_ms = px.line(
            df_ms_final, 
            x="Periodo", 
            y="Market_Share", 
            color="Banco",
            markers=True,
            template="plotly_white",
            title="Evolución de Cuota de Mercado (%)",
            labels={"Market_Share": "Share"},
            line_shape="spline"
        )

        # Configuración del Hover (Cartelito)
        fig_ms.update_traces(
            # El orden en el recuadro respetará el orden del DataFrame
            hovertemplate="<b>%{fullData.name}</b>: %{y:.2f}%<extra></extra>"
        )

        # Configuración del recuadro unificado y ordenamiento
        fig_ms.update_layout(
            hovermode="x unified",
            yaxis_ticksuffix="%",
            # Mantenemos el periodo como encabezado
            xaxis=dict(hoverformat="%m-%Y"),
            # Este parámetro asegura que el hover mantenga el orden que definimos en el DF
            hoverlabel=dict(namelength=-1)
        )

        st.plotly_chart(fig_ms, use_container_width=True)

        with st.expander("Ver tabla de Market Share (%)"):
            # 1. Creamos la tabla pivot de los bancos (Market Share %)
            df_ms_pivot = df_ms_final.pivot(index="Periodo", columns="Banco", values="Market_Share")
            
            # 2. Obtenemos el Volumen del Sistema por periodo (un valor por mes)
            # Quitamos duplicados para tener una serie: Periodo -> Total_Sistema
            df_totales = df_ms_final[["Periodo", "Total_Sistema", "Periodo_DT"]].drop_duplicates().set_index("Periodo")
            
            # 3. Unimos el Volumen del Sistema a la tabla pivot
            df_ms_completa = df_ms_pivot.copy()
            df_ms_completa["Total Sistema"] = df_totales["Total_Sistema"]
            
            # 4. Aseguramos el orden cronológico antes de mostrar
            df_ms_completa = df_ms_completa.reindex(df_totales.sort_values("Periodo_DT").index)
            
            # 5. Aplicamos formatos diferenciados: % para bancos y número para el Total
            # Creamos un diccionario de formatos dinámico basado en las columnas
            formatos = {col: "{:.2f}%" for col in df_ms_pivot.columns}
            formatos["Total Sistema"] = "{:,.0f}" # Formato con separador de miles
            
            st.dataframe(
                df_ms_completa.style.format(formatos), 
                use_container_width=True
            )
    else:
        st.warning("No hay datos suficientes para calcular el Market Share.")
else:
    st.info("Seleccione bancos y cuentas arriba para calcular la participación de mercado.")