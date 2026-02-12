# {PROJECT_NAME} Expert

## Quick Start

cp .env.example .env
docker-compose up -d
pip install -r requirements.txt
python scripts/init_db.py
streamlit run interfaces/streamlit_app.py

## Structure

agents/         - AI agents
core/          - Database and embeddings
interfaces/    - User interfaces
knowledge/     - Documentation
scripts/       - Setup tools
logs/          - Application logs
postgres_data/ - Database files