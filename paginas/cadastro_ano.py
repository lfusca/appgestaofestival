import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DB_URL = os.getenv("DB_URL")

def show():
    st.write("# Cadastros")

    ano = st.text_input("Digite o ano:", key="campo_ano")

    if st.button("Salvar", key="btn_salvar"):
        if ano:
                try:
                    conn = psycopg2.connect(DB_URL)
                    cursor = conn.cursor()

                    query = "INSERT INTO tbl_anos (id_ano) VALUES (%s)"
                    cursor.execute(query, (ano,))
                    conn.commit()

                    st.success(f"Ano '{ano}' inserido com sucesso no banco de dados!")
                except errors.UniqueViolation:
                    st.error(f"Erro: O ano '{ano}' já existe no banco de dados.")

                except Exception as e:
                    st.error(f"Ocorreu um erro ao inserir o ano: {e}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()


    st.title("Anos cadastrados")

    def apagar_ano(ano):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        delete_query = "DELETE FROM tbl_anos WHERE id_ano = %s;"
        # Converter para int nativo do Python
        ano_python = int(ano)
        cursor.execute(delete_query, (ano_python,))
        conn.commit()
        cursor.close()
        conn.close()

    def carregar_dados():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = 'SELECT id_ano AS "Anos" FROM tbl_anos;'
        cursor.execute(query)
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows, columns=colunas)
        # Converter para int nativo do Python
        df["Anos"] = df["Anos"].apply(lambda x: int(x))
        return df

    # Se há um ano a apagar no estado, apague antes de carregar os dados
    if 'delete_ano' in st.session_state:
        apagar_ano(st.session_state['delete_ano'])
        del st.session_state['delete_ano']  # Remove a chave para não apagar novamente na próxima execução

    df = carregar_dados()

    if df.empty:
        st.write("Não há dados para exibir.")
    else:
        col_titulo_ano, col_titulo_acoes = st.columns([3,1])
        col_titulo_ano.write("**Anos**")
        col_titulo_acoes.write("**Ações**")

        # Exibição da tabela linha a linha
        for index, row in df.iterrows():
            ano_val = row["Anos"]
            col_ano, col_btn = st.columns([3,1])
            col_ano.write(ano_val)

            # Ao clicar no botão, apenas marca no session_state o ano a ser apagado
            if col_btn.button("Apagar", key=f"apagar_{ano_val}"):
                st.session_state['delete_ano'] = ano_val