import sqlite3

conn = sqlite3.connect('demandas.db')
cursor = conn.cursor()

print("Iniciando migração do banco...")

# -------------------------------------------------
# 1. Verifica se a tabela usuarios existe
# -------------------------------------------------

tabela_usuarios = cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type='table' AND name='usuarios'
""").fetchone()

if tabela_usuarios is None:

    print("Tabela 'usuarios' não existe. Criando...")

    cursor.execute("""
        CREATE TABLE usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            email TEXT,
            senha TEXT
        )
    """)

    print("Tabela 'usuarios' criada.")


# -------------------------------------------------
# 2. Verifica se usuario_id já existe em demandas
# -------------------------------------------------

colunas = cursor.execute(
    "PRAGMA table_info(demandas)"
).fetchall()

nomes_colunas = [coluna[1] for coluna in colunas]

if 'usuario_id' not in nomes_colunas:

    print("Criando coluna 'usuario_id'...")

    cursor.execute("""
        ALTER TABLE demandas
        ADD COLUMN usuario_id INTEGER
    """)

    print("Coluna 'usuario_id' criada.")

else:

    print("Coluna 'usuario_id' já existe.")


# -------------------------------------------------
# 3. Cria usuários a partir dos solicitantes antigos
# -------------------------------------------------

solicitantes = cursor.execute("""
    SELECT DISTINCT solicitante
    FROM demandas
    WHERE solicitante IS NOT NULL
      AND TRIM(solicitante) != ''
""").fetchall()

for solicitante in solicitantes:

    nome = solicitante[0]

    usuario = cursor.execute("""
        SELECT id
        FROM usuarios
        WHERE nome = ?
    """, (nome,)).fetchone()

    if usuario is None:

        cursor.execute("""
            INSERT INTO usuarios (nome, email, senha)
            VALUES (?, '', '')
        """, (nome,))

        print(f"Usuário criado: {nome}")


# -------------------------------------------------
# 4. Relaciona as demandas antigas aos usuários
# -------------------------------------------------

cursor.execute("""
    UPDATE demandas
    SET usuario_id = (
        SELECT usuarios.id
        FROM usuarios
        WHERE usuarios.nome = demandas.solicitante
    )
    WHERE usuario_id IS NULL
""")


# -------------------------------------------------
# 5. Mostra o resultado da migração
# -------------------------------------------------

demandas = cursor.execute("""
    SELECT
        demandas.id,
        demandas.solicitante,
        demandas.usuario_id,
        usuarios.nome
    FROM demandas
    LEFT JOIN usuarios
        ON demandas.usuario_id = usuarios.id
""").fetchall()

print()
print("Resultado da migração:")
print("--------------------------------")

for demanda in demandas:
    print(
        f"Demanda {demanda[0]}: "
        f"{demanda[1]} -> "
        f"usuario_id={demanda[2]} -> "
        f"{demanda[3]}"
    )


conn.commit()
conn.close()

print()
print("Migração concluída com sucesso!")