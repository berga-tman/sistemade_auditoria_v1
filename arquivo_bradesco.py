import pandas as pd 
from unidecode import unidecode
def Bradesco_arquivo_Pc(df_operadora):
    

    df_dep = pd.read_excel(df_operadora,sheet_name='POS. CADASTRAL (DEPENDENTES)',header=0)

    tipos = {
    "TIPO DE REGISTRO": "string",
    "NUMERO DA SUBFATURA": "string",
    "NUMERO DO CERTIFICADO": "string",
    "NOME DO SEGURADO": "string",
    "DATA DE NASCIMENTO": "datetime64[ns]",
    "SEXO DO SEGURADO": "string",
    "ESTADO CIVIL": "string",
    "MATRICULA ESPECIAL": "string",
    #"DATA DE NASCIMENTO (Y2K)": "datetime64[ns]",
    #"DATA DE INICIO DE VIGENCIA (Y2K)": "datetime64[ns]",
    "NUMERO DO CPF": "string"
    }
    #"GRAU_PARENTESCO": "float64",
    
    df_dep.columns = df_dep.columns.map(lambda x: unidecode(x).strip().upper())
    renomear_colunas_dep = {
        "TIPO DE REGISTRO": "TIPO DE REGISTRO",
        "NUMERO DA SUBFATURA": "NUMERO DA SUBFATURA",
        "NUMERO DO CERTIFICADO": "NUMERO DO CERTIFICADO",
        "CODIGO DO DEPENDENTE": "1",
        "NOME DO DEPENDENTE": "NOME DO SEGURADO",
        "NOME DEPENDENTE": "NOME DO SEGURADO",
        "DATA DE NASCIMENTO": "DATA DE NASCIMENTO",
        "SEXO DO DEPENDENTE": "SEXO DO SEGURADO",
        "ESTADO CIVIL DO DEPENDENTE": "ESTADO CIVIL",
        "GRAU PARENTESCO": "GRAU_PARENTESCO",
        "GRAU DE PARENTESCO": "GRAU_PARENTESCO",
        "DATA DE INICIO DE VIGENCIA": "2",
        "MATRICULA ESPECIAL": "MATRICULA ESPECIAL",
        #"DATA DE NASCIMENTO (Y2K)": "DATA DE NASCIMENTO (Y2K)",
        #"DATA DE INICIO DE VIGENCIA (Y2K)": "DATA DE INICIO DE VIGENCIA (Y2K)",
        "MATRICULA ESPECIAL DO DEPENDENTE": "3",
        "DATA DE REATIVA��O": "4",
        "DATA DE CANCELAMENTO": "5",
        "NUMERO DO CPF": "NUMERO DO CPF",
        "NUMERO DO CPF DO DEPENDENTE": 'NUMERO DO CPF',
        "NUMERO DO CART�O DEPENDENTE": "6",
        "NOME DA M�E DO DEPENDENTE": "7"
    }
    df_dep["MATRICULA ESPECIAL"] = df_dep["MATRICULA ESPECIAL"].astype(str)
    
    df_dep = df_dep.rename(columns=renomear_colunas_dep)
    cols_para_remover = ['2', '1', '3', '4', '5', '6', '7']

    cols_existentes = [col for col in cols_para_remover if col in df_dep.columns]
    
    df_dep = df_dep.drop(columns=cols_existentes)
    
    #df_dep=df_dep.astype(tipos)
    df_titular = pd.read_excel(df_operadora,sheet_name='POS. CADASTRAL (TITULAR)',header=2) 
    df_titular.columns = df_titular.columns.map(
    lambda x: unidecode(x).strip().upper())
    
    #planos
    if "PLANO" not in df_titular.columns :
    
        df_planos=pd.read_excel(df_operadora,sheet_name='POS. CADASTRAL (DADOS PLANO)',header=0) 
        
        df_planos.columns = df_planos.columns.map(lambda x: unidecode(str(x)).strip())
        
        df_planos= df_planos.set_index('NUMERO DO CERTIFICADO')['PLANO']
        
        df_titular["PLANO"]=  df_titular['NUMERO DO CERTIFICADO'].map(df_planos)


    df_titular['NUMERO DO CERTIFICADO'] = df_titular['NUMERO DO CERTIFICADO'].astype(str).str.zfill(7)
    
    df_dep['NUMERO DO CERTIFICADO'] = df_dep['NUMERO DO CERTIFICADO'].astype(str).str.zfill(7)
    df_concat = pd.concat([df_titular,df_dep], ignore_index=True)
    df_plan = df_titular.set_index('NUMERO DO CERTIFICADO')['PLANO']
    
    df_Tit = df_titular.set_index('NUMERO DO CERTIFICADO')['NUMERO DO CPF'].astype(str).str.zfill(11)

    #print(df_concat.columns.tolist())
    def normaliza_cpf(x):
        if pd.isna(x):
            return x

        s = str(x).strip()

        # remove tudo que não for dígito
        digits = ''.join(c for c in s if c.isdigit())

        if not digits:
            return None  # ou mantenha x, decisão de negócio

        if len(digits) > 11:
            return None  # dado inválido, não inventa

        return digits.zfill(11)

    df_concat['NUMERO DO CPF'] = df_concat['NUMERO DO CPF'].apply(normaliza_cpf)
    df_concat['GRAU_PARENTESCO']=df_concat['GRAU_PARENTESCO'].apply(lambda x: "Conjuge" if x == 1 else ("Filho(a)" if x == 2 else "Titular"))
    df_concat['SEXO DO SEGURADO']=df_concat['SEXO DO SEGURADO'].apply(lambda x: "F" if x == "02" else ( "M" if x == "01" else ( "F" if x== 2 else "M")))
    
    df_concat['CPF_TITULAR']=df_concat["NUMERO DO CERTIFICADO"].map(df_Tit)
    
    df_concat['PLANO']=df_concat["NUMERO DO CERTIFICADO"].map(df_plan)
    
    df_concat=df_concat.dropna(subset=['NUMERO DO CPF'])
    df_concat = df_concat.fillna('').astype(str)
    
    
    '''f_concat= pdmerge'''
    colunas_operadora_1=df_concat
    return colunas_operadora_1