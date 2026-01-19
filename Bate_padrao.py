import pandas as pd 
from unidecode import unidecode
import streamlit as st
import pandas as pd
from io import BytesIO
import arquivo_bradesco
import Central_unimed
import CNU
import Sulamerica
import Amil
import OdontoPrev

def gerar_resumo_comparacoes(resumo_comparacoes_lista, resumo_totais):
    
    # Converter lista em DataFrame, garantindo colunas
    colunas_comparacoes = ["Comparação", "Iguais", "Diferentes", "Total"]
    df_comparacoes = pd.DataFrame(resumo_comparacoes_lista, columns=colunas_comparacoes)
    
    # Normalizar resumo_totais para concatenar
    df_totais = resumo_totais.rename(columns={"total_de_registros": "Total"})
    df_totais["Comparação"] = "Totais"
    df_totais["Iguais"] = 0
    df_totais["Diferentes"] = 0
    
    # Garantir mesmo tipo das colunas numéricas
    for col in ["Iguais", "Diferentes", "Total"]:
        df_comparacoes[col] = df_comparacoes[col].fillna(0).astype(int)
        df_totais[col] = df_totais[col].fillna(0).astype(int)
    
    # Concatenar de forma segura
    resumo_comparacoes = pd.concat([df_totais, df_comparacoes], axis=0, ignore_index=True)
    
    return resumo_comparacoes




def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:

    df_copy = df.copy()
    for col in df_copy.columns:
        # Pega os tipos únicos ignorando NaNs
        unique_types = set(df_copy[col].dropna().map(type))
        
        # Se tem mistura de str e int/float, ou só strings com espaços, converte para str
        if any(t in [str, int, float] for t in unique_types) and len(unique_types) > 1:
            df_copy[col] = df_copy[col].astype(str).str.strip()
        # Também converte floats para str para evitar problemas de encode/export
        elif float in unique_types:
            df_copy[col] = df_copy[col].astype(str).str.strip()
    
    return df_copy


