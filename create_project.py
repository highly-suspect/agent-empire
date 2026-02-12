import os
import shutil
import sys

def create_project(domain, port=54322):
    home = os.path.expanduser("~")
    project_name = f"{domain}-expert"
    project_path = f"{home}/agents/projects/{project_name}"
    template_path = f"{home}/agents/templates/project_template"
    
    print(f"Creating {project_name} on port {port}")
    
    if not os.path.exists(template_path):
        print(f"Error: Template not found at {template_path}")
        sys.exit(1)
    
    os.makedirs(f"{home}/agents/projects", exist_ok=True)
    shutil.copytree(template_path, project_path)
    
    shutil.copy(
        f"{project_path}/.env.example",
        f"{project_path}/.env"
    )
    
    with open(f"{project_path}/.env", 'r') as f:
        env_content = f.read()
    
    env_content = env_content.replace('your_project_name', domain)
    env_content = env_content.replace('54322', str(port))
    env_content = env_content.replace('${PORT}', str(port))
    env_content = env_content.replace('${PROJECT_NAME}', domain)
    
    with open(f"{project_path}/.env", 'w') as f:
        f.write(env_content)
    
    with open(f"{project_path}/README.md", 'r') as f:
        readme = f.read()
    readme = readme.replace('{PROJECT_NAME}', domain.title())
    with open(f"{project_path}/README.md", 'w') as f:
        f.write(readme)
    
    config_path = f"{project_path}/configs/project.yaml"
    with open(config_path, 'r') as f:
        config = f.read()
    config = config.replace('${PROJECT_NAME}', domain)
    with open(config_path, 'w') as f:
        f.write(config)
    
    os.makedirs(f"{project_path}/postgres_data", exist_ok=True)
    os.makedirs(f"{project_path}/knowledge", exist_ok=True)
    os.makedirs(f"{project_path}/knowledge/memory", exist_ok=True)
    os.makedirs(f"{project_path}/logs", exist_ok=True)
    
    print(f"Project created at: {project_path}")
    print("\nNEXT STEPS:")
    print(f"  cd ~/agents/projects/{project_name}")
    print("  # Add your OpenAI API key to .env")
    print("  docker-compose up -d")
    print("  pip install -r requirements.txt")
    print("  python scripts/init_db.py")
    print("  streamlit run interfaces/streamlit_app.py")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python create_project.py <domain> [port]")
        print("Example: python create_project.py pinescript 54322")
        print("Example: python create_project.py python 54323")
        sys.exit(1)
    
    domain = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 54322
    create_project(domain, port)