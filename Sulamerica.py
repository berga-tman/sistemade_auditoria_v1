import pandas as pd

def Pc_Sulamerica(df_operadora):
    df_operadora = pd.read_csv(df_operadora, sep=';', encoding='cp1252')#,skiprows=1)
    df_operadora = df_operadora.sort_values(by='Data_Adm', ascending=False)
    
    df_operadora.columns.astype(str).str.strip()
    
    df_titulares= df_operadora[df_operadora['Plano'].notna()]
    

    df_plano = df_titulares.drop_duplicates(subset='Matricula', keep='first').set_index('Matricula')['Plano']

    # Usa map para preencher a coluna PLANO no df_operadora
    df_operadora['PLANO'] = df_operadora['Matricula'].map(df_plano)

    # Mesma lógica para CPF do titular
    df_cpfs = df_titulares.drop_duplicates(subset='Matricula', keep='first').set_index('Matricula')['CPF']
    
    df_operadora['CPF_Titular'] = df_operadora['Matricula'].map(df_cpfs).astype(str).str.zfill(11)
    
    df_operadora['PLANO']=df_operadora['Matricula'].map(df_plano).astype(str)
    
    df_operadora['CPF']=df_operadora['CPF'].astype(str).str.zfill(11)
    
 
    df_operadora['GRAU_PARENTESCO']=df_operadora['RDP'].astype(str).apply(lambda x: "Titular" if x == "1" else ( "Conjuge" if x == "2" else "Filho(a)"))
    
    df_operadora['Data_Nasc'] = pd.to_datetime(df_operadora['Data_Nasc'], format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
    
    colunas_operadora_1=df_operadora
    return colunas_operadora_1
    
    