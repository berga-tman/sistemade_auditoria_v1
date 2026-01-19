import pandas as pd 

def Amil_arquivo_pc(df_operadora):
      
    df_operadora = pd.read_excel(df_operadora) 
    df_operadora['CPF']=df_operadora['CPF'].astype(str).str.zfill(11)
    df_operadora['PARENTESCO'] = df_operadora.apply(lambda row: ("Filho(a)" if row['PARENTESCO'] == "DEPENDENTE" and row['ESTADO CIVIL'] == "2"else "Conjuge" if row['PARENTESCO'] == "DEPENDENTE" and row['ESTADO CIVIL'] == "1"else "Titular"),axis=1)
    df_tit = df_operadora[df_operadora['PARENTESCO']=='Titular']
    df_t = df_tit.drop_duplicates(subset=['MATRÍCULA FUNCIONAL'],keep= 'first')
    df_operadora['CPF_Titular'] = df_operadora['MATRÍCULA FUNCIONAL'].map(df_t.set_index('MATRÍCULA FUNCIONAL')['CPF'])
    
    colunas_operadora_1=df_operadora
    return colunas_operadora_1
    