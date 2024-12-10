import streamlit as st
import psycopg2
from psycopg2 import errors
from dotenv import load_dotenv
import os
import pandas as pd

load_dotenv()
DB_URL = os.getenv("DB_URL")

def show():
    st.title("Classificação")

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
        st.warning("Não há anos cadastrados. Por favor, cadastre um ano primeiro.")
        return
    else:
        ano_selecionado = st.selectbox("Selecione o ano:", anos_disponiveis)

    def carregar_modalidades(ano):
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = "SELECT id_modalidade, nome FROM tbl_modalidades WHERE id_ano = %s;"
        cursor.execute(query, (int(ano),))  # Garantir int nativo
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        modalidades = pd.DataFrame(rows, columns=["id_modalidade","nome"])
        return modalidades

    df_modalidades = carregar_modalidades(ano_selecionado)
    if df_modalidades.empty:
        st.warning("Não há modalidades cadastradas para este ano.")
        return

    modalidade_selecionada = st.selectbox("Selecione a modalidade para visualizar:", 
                                          df_modalidades["nome"].tolist())
    id_modalidade_selecionada = df_modalidades[df_modalidades["nome"] == modalidade_selecionada]["id_modalidade"].values[0]
    id_modalidade_selecionada = int(id_modalidade_selecionada)

    def carregar_jurados_especialistas(ano, modalidade):
        ano = int(ano)
        modalidade = int(modalidade)
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = """
            SELECT id_jurado 
            FROM tbl_especialistas
            WHERE id_ano = %s AND id_modalidade = %s
        """
        cursor.execute(query, (ano, modalidade))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        especialistas = [r[0] for r in rows]
        return especialistas

    def carregar_equipes_por_modalidade(modalidade):
        modalidade = int(modalidade)
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = """
            SELECT id_equipe, nome, grau 
            FROM tbl_equipes
            WHERE id_modalidade = %s
            ORDER BY grau, nome;
        """
        cursor.execute(query, (modalidade,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        df = pd.DataFrame(rows, columns=["id_equipe", "nome_equipe", "grau"])
        return df

    def carregar_participantes_por_equipe(equipe_id):
        equipe_id = int(equipe_id)
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = """
            SELECT nome
            FROM tbl_participantes
            WHERE id_equipe = %s
        """
        cursor.execute(query, (equipe_id,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        participantes = [r[0] for r in rows]
        return participantes

    def carregar_notas(ano, modalidade, equipe_id):
        ano = int(ano)
        modalidade = int(modalidade)
        equipe_id = int(equipe_id)
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        query = """
            SELECT id_jurado, id_criterio, nota
            FROM tbl_notas
            WHERE id_ano = %s AND id_modalidade = %s AND id_equipe = %s
              AND status = 'ok'
        """
        cursor.execute(query, (ano, modalidade, equipe_id))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows

    def calcular_nota_final(ano, modalidade, equipe_id):
        especialistas = carregar_jurados_especialistas(ano, modalidade)
        notas_equipe = carregar_notas(ano, modalidade, equipe_id)

        if not notas_equipe:
            return 0.0

        from collections import defaultdict
        notas_por_jurado = defaultdict(list)
        for (id_jurado, id_criterio, nota) in notas_equipe:
            notas_por_jurado[id_jurado].append(nota)

        # Calcula média de critérios por jurado
        medias_jurados = {}
        for jurado, lista_notas in notas_por_jurado.items():
            medias_jurados[jurado] = sum(lista_notas) / len(lista_notas) if len(lista_notas) > 0 else 0.0

        # Separa jurados especialistas e gerais
        especialistas = set(especialistas)  # Para otimizar pesquisa
        notas_especialistas = [m for j,m in medias_jurados.items() if j in especialistas]
        notas_gerais = [m for j,m in medias_jurados.items() if j not in especialistas]

        G = len(notas_gerais)
        E = len(notas_especialistas)

        # Média dos jurados gerais
        media_geral = sum(notas_gerais)/G if G > 0 else 0.0
        # Soma das notas dos jurados especialistas
        soma_especialistas = sum(notas_especialistas)

        # Cálculo da nota final conforme o exemplo solicitado
        nota_final = (media_geral + soma_especialistas) / (E + 1) if (E > 0 or G > 0) else 0.0

        return nota_final

    def salvar_classificacao(ano, modalidade, equipe_id, nota_final):
        ano = int(ano)
        modalidade = int(modalidade)
        equipe_id = int(equipe_id)
        conn = psycopg2.connect(DB_URL)
        cursor = conn.cursor()
        # Verifica se já existe um registro para essa combinação
        query_check = """
            SELECT id_classificacao FROM tbl_classificacoes
            WHERE id_ano = %s AND id_modalidade = %s AND id_equipe = %s
        """
        cursor.execute(query_check, (ano, modalidade, equipe_id))
        result = cursor.fetchone()
        if result:
            # Atualiza o registro existente
            query_update = """
                UPDATE tbl_classificacoes
                SET nota_final = %s
                WHERE id_classificacao = %s
            """
            cursor.execute(query_update, (float(nota_final), result[0]))
        else:
            # Insere um novo registro
            query_insert = """
                INSERT INTO tbl_classificacoes (nota_final, id_ano, id_modalidade, id_equipe)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query_insert, (float(nota_final), ano, modalidade, equipe_id))

        conn.commit()
        cursor.close()
        conn.close()

    df_equipes = carregar_equipes_por_modalidade(id_modalidade_selecionada)

    if df_equipes.empty:
        st.write("Não há equipes cadastradas para esta modalidade.")
        return

    # Calcula a nota final e salva na tabela tbl_classificacoes
    df_equipes["nota_final"] = df_equipes.apply(
        lambda row: calcular_nota_final(ano_selecionado, id_modalidade_selecionada, row["id_equipe"]), axis=1
    )

    # Salva cada nota final na tbl_classificacoes
    for _, row in df_equipes.iterrows():
        salvar_classificacao(ano_selecionado, id_modalidade_selecionada, row["id_equipe"], row["nota_final"])

    # Agora monta a estrutura de classificação
    nome_modalidade = modalidade_selecionada
    st.write(f"## Modalidade: {nome_modalidade}")

    grupos_grau = df_equipes["grau"].unique()
    for grau in grupos_grau:
        st.write(f"### Grau: {grau}")

        df_grau = df_equipes[df_equipes["grau"] == grau].copy()
        df_grau.sort_values(by="nota_final", ascending=False, inplace=True)

        for _, eq_row in df_grau.iterrows():
            equipe_nome = eq_row["nome_equipe"]
            nota_final = eq_row["nota_final"]
            participantes = carregar_participantes_por_equipe(eq_row["id_equipe"])

            st.write(f"**{equipe_nome}** - Nota: {nota_final:.3f}")
            for p in participantes:
                st.write(f"- {p}")
            st.write("---")
