# Prueba Técnica Backend

## Instalación

1. Crear entorno virtual:
```
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
deactivate # desactivar el entorno virtual
```

2. Instalar dependencias (Cualquiera de las 2 opciones):
```
pip install -r requirements.txt
pip install fastapi uvicorn pyjwt pydantic pymongo python-dotenv
```

3. Ejecutar:
```
uvicorn main:app --reload --port 8080
```

4. Documentación Swagger:
http://localhost:8080/docs

## Credenciales de prueba
- Username: admin
- Password: 1234
