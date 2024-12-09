import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

# Carrega as variáveis de ambiente
load_dotenv()
DB_URL = os.getenv("DB_URL")

def show():
    st.write("# Cadastro de Critérios")

    # Função para carregar anos disponíveis
    def carregar_anos():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id_ano FROM tbl_anos ORDER BY id_ano;')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        anos = [r[0] for r in rows]
        return anos

    # Função para carregar modalidades por ano
    def carregar_modalidades_por_ano(ano):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id_modalidade, nome FROM tbl_modalidades WHERE id_ano = %s ORDER BY nome;', (ano,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows  # Retorna uma lista de tuplas: (id_modalidade, nome)

    # Função para carregar critérios
    def carregar_criterios():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = 'SELECT id_criterio, nome, id_modalidade FROM tbl_criterios;'
        cursor.execute(query)
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows, columns=colunas)
        return df

    # Função para apagar critério
    def apagar_criterio(id_criterio):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        delete_query = "DELETE FROM tbl_criterios WHERE id_criterio = %s;"
        cursor.execute(delete_query, (id_criterio,))
        conn.commit()
        cursor.close()
        conn.close()

    # Inicializa um contador para o form key, para resetar o formulário
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    # Carregar anos disponíveis
    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar critérios.")
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar critérios:", anos_disponiveis)

        # Carregar modalidades para o ano selecionado
        modalidades = carregar_modalidades_por_ano(ano_selecionado)
        if not modalidades:
            st.warning("Não há modalidades cadastradas para o ano selecionado. Cadastre uma modalidade primeiro.")
        else:
            # Criar dicionário de modalidade para fácil acesso
            modalidade_dict = {nome: mid for (mid, nome) in modalidades}
            modalidade_nomes = list(modalidade_dict.keys())

            # Combobox para selecionar modalidade
            modalidade_selecionada_nome = st.selectbox("Selecione a modalidade:", modalidade_nomes)
            id_modalidade_selecionada = modalidade_dict[modalidade_selecionada_nome]

            # Formulário para cadastrar critério
            form_key = f'form_cadastro_criterio_{st.session_state["form_counter"]}'
            with st.form(key=form_key):
                st.write("### Cadastrar Critério")
                nome_criterio = st.text_input("Nome do critério:")
                submit_button = st.form_submit_button(label='Salvar Critério')

                if submit_button:
                    if nome_criterio and id_modalidade_selecionada:
                        try:
                            conn = psycopg2.connect(DB_URL)
                            cursor = conn.cursor()
                            query = "INSERT INTO tbl_criterios (nome, id_modalidade) VALUES (%s, %s)"
                            cursor.execute(query, (nome_criterio, id_modalidade_selecionada))
                            conn.commit()
                            st.success(f"Critério '{nome_criterio}' inserido com sucesso na modalidade '{modalidade_selecionada_nome}'!")

                            # Incrementar o contador para resetar o formulário
                            st.session_state['form_counter'] += 1
                        except errors.UniqueViolation:
                            st.error(f"Erro: O critério '{nome_criterio}' já existe nesta modalidade.")
                        except Exception as e:
                            st.error(f"Ocorreu um erro ao inserir o critério: {e}")
                        finally:
                            if cursor:
                                cursor.close()
                            if conn:
                                conn.close()
                    else:
                        st.warning("Por favor, preencha o nome do critério.")

            st.title("Critérios Cadastrados")

            # Apagar critério se houver
            if 'delete_criterio' in st.session_state:
                apagar_criterio(st.session_state['delete_criterio']['id_criterio'])
                del st.session_state['delete_criterio']
                # Incrementar o contador para atualizar a lista
                st.session_state['form_counter'] += 1

            # Carregar critérios
            df_criterios = carregar_criterios()

            # Filtrar critérios pela modalidade selecionada
            df_filtrado = df_criterios[df_criterios["id_modalidade"] == id_modalidade_selecionada]

            if df_filtrado.empty:
                st.write(f"Não há critérios cadastrados para a modalidade '{modalidade_selecionada_nome}'.")
            else:
                # Cabeçalhos da tabela
                col_tit_nome, col_tit_modalidade, col_tit_acao = st.columns([3,2,1])
                col_tit_nome.write("**Nome**")
                col_tit_modalidade.write("**Modalidade**")
                col_tit_acao.write("**Ação**")

                # Exibir critérios
                for index, row in df_filtrado.iterrows():
                    id_criterio_val = row["id_criterio"]
                    nome_val = row["nome"]
                    id_modalidade_val = row["id_modalidade"]

                    # Obter o nome da modalidade a partir do id_modalidade
                    nome_modalidade_val = [nome for nome, mid in modalidade_dict.items() if mid == id_modalidade_val]
                    nome_modalidade_val = nome_modalidade_val[0] if nome_modalidade_val else "Desconhecida"

                    col_nome, col_modalidade, col_acao = st.columns([3,2,1])
                    col_nome.write(nome_val)
                    col_modalidade.write(nome_modalidade_val)

                    if col_acao.button("Apagar", key=f"apagar_{id_criterio_val}"):
                        st.session_state['delete_criterio'] = {"id_criterio": id_criterio_val}
