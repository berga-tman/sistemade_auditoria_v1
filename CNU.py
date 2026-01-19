import pandas as pd 


def CNU_arquivo_Pc(df_operadora):
      
    df_operadora = pd.read_csv(
    df_operadora,
    sep=';',
    encoding='latin1')
    
    df_operadora['NUM_CPF']=df_operadora['NUM_CPF'].astype(str).str.zfill(11)
    df_operadora['NOME_TIPO_BENEFICIARIO'] =df_operadora['NOME_TIPO_BENEFICIARIO'].apply(lambda x: "Filho(a)" 
                                                                                         if x == "Filho" else ( "Filho(a)" if x == "Filha" 
                                                                                                               else ( "Conjuge" if x== 'Cnjuge' 
                                                                                                                     else ('Companheiro(a)'if x=='Companheiro ou Companheira'
                                                                                                                           else( 'Titular'if x=='TITULAR' else x)))))
    df_operadora['NUM_CARTAO'] = (df_operadora['NUM_CARTAO'].astype(str).str[:-5])
    df_tit = df_operadora[df_operadora['NOME_TIPO_BENEFICIARIO'] == "Titular"]
    
    df_t= df_tit.set_index('NUM_CARTAO')['NUM_CPF']
    df_operadora['CPF_Titular']=df_operadora['NUM_CARTAO'].map(df_t)
    
    
    colunas_operadora_1=df_operadora
    return colunas_operadora_1
    