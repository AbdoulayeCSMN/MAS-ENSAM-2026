$env:PYTHONPATH = "C:\Users\Alif computer\Desktop\projet technologie web\agentIA\MultiAgentSecurite\src"
python -c "import sys; sys.path.insert(0, 'src'); from api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)"


pour lance ron peut aussi utiliser cela :


python -c "import sys; sys.path.insert(0, 'src'); from api import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=8000, reload=False)"




Accédez à votre API :
Swagger UI (documentation interactive) : http://127.0.0.1:8000/docs

Redoc (documentation alternative) : http://127.0.0.1:8000/redoc

Endpoint de scan : POST http://127.0.0.1:8000/scan

Endpoint rapports : GET http://127.0.0.1:8000/reports/{scan_id}

Endpoint patches : POST http://127.0.0.1:8000/reports/{scan_id}/apply

Pour tester avec un projet qui a des vulnérabilités :