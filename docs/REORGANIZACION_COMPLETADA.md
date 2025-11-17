# 📁 Nueva Estructura de Directorios - chatBETO

## ✅ Reorganización Completada

**🗂️ ANTES:** 150+ archivos en directorio raíz  
**🗂️ AHORA:** Estructura organizada por funcionalidad

### 📂 Nueva Estructura:

```
chatBETO/
├── 📁 web/                    # Frontend (5 archivos)
├── 📁 api/                    # APIs PHP (11 archivos)
├── 📁 scripts/               
│   ├── node/                 # Scripts JavaScript (8 archivos)
│   ├── python/               # Scripts Python (39 archivos)
│   ├── puppeteer/            # Automatización (17 archivos)
│   └── legacy/               # Scripts obsoletos (13 archivos)
├── 📁 database/              # BD config/schemas (7 archivos)
├── 📁 config/                # Configuraciones (4 archivos)
├── 📁 docs/                  # Documentación (10 archivos)
├── 📁 data/
│   ├── exports/              # Exports ChatGPT
│   ├── json/                 # Archivos JSON (9 archivos)
│   ├── logs/                 # Logs/screenshots (25 archivos)
│   └── screenshots/          # Screenshots debug
└── 📁 tests/                 # Tests (7 archivos)
```

## 🔧 PRÓXIMOS PASOS REQUERIDOS:

### 1. Actualizar servidor web XAMPP:
```bash
sudo cp web/* /opt/lampp/htdocs/chatBETO/
sudo cp api/* /opt/lampp/htdocs/chatBETO/api/
sudo cp database/db_connection.php /opt/lampp/htdocs/chatBETO/
```

### 2. Actualizar rutas en archivos HTML:
- `web/index.html`: Cambiar rutas de API a `api/`
- `web/estadisticas.html`: Actualizar rutas

### 3. Actualizar includes en archivos PHP:
- APIs ahora deben apuntar a `../database/db_connection.php`

## 📈 BENEFICIOS LOGRADOS:

✅ **Navegación clara** - Cada tipo de archivo en su lugar  
✅ **Mejor mantenimiento** - Estructura profesional  
✅ **Seguridad mejorada** - Configs sensibles protegidas  
✅ **Legacy preservado** - Scripts antiguos accesibles  
✅ **Escalabilidad** - Fácil agregar nuevos archivos