import pandas as pd

#arquivo='Base Seguros Unimed 18.06.xlsx'

def posicao_cadastral_seguros_uniemd(arquivo):

    df=pd.read_excel(arquivo)
    fi={'Filha':'Filho(a)','Filho':'Filho(a)','Filha adotiva':'Filho(a)','Filho adotivo':'Filho(a)'}

    df['Dependencia'] = df['Relação Dep.'].apply(lambda x: fi.get(x, x))

    df=df.rename(columns={'CPF Titular':'CPF'})
    return df









    