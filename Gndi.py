import pandas as pd 

arquivo = "R:\Inovacoes\Bernardo\Rep_sitemas\Inovavoes_sys\BASE DE ATIVOS OPERADORA - SAÚDE.CSV"

def pc_Gndi(arquivo):

    df_recebido  =pd.read_csv(arquivo,sep=";" , encoding="latin1")
    
    return df_recebido
