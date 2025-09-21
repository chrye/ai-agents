python -m venv labenv
.\labenv\Scripts\activate.ps1

pip install -r requirements.txt azure-ai-projects

.\runAzLogin.ps1

python agent_triage.py
