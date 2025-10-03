python -m venv labenv
.\labenv\Scripts\activate.ps1

pip install -r requirements.txt azure-ai-projects mcp

.\runAzLogin.ps1

python client.py
