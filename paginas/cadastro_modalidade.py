import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DB_URL = os.getenv("DB_URL")

def show():
    st.write("# Cadastro de Modalidades")

    def carregar_anos():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id_ano FROM tbl_anos;')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        anos = [r[0] for r in rows]
        return anos

    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar modalidades.")
    else:
        # Seleciona o ano para cadastro e filtro
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar modalidades:", anos_disponiveis)

        # Campo para cadastrar modalidade
        nome_modalidade = st.text_input("Nome da modalidade:", key="campo_nome_modalidade")

        if st.button("Salvar", key="btn_salvar_modalidade"):
            if nome_modalidade and ano_selecionado:
                try:
                    conn = psycopg2.connect(DB_URL)
                    cursor = conn.cursor()
                    query = "INSERT INTO tbl_modalidades (nome, id_ano) VALUES (%s, %s)"
                    cursor.execute(query, (nome_modalidade, int(ano_selecionado)))
                    conn.commit()
                    st.success(f"Modalidade '{nome_modalidade}' inserida com sucesso no ano {ano_selecionado}!")
                except errors.UniqueViolation:
                    st.error(f"Erro: A modalidade '{nome_modalidade}' já existe no banco de dados para este ano.")
                except Exception as e:
                    st.error(f"Ocorreu um erro ao inserir a modalidade: {e}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()
            else:
                st.warning("Por favor, preencha o nome da modalidade e selecione um ano.")

        st.title("Modalidades Cadastradas")

        def apagar_modalidade(nome_modalidade, id_ano):
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            delete_query = "DELETE FROM tbl_modalidades WHERE nome = %s AND id_ano = %s;"
            cursor.execute(delete_query, (nome_modalidade, id_ano))
            conn.commit()
            cursor.close()
            conn.close()

        def carregar_modalidades():
            conn = psycopg2.connect(DB_URL)
            cursor = conn.cursor()
            query = 'SELECT nome, id_ano FROM tbl_modalidades;'
            cursor.execute(query)
            rows = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            cursor.close()
            conn.close()
            df = pd.DataFrame(rows, columns=colunas)
            if not df.empty:
                df["id_ano"] = df["id_ano"].apply(lambda x: int(x))
            return df

        # Se há uma modalidade a apagar no estado, apague antes de carregar os dados
        if 'delete_modalidade' in st.session_state:
            apagar_modalidade(st.session_state['delete_modalidade']['nome'],
                            st.session_state['delete_modalidade']['id_ano'])
            del st.session_state['delete_modalidade']

        df_modalidades = carregar_modalidades()

        # Filtra o DataFrame pelo ano selecionado
        if not df_modalidades.empty:
            df_filtrado = df_modalidades[df_modalidades["id_ano"] == ano_selecionado]
        else:
            df_filtrado = pd.DataFrame()

        if df_filtrado.empty:
            st.write(f"Não há modalidades cadastradas para o ano {ano_selecionado}.")
        else:
            col_tit_nome, col_tit_ano, col_tit_acao = st.columns([2,1,1])
            col_tit_nome.write("**Nome**")
            col_tit_ano.write("**Ano**")
            col_tit_acao.write("**Ação**")

            # Exibição linha a linha do df_filtrado
            for index, row in df_filtrado.iterrows():
                nome_val = row["nome"]
                ano_val = row["id_ano"]

                col_nome, col_ano, col_acao = st.columns([2,1,1])
                col_nome.write(nome_val)
                col_ano.write(ano_val)

                if col_acao.button("Apagar", key=f"apagar_{nome_val}_{ano_val}"):
                    st.session_state['delete_modalidade'] = {"nome": nome_val, "id_ano": ano_val}
