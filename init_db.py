import sqlite3


conn = sqlite3.connect('demandas.db')
cursor = conn.cursor()


cursor.execute('''
CREATE TABLE IF NOT EXISTS demandas (
    id INTEGER,
    titulo TEXT,
    descricao TEXT,
    solicitante TEXT,
    data_criacao TEXT,
    priority INTEGER DEFAULT 0
)
''')


cursor.execute('''
CREATE TABLE IF NOT EXISTS comentarios (
    id INTEGER,
    demanda_id INTEGER,
    comentario TEXT,
    autor TEXT,
    data TEXT
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT,
    email TEXT,
    senha TEXT
)
''')


cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('Admin', 'admin@example.com', 'admin123')")
cursor.execute("INSERT INTO usuarios (nome, email, senha) VALUES ('User1', 'user1@example.com', 'user123')")

cursor.execute("INSERT INTO demandas VALUES (1, 'Corrigir bug no login', 'Usuários não conseguem fazer login', 'Admin', '2024-01-15 10:30:00', 0)")
cursor.execute("INSERT INTO demandas VALUES (2, 'Implementar relatório de vendas', 'Precisamos de um relatório mensal', 'User1', '2024-01-16 14:20:00', 1)")
cursor.execute("INSERT INTO demandas VALUES (3, 'Melhorar performance', 'Sistema está lento', 'User1', '2024-01-17 09:15:00', 2)")

cursor.execute("INSERT INTO demandas VALUES (5, 'Adicionar filtros', 'Usuários querem filtrar demandas', 'User1', '2024-01-18 11:00:00', 1)")

cursor.execute("INSERT INTO comentarios VALUES (1, 1, 'Vou investigar esse bug', 'Tech Team', '2024-01-15 11:00:00')")
cursor.execute("INSERT INTO comentarios VALUES (2, 1, 'Bug corrigido na branch develop', 'Desenvolvedor', '2024-01-15 16:30:00')")
cursor.execute("INSERT INTO comentarios VALUES (3, 99, 'Este comentário está órfão', 'Usuário', '2024-01-16 10:00:00')")

conn.commit()
conn.close()

print("Banco de dados criado com sucesso!")
