from sqlalchemy import create_engine, text

engine = create_engine("postgresql://postgres:postgres@localhost:5432/postgres")

with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS test_embeddings (
            id serial PRIMARY KEY,
            content text,
            embedding vector(3)
        )
    """))

    conn.execute(text("""
        INSERT INTO test_embeddings (content, embedding) VALUES
        ('documento a', '[0.1, 0.2, 0.3]'),
        ('documento b', '[0.4, 0.5, 0.6]'),
        ('documento c', '[0.9, 0.1, 0.2]')
    """))
    conn.commit()

    result = conn.execute(text("""
        SELECT content, embedding <=> '[0.1, 0.2, 0.3]' AS distancia
        FROM test_embeddings
        ORDER BY distancia
        LIMIT 2
    """))

    for row in result:
        print(row)

print("pgvector OK ")