import mysql.connector
from datetime import datetime

def connect_to_db():
    """Conectar a la base de datos"""
    return mysql.connector.connect(
        host='sv46.byethost46.org',
        user='iunaorg_b3toh',
        password='elgeneral2018',
        database='iunaorg_chatBeto'
    )

def create_projects_table():
    """Crear tabla projects"""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Crear tabla projects
    create_table_query = """
    CREATE TABLE IF NOT EXISTS projects (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL UNIQUE,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        conversation_count INT DEFAULT 0,
        INDEX idx_name (name)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
    """
    
    cursor.execute(create_table_query)
    print("✅ Tabla 'projects' creada correctamente")
    
    # Insertar proyectos únicos desde conversations
    insert_projects_query = """
    INSERT IGNORE INTO projects (name, description, conversation_count)
    SELECT 
        project_name as name,
        CONCAT('Categoría: ', project_name) as description,
        COUNT(*) as conversation_count
    FROM conversations 
    WHERE project_name IS NOT NULL 
    GROUP BY project_name
    """
    
    cursor.execute(insert_projects_query)
    projects_inserted = cursor.rowcount
    print(f"✅ {projects_inserted} proyectos únicos insertados")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return projects_inserted

def add_project_id_to_conversations():
    """Agregar columna project_id a conversations y actualizar referencias"""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    # Verificar si la columna ya existe
    cursor.execute("""
        SELECT COUNT(*) 
        FROM information_schema.COLUMNS 
        WHERE TABLE_SCHEMA = 'iunaorg_chatBeto' 
        AND TABLE_NAME = 'conversations' 
        AND COLUMN_NAME = 'project_id'
    """)
    
    if cursor.fetchone()[0] == 0:
        # Agregar columna project_id
        cursor.execute("""
            ALTER TABLE conversations 
            ADD COLUMN project_id INT,
            ADD INDEX idx_project_id (project_id),
            ADD FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
        """)
        print("✅ Columna project_id agregada a conversations")
    else:
        print("ℹ️  Columna project_id ya existe")
    
    # Actualizar project_id basado en project_name
    update_query = """
    UPDATE conversations c 
    INNER JOIN projects p ON c.project_name = p.name 
    SET c.project_id = p.id 
    WHERE c.project_name IS NOT NULL
    """
    
    cursor.execute(update_query)
    updated_rows = cursor.rowcount
    print(f"✅ {updated_rows} conversaciones actualizadas con project_id")
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return updated_rows

def verify_normalization():
    """Verificar que la normalización fue exitosa"""
    conn = connect_to_db()
    cursor = conn.cursor()
    
    print("\n📊 Verificación de la normalización:")
    
    # Contar proyectos
    cursor.execute("SELECT COUNT(*) FROM projects")
    total_projects = cursor.fetchone()[0]
    print(f"Total de proyectos: {total_projects}")
    
    # Contar conversaciones con project_id
    cursor.execute("SELECT COUNT(*) FROM conversations WHERE project_id IS NOT NULL")
    conversations_with_project = cursor.fetchone()[0]
    print(f"Conversaciones con project_id: {conversations_with_project}")
    
    # Mostrar proyectos con su conteo
    cursor.execute("""
        SELECT p.id, p.name, p.conversation_count, COUNT(c.conversation_id) as actual_count
        FROM projects p
        LEFT JOIN conversations c ON p.id = c.project_id
        GROUP BY p.id, p.name, p.conversation_count
        ORDER BY actual_count DESC
        LIMIT 10
    """)
    
    print("\nTop 10 proyectos:")
    for row in cursor.fetchall():
        project_id, name, stored_count, actual_count = row
        print(f"  {project_id}: {name} (Almacenado: {stored_count}, Real: {actual_count})")
    
    # Verificar integridad referencial
    cursor.execute("""
        SELECT COUNT(*) 
        FROM conversations 
        WHERE project_name IS NOT NULL AND project_id IS NULL
    """)
    orphaned_conversations = cursor.fetchone()[0]
    
    if orphaned_conversations > 0:
        print(f"⚠️  {orphaned_conversations} conversaciones sin project_id pero con project_name")
    else:
        print("✅ Todas las conversaciones tienen su project_id correctamente asignado")
    
    cursor.close()
    conn.close()

def main():
    print("🚀 Iniciando normalización de base de datos...")
    print("Estructura: PROYECTO → CONVERSACIÓN → MENSAJE\n")
    
    try:
        # Paso 1: Crear tabla projects
        print("Paso 1: Creando tabla projects")
        projects_count = create_projects_table()
        
        # Paso 2: Agregar project_id a conversations
        print("\nPaso 2: Normalizando tabla conversations")
        updated_count = add_project_id_to_conversations()
        
        # Paso 3: Verificar resultados
        verify_normalization()
        
        print(f"\n🎉 ¡Normalización completada exitosamente!")
        print(f"   - {projects_count} proyectos creados")
        print(f"   - {updated_count} conversaciones normalizadas")
        print("\n💡 Ahora puedes usar filtros por proyecto en las búsquedas")
        
    except Exception as e:
        print(f"❌ Error durante la normalización: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    main()