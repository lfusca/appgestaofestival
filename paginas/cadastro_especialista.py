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
    
    st.write("# Cadastro de Especialistas")

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

    # Função para carregar jurados
    def carregar_jurados():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        cursor.execute('SELECT id_jurado, nome FROM tbl_jurados ORDER BY nome;')
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows  # Retorna uma lista de tuplas: (id_jurado, nome)

    # Função para carregar especialistas
    def carregar_especialistas():
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = '''
            SELECT e.id_ano, e.id_jurado, e.id_modalidade, j.nome AS nome_jurado, m.nome AS nome_modalidade, a.id_ano AS ano
            FROM tbl_especialistas e
            JOIN tbl_jurados j ON e.id_jurado = j.id_jurado
            JOIN tbl_modalidades m ON e.id_modalidade = m.id_modalidade
            JOIN tbl_anos a ON e.id_ano = a.id_ano
            ORDER BY e.id_ano, e.id_jurado, e.id_modalidade;
        '''
        cursor.execute(query)
        rows = cursor.fetchall()
        colunas = [desc[0] for desc in cursor.description]
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows, columns=colunas)
        return df

    # Função para apagar especialista
    def apagar_especialista(id_ano, id_jurado, id_modalidade):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        delete_query = "DELETE FROM tbl_especialistas WHERE id_ano = %s AND id_jurado = %s AND id_modalidade = %s;"
        cursor.execute(delete_query, (id_ano, id_jurado, id_modalidade))
        conn.commit()
        cursor.close()
        conn.close()

    # Inicializa um contador para o form key, para resetar o formulário
    if 'form_counter' not in st.session_state:
        st.session_state['form_counter'] = 0

    # Carregar anos disponíveis
    anos_disponiveis = carregar_anos()

    if not anos_disponiveis:
        st.warning("Não há anos cadastrados. Cadastre um ano primeiro para poder cadastrar especialistas.")
    else:
        # Combobox para selecionar o ano
        ano_selecionado = st.selectbox("Selecione o ano para cadastrar e visualizar especialistas:", anos_disponiveis)

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

            # Carregar jurados
            jurados = carregar_jurados()
            if not jurados:
                st.warning("Não há jurados cadastrados. Cadastre um jurado primeiro para poder cadastrar especialistas.")
            else:
                # Criar dicionário de jurado para fácil acesso
                jurado_dict = {nome: jid for (jid, nome) in jurados}
                jurado_nomes = list(jurado_dict.keys())

                # Combobox para selecionar jurado
                jurado_selecionado_nome = st.selectbox("Selecione o jurado:", jurado_nomes)
                id_jurado_selecionado = jurado_dict[jurado_selecionado_nome]

                # Formulário para cadastrar especialista
                form_key = f'form_cadastro_especialista_{st.session_state["form_counter"]}'
                with st.form(key=form_key):
                    st.write("### Cadastrar Especialista")
                    # Como todos os dados vêm de comboboxes, não há campos de texto para digitação
                    # Apenas o botão de submissão
                    submit_button = st.form_submit_button(label='Salvar Especialista')

                    if submit_button:
                        # Validar se todas as seleções foram feitas
                        if ano_selecionado and id_modalidade_selecionada and id_jurado_selecionado:
                            try:
                                conn = psycopg2.connect(DB_URL)
                                cursor = conn.cursor()
                                # Inserir o especialista com os IDs selecionados
                                query = "INSERT INTO tbl_especialistas (id_ano, id_jurado, id_modalidade) VALUES (%s, %s, %s)"
                                cursor.execute(query, (ano_selecionado, id_jurado_selecionado, id_modalidade_selecionada))
                                conn.commit()
                                st.success(f"Especialista cadastrado com sucesso na modalidade '{modalidade_selecionada_nome}'!")
                                
                                # Incrementar o contador para resetar o formulário
                                st.session_state['form_counter'] += 1
                            except errors.UniqueViolation:
                                st.error("Erro: Este especialista já está cadastrado na combinação selecionada de Ano, Jurado e Modalidade.")
                            except Exception as e:
                                st.error(f"Ocorreu um erro ao inserir o especialista: {e}")
                            finally:
                                if cursor:
                                    cursor.close()
                                if conn:
                                    conn.close()
                        else:
                            st.warning("Por favor, selecione todas as opções.")

                st.markdown("---")
                st.title("Especialistas Cadastrados")

                # Apagar especialista se houver
                if 'delete_especialista' in st.session_state:
                    apagar_especialista(
                        st.session_state['delete_especialista']['id_ano'],
                        st.session_state['delete_especialista']['id_jurado'],
                        st.session_state['delete_especialista']['id_modalidade']
                    )
                    del st.session_state['delete_especialista']
                    # Incrementar o contador para atualizar a lista
                    st.session_state['form_counter'] += 1

                # Carregar especialistas
                df_especialistas = carregar_especialistas()

                # Filtrar especialistas pela seleção atual
                df_filtrado = df_especialistas[
                    (df_especialistas["id_ano"] == ano_selecionado) &
                    (df_especialistas["id_modalidade"] == id_modalidade_selecionada)
                ]

                if df_filtrado.empty:
                    st.write(f"Não há especialistas cadastrados para a modalidade '{modalidade_selecionada_nome}'.")
                else:
                    # Cabeçalhos da tabela
                    col_tit_ano, col_tit_jurado, col_tit_modalidade, col_tit_acao = st.columns([2,3,3,1])
                    col_tit_ano.write("**Ano**")
                    col_tit_jurado.write("**Jurado**")
                    col_tit_modalidade.write("**Modalidade**")
                    col_tit_acao.write("**Ação**")

                    # Exibir especialistas
                    for index, row in df_filtrado.iterrows():
                        id_ano_val = row["id_ano"]
                        id_jurado_val = row["id_jurado"]
                        id_modalidade_val = row["id_modalidade"]
                        nome_jurado_val = row["nome_jurado"]
                        nome_modalidade_val = row["nome_modalidade"]

                        # Chave única para o botão de apagar baseada nos três IDs
                        button_key = f"apagar_{id_ano_val}_{id_jurado_val}_{id_modalidade_val}"

                        col_ano, col_jurado, col_modalidade, col_acao = st.columns([2,3,3,1])
                        col_ano.write(f"{id_ano_val}")
                        col_jurado.write(nome_jurado_val)
                        col_modalidade.write(nome_modalidade_val)

                        if col_acao.button("Apagar", key=button_key):
                            st.session_state['delete_especialista'] = {
                                "id_ano": id_ano_val,
                                "id_jurado": id_jurado_val,
                                "id_modalidade": id_modalidade_val
                            }
