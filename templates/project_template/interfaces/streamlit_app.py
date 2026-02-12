import streamlit as st
import sys
import os
import yaml
import asyncio
from pathlib import Path

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

config_path = Path(__file__).parent.parent / 'configs' / 'project.yaml'
with open(config_path, 'r') as f:
    config = yaml.safe_load(f)

st.set_page_config(
    page_title=config['ui']['page_title'],
    page_icon=config['ui']['page_icon'],
    layout='centered'
)

st.title(f"{config['ui']['page_icon']} {config['project']['name']}")

from agents.base import BaseAgent
from controllers.controller import Controller
from memory.memory import Memory
from tools import DatabaseTool, WebTool

if 'controller' not in st.session_state:
    agent = BaseAgent(
        name='expert',
        system_prompt=f"You are an expert in {config['project']['name']}. Provide clear, accurate, and helpful responses.",
        config=config['agent']
    )
    memory = Memory(
        namespace=config['memory']['namespace'],
        config=config['memory']
    )
    tools = {
        'db': DatabaseTool(),
        'web': WebTool()
    }
    st.session_state.controller = Controller(agent, memory, tools, config)

if 'messages' not in st.session_state:
    st.session_state.messages = []

def run_async(coro):
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        return loop.run_until_complete(coro)
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return f"An error occurred: {str(e)}"

for message in st.session_state.messages:
    with st.chat_message(message['role']):
        st.markdown(message['content'])

if prompt := st.chat_input('Ask me anything...'):
    st.session_state.messages.append({'role': 'user', 'content': prompt})
    with st.chat_message('user'):
        st.markdown(prompt)
    
    with st.chat_message('assistant'):
        with st.spinner('Thinking...'):
            response = run_async(
                st.session_state.controller.process_query(prompt)
            )
            st.markdown(response)
            st.session_state.messages.append(
                {'role': 'assistant', 'content': response}
            )