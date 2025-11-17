import json
import os
from datetime import datetime

# Lista de GPTs personalizados conocidos
gpts_personalizados = [
    ("VS Code Github", "https://chatgpt.com/g/g-p-678aca4bde1081918b303cfa0dbe0949-vs-code-github/project"),
    ("ChatBeto", "https://chatgpt.com/g/g-p-68881bc5647c8191ba11903043f95ce9-chatbeto/project"),
    ("Xubuntu", "https://chatgpt.com/g/g-p-67bb710a9e348191bde6345e3c43f16d-xubuntu/project"),
    ("Fiverr-Alejandro", "https://chatgpt.com/g/g-p-689a08ad26488191965825aff4f517fe-fiverr-alejandro/project"),
    ("ChatGPT", "https://chatgpt.com/g/g-p-680ce62f83148191b2dca207e85e0e99-chatgpt/project"),
    ("Galaxy S7 FE", "https://chatgpt.com/g/g-p-6884f2e91d40819197318fa3ae3ef1f3-galaxy-s7-fe/project"),
    ("Medios Audiovisuales", "https://chatgpt.com/g/g-p-67eba26c610881918650a47d2f907173-medios-audiovisuales/project"),
    ("Profesor Proyectual UNA", "https://chatgpt.com/g/g-p-67ab14a8231c819181c69d9472e718a0-profesor-proyectual-una/project"),
    ("Contabo", "https://chatgpt.com/g/g-p-6853e990af508191adb81fa2be23ca08-contabo/project"),
    ("Lenguaje Visual", "https://chatgpt.com/g/g-p-681b4c1d7c50819193aa3bbebfac1669-lenguaje-visual/project")
]

print("🤖 Extractor de Proyectos ChatGPT")
print("=" * 50)

# Mostrar GPTs personalizados
print(f"\n🎯 GPTs Personalizados ({len(gpts_personalizados)}):")
for i, (titulo, url) in enumerate(gpts_personalizados, 1):
    print(f"{i:2}. {titulo} → {url}")

# Intentar leer conversations.json si existe
archivo_conversations = "/home/beto/Documentos/Github/chatBeto/chatBETO/extracted/conversations.json"
conversaciones_encontradas = 0

if os.path.exists(archivo_conversations):
    print(f"\n🔍 Leyendo conversations.json...")
    try:
        with open(archivo_conversations, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if isinstance(data, list):
            conversaciones_encontradas = len(data)
        else:
            conversaciones_encontradas = len(data.get("conversations", []))
        
        print(f"💬 Conversaciones encontradas: {conversaciones_encontradas}")
    except Exception as e:
        print(f"❌ Error al leer conversations.json: {e}")
else:
    print(f"\n📁 No se encontró {archivo_conversations}")

print(f"\n📊 Resumen:")
print(f"   📦 GPTs Personalizados: {len(gpts_personalizados)}")
print(f"   💬 Conversaciones: {conversaciones_encontradas}")
print(f"   📈 Total: {len(gpts_personalizados) + conversaciones_encontradas}")

# Preguntar si quiere guardar en Markdown
print(f"\n📄 ¿Quieres guardar los GPTs en un archivo Markdown? (s/N): ", end="")
respuesta = input().lower().strip()

if respuesta in ['s', 'si', 'sí', 'y', 'yes']:
    # Crear archivo Markdown
    markdown_file = "gpts_personalizados.md"
    fecha_actual = datetime.now().strftime("%d de %B de %Y a las %H:%M")
    
    with open(markdown_file, "w", encoding="utf-8") as md:
        md.write(f"# 🤖 GPTs Personalizados de ChatGPT\n\n")
        md.write(f"**Generado el:** {fecha_actual}\n")
        md.write(f"**Total de GPTs:** {len(gpts_personalizados)}\n\n")
        md.write("---\n\n")
        
        for i, (titulo, url) in enumerate(gpts_personalizados, 1):
            md.write(f"{i}. **{titulo}**\n")
            md.write(f"   - 🔗 [Abrir GPT]({url})\n\n")
    
    print(f"✅ Archivo guardado como: {markdown_file}")
    print(f"📂 Ubicación: {os.path.abspath(markdown_file)}")
else:
    print("👍 No se guardó archivo Markdown.")

print(f"\n🎉 ¡Proceso completado!")