def padrao( nome_op, dt_op, cpft_op, sexo_op, plano_op, parentesco_op, cpf,df_folha_1, df_operadora_1):
    #Função auxiliar
    def limpa_cpf(x):
        if pd.isna(x):
            return ""
        x = str(x).strip()
        x = ''.join(filter(str.isdigit, x))
        return x.zfill(11) if x else ""

    def sanitize_text(df, cols):
        for col in cols:
            if col in df.columns:
                df[col] = df[col].fillna('').astype(str).str.strip().str.lower().apply(unidecode)
        return df

    #Preparação das colunas de texto
    text_cols_folha = ['NOME_BENEF_folha', 'SEXO_folha', 'PLANO_folha', 'PARENTESCO_folha']
    df_folha_1 = sanitize_text(df_folha_1, text_cols_folha)
    df_operadora_1 = sanitize_text(df_operadora_1, [nome_op, sexo_op, plano_op, parentesco_op])

    #Criação da chave de merge baseada em CPF
    df_folha_1["chave_merge"] = df_folha_1["CPF_folha"].apply(limpa_cpf)
    df_operadora_1["chave_merge"] = df_operadora_1[cpf].apply(limpa_cpf)

    # Merge 
    df_analise = pd.merge(
        df_operadora_1,
        df_folha_1,
        on="chave_merge",
        how="outer",
        indicator=True)

    df_analise["_merge"] = df_analise["_merge"].astype(str).replace({
        "left_only": "presente na operadora",
        "both": "presente em ambas",
        "right_only": "presente na folha"})
    df_analise.rename(columns={"_merge": "está presente onde ?"}, inplace=True)

    #Normalização de nomes e datas
    df_analise['NOME_BENEF_folha'] = df_analise['NOME_BENEF_folha'].fillna('').astype(str).str.strip().str.lower().apply(unidecode)
    df_analise[nome_op] = df_analise[nome_op].fillna('').astype(str).str.strip().str.lower().apply(unidecode)

    df_analise['DATA DE NASCIMENTO_folha'] = pd.to_datetime(df_analise['DATA DE NASCIMENTO_folha'], errors='coerce')
    df_analise["DATA DE NASCIMENTO_folha"] = df_analise["DATA DE NASCIMENTO_folha"].dt.strftime('%d/%m/%Y')

    df_analise[cpft_op] = df_analise[cpft_op].fillna('').astype(str).str.zfill(11)
    df_analise['CPF TITULAR_folha'] = df_analise['CPF TITULAR_folha'].fillna('').astype(str).str.zfill(11)

    #Colunas para conferência 
    colunas_para_conferir = {
        nome_op: "NOME_BENEF_folha",
        sexo_op: "SEXO_folha",
        plano_op: "PLANO_folha",
        dt_op: "DATA DE NASCIMENTO_folha",
        cpft_op: "CPF TITULAR_folha",
        parentesco_op: "PARENTESCO_folha"}

    df_analise = df_analise.sort_values(by="está presente onde ?")

    #Criação das colunas de conferência
    col_comps = []
    mask = df_analise["está presente onde ?"] == "presente em ambas"

    for col_op, col_folha in colunas_para_conferir.items():
        nome_col_conferencia = f"Conferencia_{col_op.split()[0]}"
        df_analise[nome_col_conferencia] = ""
        df_analise.loc[mask, nome_col_conferencia] = (
            df_analise.loc[mask, col_op]
            .eq(df_analise.loc[mask, col_folha])
            .map({True: "Igual", False: "Diferente"})
        )
        col_comps.append(nome_col_conferencia)

    #Gerar resumo_comparacoes_lista
    resumo_comparacoes_lista = []
    for col in col_comps:
        contagem = df_analise[col].value_counts(dropna=False)
        resumo_comparacoes_lista.append({
            "Comparação": col,
            "Iguais": contagem.get("Igual", 0),
            "Diferentes": contagem.get("Diferente", 0),
            "Total": contagem.get("Igual", 0) + contagem.get("Diferente", 0)
        })

    #Gerar resumo_totais
    resumo_totais = (
        df_analise
        .groupby("está presente onde ?", dropna=False)
        .agg(total_de_registros=("chave_merge", "count"))
        .reset_index()
    )

    #Gerar DataFrame final blindado
    def gerar_resumo_comparacoes(resumo_comparacoes_lista, resumo_totais):
        colunas_comparacoes = ["Comparação", "Iguais", "Diferentes", "Total"]
        df_comparacoes = pd.DataFrame(resumo_comparacoes_lista, columns=colunas_comparacoes)

        df_totais = resumo_totais.rename(columns={"total_de_registros": "Total"})
        df_totais["Comparação"] = "Totais"
        df_totais["Iguais"] = 0
        df_totais["Diferentes"] = 0

        for col in ["Iguais", "Diferentes", "Total"]:
            df_comparacoes[col] = df_comparacoes[col].fillna(0).astype(int)
            df_totais[col] = df_totais[col].fillna(0).astype(int)

        resumo_comparacoes = pd.concat([df_totais, df_comparacoes], axis=0, ignore_index=True)
        return resumo_comparacoes

    resumo_comparacoes = gerar_resumo_comparacoes(resumo_comparacoes_lista, resumo_totais)

    # Drop de colunas auxiliares
    colunas_auxiliares = ["primeiro_nome",'primeiro_nome_x', "chave_merge",'primeiro_nome_y']
    df_folha_1 = df_folha_1.drop(columns=colunas_auxiliares, errors='ignore')
    df_operadora_1 = df_operadora_1.drop(columns=colunas_auxiliares, errors='ignore')
    df_analise = df_analise.drop(columns=colunas_auxiliares, errors='ignore')

    return df_analise, df_operadora_1, df_folha_1, resumo_comparacoes, resumo_totais
    
    

