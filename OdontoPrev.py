import pandas as pd

def OdontoPrev_arquivo_pc(df_operadora):
  """
  Função simples para processar o DataFrame da OdontoPrev.
  """
  df_operadora=pd.read_excel(df_operadora)
  
  # Garantir que as colunas essenciais existam


  # Mapeamento de parentesco
  graus = {
      'TITULAR': 'Titular',
      'DEP LEGAL': 'Dep_Legal',
      'FILHO': 'Filho(a)',
      'CONJUGE': 'Conjuge',
      'MAE': 'Mae',
      'IRMA': 'Irma',
      'PAI': 'Pai'
  }
  df_operadora['PARENTESCO'] = df_operadora['PARENTESCO'].map(graus).fillna(df_operadora['PARENTESCO'])

  # Formatação de CPF
  def format_cpf(x):
      if pd.isnull(x):
          return ''
      x = str(x)
      x = ''.join(filter(str.isdigit, x))
      return x.zfill(11)

  df_operadora['CPF_ASSOCIADO'] = df_operadora['CPF_ASSOCIADO'].apply(format_cpf)
  df_operadora['CPF_TITULAR'] = df_operadora['CPF_TITULAR'].apply(format_cpf)

  # Centro de custo como string
  df_operadora['CENTRO DE CUSTO'] = df_operadora['CENTRO DE CUSTO'].astype(str)

  # Datas e numéricos
  df_operadora["DATA_DE_NASCIMENTO"] = pd.to_datetime(df_operadora["DATA_DE_NASCIMENTO"], errors="coerce", format='%d/%m/%Y').dt.strftime('%d/%m/%Y')
  df_operadora["MATRÍCULA"] = pd.to_numeric(df_operadora["MATRÍCULA"], errors="coerce")

  # Coluna Sexo
  df_operadora["Sexo"] = "não_Informado"

  return df_operadora