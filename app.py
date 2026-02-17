import streamlit as st
import pandas as pd
import io
import os

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
    df['Saldo_Act'] = df['Debe'] - df['Haber']
    df["Periodo"] = df["Mes"] + "-" + df["Año"]
    
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


    return df

# --- CARGA DE DATOS ---
df = cargar_datos()

if df.empty:
    st.error("No hay datos disponibles.")
    st.stop()


# --------------------- SECCION TABLA ENTIDADES FINANCIERAS ---------------------#
st.divider()
# --- SECCIÓN: FILTROS DE ENTIDADES Y CUENTAS ---
st.subheader("📊 **Entidades Financieras**")

with st.expander("🎯 **Configurar Filtros**", expanded=True):
    # 1. Selección de Entidades (Ancho completo)
    lista_bancos_master = sorted(df["Banco"].unique())
    bancos_sel = st.multiselect("🏢 Entidades Financieras:", 
                                options=lista_bancos_master, 
                                default=[lista_bancos_master[0]] if lista_bancos_master else [])

    # 2. Fila 1: Periodo Único y Masa Patrimonial
    c_f1, c_f2 = st.columns([2, 1])
    with c_f1:
        # Usamos la columna 'Periodo' que ya tienes creada (formato MM-AAAA)
        lista_periodos = df.sort_values(["Año", "Mes"], ascending=False)["Periodo"].unique().tolist()
        periodo_sel = st.selectbox("📅 Periodo (MM-AAAA):", options=lista_periodos)
    with c_f2:
        nivel0_sel = st.selectbox("Masa Patrimonial:", ["Todos"] + sorted(df["Nivel_0"].unique().tolist()))

    # 3. Fila 2: Rubro (Nivel 2) y Nivel de Detalle
    c_f3, c_f4 = st.columns(2)
    with c_f3:
        # Filtrado preventivo para el Rubro
        df_n2_opc = df[df["Nivel_0"] == nivel0_sel] if nivel0_sel != "Todos" else df
        opciones_n2 = sorted([str(x) for x in df_n2_opc["Nivel_2"].dropna().unique().tolist()])
        nivel2_sel = st.selectbox("Rubro (Nivel 2):", ["Todos"] + opciones_n2)
    with c_f4:
        nivel1_sel = st.selectbox("Nivel de Detalle:", ["Todos"] + sorted(df["Nivel_1"].unique().tolist()))

    # 4. Fila 3: Multiselect de Cuentas (Filtrado dinámico)
    df_opc = df[df["Periodo"] == periodo_sel].copy()
    if nivel0_sel != "Todos": df_opc = df_opc[df_opc["Nivel_0"] == nivel0_sel]
    if nivel2_sel != "Todos": df_opc = df_opc[df_opc["Nivel_2"] == nivel2_sel]
    if nivel1_sel != "Todos": df_opc = df_opc[df_opc["Nivel_1"] == nivel1_sel]
    
    lista_cuentas_master = sorted((df_opc["Codigo"] + " - " + df_opc["Cuenta"]).unique())
    cuentas_sel_list = st.multiselect("🔢 Seleccionar Cuentas:", options=lista_cuentas_master, placeholder="Busque cuenta(s)...")

# --- LÓGICA DE COMPARATIVO ---
try:
    # Extraemos mes y año del Periodo seleccionado (MM-AAAA)
    mes_sel, año_sel = periodo_sel.split("-")
    mes_num, año_num = int(mes_sel), int(año_sel)
    
    if mes_num == 1: 
        mes_ant, año_ant = "12", str(año_num - 1)
    else: 
        mes_ant, año_ant = str(mes_num - 1).zfill(2), str(año_num)
except:
    mes_ant, año_ant = None, None

# Filtrado para la comparativa
df_actual = df[(df["Año"] == año_sel) & (df["Mes"] == mes_sel) & (df["Banco"].isin(bancos_sel))].copy()
df_anterior = df[(df["Año"] == año_ant) & (df["Mes"] == mes_ant) & (df["Banco"].isin(bancos_sel))].copy()

# Merge y cálculos
df_comp = pd.merge(df_actual, df_anterior[['Banco', 'Codigo', 'Saldo_Act']], on=['Banco', 'Codigo'], how='left', suffixes=('', '_Ant')).fillna(0)
df_comp['Var. Absoluta'] = df_comp['Saldo_Act'] - df_comp['Saldo_Act_Ant']
df_comp['Var. %'] = df_comp.apply(lambda x: ((x['Saldo_Act'] - x['Saldo_Act_Ant']) / abs(x['Saldo_Act_Ant']) * 100) if x['Saldo_Act_Ant'] != 0 else 0, axis=1)

# --- PREPARACIÓN DE TABLA FINAL ---
st.divider()
df_res = df_comp.copy()

# Aplicamos filtros finales a la tabla
if nivel0_sel != "Todos": df_res = df_res[df_res["Nivel_0"] == nivel0_sel]
if nivel2_sel != "Todos": df_res = df_res[df_res["Nivel_2"] == nivel2_sel]
if nivel1_sel != "Todos": df_res = df_res[df_res["Nivel_1"] == nivel1_sel]
if cuentas_sel_list:
    codigos_sel = [c.split(" - ")[0] for c in cuentas_sel_list]
    df_res = df_res[df_res["Codigo"].isin(codigos_sel)]

# Función de colores mejorada
def color_variacion(val):
    if val < 0: return 'color: #ff4b4b; font-weight: bold;' # Rojo
    elif val > 0: return 'color: #008000; font-weight: bold;' # Verde
    return 'color: black;' # Negro para el 0

st.subheader("📝 Detalle por Cuenta")

# Mostramos la tabla con las columnas solicitadas
df_styled = (df_res[["Banco", "Nivel_0", "Nivel_2","Codigo", "Cuenta", "Saldo_Act", "Var. Absoluta", "Var. %"]]
             .style.format({
                 "Saldo_Act": "{:,.2f}", 
                 "Var. Absoluta": "{:,.2f}", 
                 "Var. %": "{:.2f}%"
             })
             .map(color_variacion, subset=['Var. Absoluta', 'Var. %']))

st.dataframe(df_styled, use_container_width=True, hide_index=True, height=500)

# --- TOTALIZADOR AL PIE DE LA TABLA ---

# Calculamos la suma de la columna filtrada
total_seleccionado = df_res["Saldo_Act"].sum()
total_var_abs = df_res["Var. Absoluta"].sum()

# Creamos tres columnas para mostrar los totales de forma estética
st.markdown("---")
c_t1, c_t2, c_t3 = st.columns([2, 1, 1])

with c_t1:
    st.metric(label="💰 Total Saldo Actual", value=f"$ {formato_ar(total_seleccionado)}")

with c_t2:
    # Usamos delta para mostrar la variación absoluta con color automático
    st.metric(label="📈 Var. Absoluta Total", 
              value=f"$ {formato_ar(total_var_abs)}",
              delta=formato_ar(total_var_abs))

with c_t3:
    # Calculamos la variación porcentual del total
    saldo_ant_total = total_seleccionado - total_var_abs
    if saldo_ant_total != 0:
        var_pct_total = (total_var_abs / abs(saldo_ant_total)) * 100
    else:
        var_pct_total = 0
        
    st.metric(label="📊 Var. % Total", 
              value=f"{var_pct_total:.2f}%",
              delta=f"{var_pct_total:.2f}%")