def init_session_state():
    defaults = {
        "comparacoes": [],
        "operadora_bytes": None,
        "folha_bytes": None,
        "resultado": None
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
def app():
    init_session_state()
    st.title("Auditoria Cadastral")
    

    st.subheader("📂 Upload de Arquivos para Bate Cadastral")
    
    # Upload do arquivo da operadora
    #uploaded_file_operadora_1 = st.file_uploader("Envie o arquivo de Posição Cadastral xlsx", type=["xlsx", "xls"], key="file_operadora_1")
    #selecione a Operadora
    
   
    st.markdown("### 📤 Arquivo da Operadora")
    uploaded_file_operadora_1 = st.file_uploader(
        "Envie o arquivo da operadora (XLSX ,CSV, XLS)", 
        type=["xlsx", "xls",'csv'], 
        key="file_operadora_1"
    )
    if uploaded_file_operadora_1 is not None:
        st.session_state["operadora_bytes"] = uploaded_file_operadora_1.getvalue()
        st.success("✅ Arquivo da operadora carregado com sucesso!")
        Operadora_fatura = st.selectbox("Selecione a Operadora",['Padrão','Bradesco','Amil','Sulamerica','Seguros Unimed','CNU','OdontoPrev'])
    else:
        st.warning("⚠️ Aguardando o envio do arquivo da operadora.")
########## operadoras ##############
    if uploaded_file_operadora_1 is not None:
        if Operadora_fatura == 'Bradesco':
            df_operadora_1 = arquivo_bradesco.Bradesco_arquivo_Pc(uploaded_file_operadora_1)
        elif Operadora_fatura == 'Amil':
            df_operadora_1 = Amil.Amil_arquivo_pc(uploaded_file_operadora_1)
            
        elif Operadora_fatura == 'Sulamerica':
            df_operadora_1=Sulamerica.Pc_Sulamerica(uploaded_file_operadora_1)
            
        elif Operadora_fatura == 'Seguros Unimed':
            df_operadora_1 = Central_unimed.posicao_cadastral_seguros_uniemd(uploaded_file_operadora_1)
            
        elif Operadora_fatura == 'CNU':
            df_operadora_1=CNU.CNU_arquivo_Pc(uploaded_file_operadora_1)
            
        elif Operadora_fatura=='OdontoPrev':
            df_operadora_1=OdontoPrev.OdontoPrev_arquivo_pc(uploaded_file_operadora_1)
            
        elif Operadora_fatura == 'Padrão':
            st.info("Selecione a Operadora")
            
    st.markdown("### 📤 Arquivo da Folha da Empresa")
    uploaded_file_folha_1 = st.file_uploader(
        "Envie o arquivo da folha (XLSX ,CSV, XLS)", 
        type=["xlsx", "xls",'csv'], 
        key="file_folha_1"
    )
    if uploaded_file_folha_1 is not None:
        st.session_state["folha_bytes"] = uploaded_file_folha_1.getvalue()

        st.success("✅ Arquivo da folha carregado com sucesso!")
    else:
        st.warning("⚠️ Aguardando o envio do arquivo da folha.")

    if uploaded_file_folha_1 is not None and uploaded_file_operadora_1 is not None and Operadora_fatura:
        st.markdown("---")
        st.success(f"🎯 Arquivos enviados e operadora definida: {Operadora_fatura}. Pronto para avançar!")
    elif uploaded_file_folha_1 is not None and uploaded_file_operadora_1 is not None and not Operadora_fatura:
        st.warning("⚠️ Arquivos enviados, mas selecione a operadora antes de prosseguir.")
    else:
        st.info("📂 Envie todos os arquivos e selecione a operadora para continuar.")
 ###############################################################################################################

 ###############################################################################################################################
    if uploaded_file_folha_1 is not None and uploaded_file_operadora_1 is not None and Operadora_fatura:
        try:
            #mostra os dados da operadora
            with st.expander("Mostrar dados da operadora"):
                st.write("Prévia dos dados operadora:")
                colunas_str = df_operadora_1.columns
                df_operadora_1[colunas_str] = (df_operadora_1[colunas_str].astype("string").apply(lambda x: x.str.strip().replace("", pd.NA)))

                # criar view só para exibição
                df_operadora_1_view = df_operadora_1.copy()
                st.dataframe(df_operadora_1_view, use_container_width=True, height=400)


            df_folha_1 = pd.read_excel(uploaded_file_folha_1)
            #mostra dados folha
            ajuste_cpf = st.toggle("ajustar cpf folha ?")
            
            if ajuste_cpf:
                with st.expander("selecione as colunas de cpf"):
                    colunas_cpf=[]
                    colunas_cpf =st.multiselect("colunas de cpf",df_folha_1.columns.tolist())
                    for coluna in colunas_cpf:
                        df_folha_1[coluna]= (df_folha_1[coluna].astype(str).str.strip().str.replace(r'\D+', '', regex=True))
                       
            with st.expander("Mostrar dados da Folha"):
                st.write("Prévia dos dados folha:")
                df_folha_1_view=df_folha_1.copy(deep=True)
                st.dataframe(df_folha_1_view, use_container_width=True, height=400)
                
                
            #an_padrao
            
            an_pd = st.toggle("Analise Padrão ?")


            if an_pd:
                colunas_para_renomear = df_folha_1.columns 
                df_folha_1.rename(
                columns={col: f"{col}_folha" for col in colunas_para_renomear},
                inplace=True)
                #LAYOUT PADRAO BRADESCU
               
                if Operadora_fatura =='Bradesco':
                
                    
                    df_operadora_1['NUMERO DO CPF']=df_operadora_1['NUMERO DO CPF'].astype(str).str.zfill(11)
                    df_folha_1["primeiro_nome"] = df_folha_1["NOME_BENEF_folha"].fillna('').astype(str).str.strip().str.lower().str.split().str[0].apply(unidecode)    
                    df_operadora_1["primeiro_nome"]= df_operadora_1["NOME DO SEGURADO"].fillna('').astype(str).str.strip().str.lower().str.split().str[0].apply(unidecode)
                    
                    # chave para enrigecer o codigo
                    df_folha_1['PARENTESCO_folha']=df_folha_1["PARENTESCO_folha"].apply(unidecode)
                    
                    
                    df_folha_1["chave_merge"] = df_folha_1['CPF_folha']
                    df_operadora_1["chave_merge"] =df_operadora_1['NUMERO DO CPF'] 
        
                    df_analise = pd.merge(df_operadora_1,df_folha_1,on="chave_merge",how="outer",indicator=True)
                    df_analise["_merge"] = df_analise["_merge"].astype(str).replace({"left_only": "presente na operadora", "both": "presente em ambas", "right_only": "presente na folha"})
                    df_analise.rename(columns={"_merge": "está presente onde ?"}, inplace=True)
                    
                    df_analise['NOME_BENEF_folha'] = df_analise['NOME_BENEF_folha'].fillna('').astype(str).str.strip().str.lower()
                    df_analise['NOME DO SEGURADO'] = df_analise['NOME DO SEGURADO'].fillna('').astype(str).str.strip().str.lower()
                    df_analise['NOME DO SEGURADO']=df_analise['NOME DO SEGURADO'].apply(unidecode)
                    df_analise['NOME_BENEF_folha']=df_analise['NOME_BENEF_folha'].apply(unidecode)
                    
                    
                    
                    df_analise['DATA DE NASCIMENTO_folha'] = pd.to_datetime(df_analise['DATA DE NASCIMENTO_folha'], errors='coerce')
                    df_analise["DATA DE NASCIMENTO_folha"]=df_analise["DATA DE NASCIMENTO_folha"].dt.strftime('%d/%m/%Y')
                    
                    df_analise['CPF_TITULAR'] = df_analise['CPF_TITULAR'].astype(str).str.zfill(11)  # garante 11 dígitos
                    df_analise['CPF TITULAR_folha'] = df_analise['CPF TITULAR_folha'].astype(str).str.zfill(11)
                    
                    colunas_para_conferir = {
                            "NOME DO SEGURADO": "NOME_BENEF_folha",
                            "SEXO DO SEGURADO": "SEXO_folha",
                            "PLANO": "PLANO_folha",
                            "DATA DE NASCIMENTO (Y2K)": "DATA DE NASCIMENTO_folha",
                            "CPF_TITULAR": "CPF TITULAR_folha",
                            "GRAU_PARENTESCO": "PARENTESCO_folha"
                    }
                    df_analise = df_analise.sort_values(by="está presente onde ?")
                    
                
                    for col_op, col_folha in colunas_para_conferir.items():
                            nome_col_conferencia = f"Conferencia_{col_op.split()[0]}"  # exemplo: "Conferencia_NOME"
                            df_analise[nome_col_conferencia] = ""  # começa vazia

                    # Masc
                    mask = df_analise["está presente onde ?"] == "presente em ambas"
                    col_comps=[]
                    
                    # Aplica a conferência para cada coluna, apenas nas linhas presentes em ambas
                    for col_op, col_folha in colunas_para_conferir.items():
                            nome_col_conferencia = f"Conferencia_{col_op.split()[0]}"
                            df_analise.loc[mask, nome_col_conferencia] = (
                                df_analise.loc[mask, col_op]
                                .eq(df_analise.loc[mask, col_folha])
                                .map({True: "Igual", False: "Diferente"}))
                            col_comps.append(nome_col_conferencia)
                        

                    #dropa colunas auxiliares
                    resumo_comparacoes = []
                    for coluna in col_comps:
                        if coluna in df_analise.columns:
                            contagem = df_analise[coluna].value_counts(dropna=False)
                            resumo_comparacoes.append({
                                "Comparação": coluna,
                                "Iguais": contagem.get("Igual", 0),
                                "Diferentes": contagem.get("Diferente", 0),
                                "Total": contagem.get("Igual", 0) + contagem.get("Diferente", 0)
                            })
                            
                    resumo_totais =df_analise.groupby("está presente onde ?").agg(total_de_registros=("chave_merge","count")).reset_index()
                    resumo_totais[""]=pd.NA
                    resumo_totais[" "]=pd.NA
                    print(resumo_comparacoes)
                    resumo_comparacoes=pd.DataFrame(resumo_comparacoes)
                    
                    resumo_comparacoes =pd.concat([resumo_totais, resumo_comparacoes], axis=0, ignore_index=True)
                    resumo_comparacoes['Iguais']=resumo_comparacoes['Iguais'].fillna(0).astype(int)
                    resumo_comparacoes['Diferentes']=resumo_comparacoes['Diferentes'].fillna(0).astype(int)
                    resumo_comparacoes['Total']=resumo_comparacoes['Total'].fillna(0).astype(int)
                    resumo_comparacoes['total_de_registros']=resumo_comparacoes['total_de_registros'].fillna(0).astype(int)
                    

                    colunas_auxiliares = ["primeiro_nome",'primeiro_nome_x', "chave_merge",'primeiro_nome_y']
                    
                    df_folha_1=df_folha_1.drop(columns=colunas_auxiliares, errors='ignore')
                    
                    df_operadora_1=df_operadora_1.drop(columns=colunas_auxiliares, errors='ignore')
                    
                    df_analise = df_analise.drop(columns=colunas_auxiliares, errors='ignore')
                            
                if Operadora_fatura =='Sulamerica':
                    
                    #df_folha_1['CPF_folha'] = df_folha_1['CPF_folha'].astype(str).str.zfill(11)
                    df_operadora_1['CPF'] = df_operadora_1['CPF'].fillna('').astype(str).str.zfill(11)
                    df_operadora_1['Matricula'] = df_operadora_1['Matricula'].fillna('').astype(str)
                    #df_analise =pd.merge(df_operadora_1, df_folha_1, left_on='CPF', right_on='CPF_folha', how='outer', indicator=True)
                    
                    #######################################
                    nome="Nome completo do beneficiario"
                    dt_op="Data_Nasc"
                    sexo_op="Sexo"
                    plano_op="Plano"
                    parentesco_op="GRAU_PARENTESCO"
                    cpft_op= "CPF_Titular"
                    cpf="CPF"

                    # Inicializa a lista antes do loop
                    resumo_comparacoes = []
    
                    df_analise,df_operadora_1, df_folha_1 , resumo_comparacoes, resumo_totais = padrao(nome,dt_op,cpft_op,sexo_op,plano_op,parentesco_op,cpf,df_folha_1,df_operadora_1)                    
                if Operadora_fatura =='CNU':
                    df_folha_1['CPF_folha'] = df_folha_1['CPF_folha'].astype(str).str.zfill(11)
                    df_operadora_1['CPF'] = df_operadora_1['CPF'].fillna('').astype(str).str.zfill(11)
                    df_operadora_1['NUM_MATRIC_EMPRESA'] = df_operadora_1['NUM_MATRIC_EMPRESA'].fillna('').astype(str)

                    
                    #######################################
                    nome="NOME_ASSOCIADO"
                    dt_op="DATA_NASCIMENTO"
                    sexo_op="SEXO"
                    plano_op="COD_PLANO"
                    parentesco_op="NOME_TIPO_BENEFICIARIO"
                    cpft_op= "CPF_Titular"
                    cpf="NUM_CPF"

                    # Inicializa a lista antes do loop
                    resumo_comparacoes = []
    
                    df_analise,df_operadora_1, df_folha_1 , resumo_comparacoes, resumo_totais = padrao(nome,dt_op,cpft_op,sexo_op,plano_op,parentesco_op,cpf,df_folha_1,df_operadora_1)
                    
                if Operadora_fatura =='Amil':
                    df_folha_1['CPF_folha'] = df_folha_1['CPF_folha'].astype(str).str.zfill(11)
                    df_operadora_1['CPF'] = df_operadora_1['CPF'].fillna('').astype(str).str.zfill(11)
                    df_operadora_1['MATRÍCULA FUNCIONAL'] = df_operadora_1['MATRÍCULA FUNCIONAL'].fillna('').astype(str)

                    
                    #######################################
                    nome="NOME DO BENEFICIÁRIO"
                    dt_op="DATA DE NASCIMENTO"
                    sexo_op="SEXO"
                    plano_op="CÓDIGO DO PLANO"
                    parentesco_op="PARENTESCO"
                    cpft_op= "CPF_Titular"

                    # Inicializa a lista antes do loop
                    resumo_comparacoes = []
    
                    df_analise,df_operadora_1, df_folha_1 , resumo_comparacoes, resumo_totais = padrao(nome,dt_op,cpft_op,sexo_op,plano_op,parentesco_op,cpf,df_folha_1,df_operadora_1)
                      
                if Operadora_fatura =='Seguros Unimed':
                    df_folha_1['CPF_folha'] = df_folha_1['CPF_folha'].astype(str).str.zfill(11)
                    df_operadora_1['CPF'] = df_operadora_1['CPF'].fillna('').astype(str).str.zfill(11)
                    df_operadora_1['Código Família'] = df_operadora_1['Código Família'].fillna('').astype(str)

                    
                    #######################################
                    nome="Nome Segurado"
                    dt_op="Data Nascimento"
                    sexo_op="Sexo"
                    plano_op="Plano/Prod"
                    parentesco_op="PARENTESCO"
                    cpft_op= "CPF_Titular"
                    

                    
                    

                    # Inicializa a lista antes do loop
                    resumo_comparacoes = []
    
                    df_analise,df_operadora_1, df_folha_1 , resumo_comparacoes, resumo_totais = padrao(nome,dt_op,cpft_op,sexo_op,plano_op,parentesco_op,cpf,df_folha_1,df_operadora_1)
                
                if Operadora_fatura=='OdontoPrev':
                    nome="NOME_BENEFICIARIO"
                    dt_op="DATA_DE_NASCIMENTO"
                    cpf="CPF_ASSOCIADO"
                    plano_op="PLANO"
                    parentesco_op='PARENTESCO'
                    cpft_op= "CPF_TITULAR"
                    sexo_op="Sexo"
                    
                    df_analise,df_operadora_1, df_folha_1 , resumo_comparacoes, resumo_totais = padrao(nome,dt_op,cpft_op,sexo_op,plano_op,parentesco_op,cpf,df_folha_1,df_operadora_1)

            else:    
                @st.dialog("Renomear")
                
                def abrir_dialogo_renomear():
                    tab1, tab2 = st.tabs(["Folha", "Operadora"])

                    #Folha
                    with tab1:
                        with st.form("form_renomear_folha"):
                            novos_nomes_folha = {}
                            for col in df_folha_1.columns:
                                novo_nome = st.text_input(f"Novo nome para '{col}'", value=col, key=f"renomear_folha_{col}")
                                novos_nomes_folha[col] = novo_nome

                            if st.form_submit_button("Aplicar renomeação da Folha", type="primary"):
                                df_folha_1.rename(columns=novos_nomes_folha, inplace=True)
                                st.success("Colunas da folha renomeadas com sucesso!")
                                st.rerun()

                    #Operadora
                    with tab2:
                        with st.form("form_renomear_operadora"):
                            novos_nomes_operadora = {}
                            for col in df_operadora_1.columns:
                                novo_nome = st.text_input(f"Novo nome para '{col}'", value=col, key=f"renomear_operadora_{col}")
                                novos_nomes_operadora[col] = novo_nome

                            if st.form_submit_button("Aplicar renomeação da Operadora", type="primary"):
                                df_operadora_1.rename(columns=novos_nomes_operadora, inplace=True)
                                st.success("Colunas da operadora renomeadas com sucesso!")
                                st.rerun()

                # Botão que chama o dialogo
                if st.button("Renomear Colunas"):
                    abrir_dialogo_renomear()
                
                
                # Atualize as listas de colunas após renomear
                colunas_folha_1 = df_folha_1.columns.tolist()
                colunas_operadora_1 = df_operadora_1.columns.tolist()

                # Escolhe a chave
                col1 = st.selectbox("Selecione a coluna chave na operadora", colunas_operadora_1)
                col2 = st.selectbox("Selecione a coluna chave na folha", colunas_folha_1)

                # Forçar tipo string para merge
                df_operadora_1[col1] = df_operadora_1[col1].astype(str)
                df_folha_1[col2] = df_folha_1[col2].astype(str)

                # Merge inicial
                df_analise = pd.merge(df_operadora_1, df_folha_1, left_on=col1, right_on=col2, how='outer', indicator=True)
                df_analise["_merge"] = df_analise["_merge"].replace({"left_only": "presente na operadora", "both": "presente em ambas", "right_only": "presente na folha"})
                df_analise.rename(columns={"_merge": "está presente onde ?"}, inplace=True)

                # --- Adicionar Comparações Dinâmicas ---
                @st.dialog("Adicionar Comparação de Colunas")
                def abrir_dialogo_comparacao():
                    st.markdown("### Comparações Personalizadas")
                    col_op = st.selectbox("Coluna da operadora para comparar", colunas_operadora_1, key="col_op_comparar_dialog")
                    col_folha = st.selectbox("Coluna da folha para comparar", colunas_folha_1, key="col_folha_comparar_dialog")

                    if st.button("Adicionar", key="botao_adicionar_dialog"):
                        st.session_state.comparacoes.append((col_op, col_folha))
                        st.rerun()  # Atualiza a interface principal com a nova comparação

                # Botão principal que abre o diálogo
                if st.button("Nova Comparação"):
                    abrir_dialogo_comparacao()
                
                
                #se der erro esse serve
                '''col_op = st.selectbox("Coluna da operadora para comparar", colunas_operadora_1, key="col_op_comparar")
                col_folha = st.selectbox("Coluna da folha para comparar", colunas_folha_1, key="col_folha_comparar")
                if st.button("Adicionar Comparação"):
                    st.session_state.comparacoes.append((col_op, col_folha))'''

                # Realizar as comparações salvas
                for c_op, c_folha in st.session_state.comparacoes:
                    nome_coluna_resultado = f"Comparação_{c_op}_vs_{c_folha}"
                    try:
                        comparacao = df_analise[c_op] == df_analise[c_folha]
                        df_analise[nome_coluna_resultado] = comparacao.map({True: "Igual", False: "Diferente"})
                    except Exception as e:
                        df_analise[nome_coluna_resultado] = f"Erro: {e}"

                # 2. Mostrar o df_analise atualizado
                
                # st.dataframe(df_analise)
                # 3. Criar o resumo das comparações
                resumo_comparacoes = []
                for c_op, c_folha in st.session_state.comparacoes:
                    nome_coluna_resultado = f"Comparação_{c_op}_vs_{c_folha}"
                    if nome_coluna_resultado in df_analise.columns:
                        contagem = df_analise[nome_coluna_resultado].value_counts(dropna=False)
                        resumo_comparacoes.append({
                            "Comparação": f"{c_op} vs {c_folha}",
                            "Iguais": contagem.get("Igual", 0),
                            "Diferentes": contagem.get("Diferente", 0),
                            "Total": contagem.get("Igual", 0) + contagem.get("Diferente", 0)
                        })
            
            #st.dataframe(df_folha_1)
           # st.dataframe(df_operadora_1)
            #df_analise = df_analise.fillna('')            
            st.dataframe(df_analise)
            # . Criar dataframe de resumo e mostrar
            df_view_comparacoes=resumo_comparacoes
            
            #df_view_comparacoes = pd.DataFrame(resumo_comparacoes)
            st.markdown("### Resumo das Comparações")
            st.dataframe(df_view_comparacoes)
            
            # . Função para tratar categorias e preencher nulos com vazio
            def fill_categoricals_with_empty(df: pd.DataFrame) -> pd.DataFrame:
                assert isinstance(df, pd.DataFrame), f"Esperado DataFrame, recebido {type(df)}"

                for col in df.select_dtypes(['category']).columns:
                    df[col] = df[col].cat.add_categories(['']).fillna('')

                return df
            
            
            
            # 6. Aplicar tratamento antes de exportar
            dfs_para_exportar = {
                'Folha_Cliente': df_folha_1,
                'Folha_Operadora': df_operadora_1,
                'Auditoria': df_analise,
                'Resumo_Auditoria': df_view_comparacoes
            }
            for k, v in dfs_para_exportar.items():
                print(k, type(v))
            if isinstance(df_view_comparacoes, list):
               df_view_comparacoes = pd.concat(df_view_comparacoes, ignore_index=True)
            assert isinstance(df_view_comparacoes, pd.DataFrame)
            
            for key in dfs_para_exportar:
                dfs_para_exportar[key] = fill_categoricals_with_empty(dfs_para_exportar[key]).fillna('').astype(str)
                
            # 7. Gerar arquivo Excel em buffer
            buffer = BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                for sheet_name, df_export in dfs_para_exportar.items():
                    df_export.to_excel(writer, sheet_name=sheet_name, index=False)
                    
                    workbook = writer.book
                    worksheet = writer.sheets[sheet_name]

                    # Formatos
                    formato_cabecalho = workbook.add_format({
                        'bold': True,
                        'bg_color': '#1F4E78',
                        'font_color': '#FFFFFF',
                        'border': 1,
                        'align': 'center',
                        'valign': 'vcenter'
                    })

                    formato_corpo = workbook.add_format({
                        'font_color': '#000000',
                        'bg_color': '#FFFFFF',
                        'align': 'left',
                        'valign': 'vcenter'
                    })

                    # Aplica formato de cabeçalho
                    for col_num, value in enumerate(df_export.columns.values):
                        worksheet.write(0, col_num, value, formato_cabecalho)

                    # Ajusta largura das colunas automaticamente
                    for i, col in enumerate(df_export.columns):
                        max_len = max(df_export[col].astype(str).map(len).max(), len(col)) + 2
                        worksheet.set_column(i, i, max_len)

                    # Aplica formato de corpo em todas as células de dados
                    # Usa conditional_format para todas as células, evitando loops
                    worksheet.conditional_format(1, 0, len(df_export), len(df_export.columns)-1,
                                                {'type': 'no_errors', 'format': formato_corpo})

            

            buffer.seek(0)

            # 8. Botão de download
            if st.download_button(
                label="📥 Clique para baixar o arquivo",
                data=buffer.getvalue(),
                file_name="Auditoria.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ,
            ):
                st.success("Download iniciado!")

        except Exception as e:
            st.warning(e)
            #st.warning(f'Conclua as etapas anteriores. Erro: {e}')