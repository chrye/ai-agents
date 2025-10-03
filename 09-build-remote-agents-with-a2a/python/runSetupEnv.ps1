python -m venv labenv
.\labenv\Scripts\activate.ps1

pip install -r requirements.txt azure-ai-projects a2a-sdk

.\runAzLogin.ps1

python run_all.py
