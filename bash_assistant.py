import streamlit as st
from llama_index.agent.openai import OpenAIAgent
from llama_index.llms.openai import OpenAI
from llama_index.core.tools import BaseTool, FunctionTool
import subprocess
import os
import json

from dotenv import load_dotenv

load_dotenv()

system_prompt = """You are an expert in linux bash commands, you help the user in troubleshooting or fetching deails from the system based on the user query. 
Make sure that you understand the user query and form a STEP BY STEP plan of how you would answer the question.
Use the `run_command` function tool execute bash commands and get the response. 
Analyse the response to answer the user questions. 
You can use the tool as many times as needed in order to answer the question. 

RULES:
- Never execute harmful commands. 
- Never delete anything, shutdown or restart the system. Do not install anything or change anything on the system.
- Respond that you will not be able to do it if user askes you to perform anything that changes data in the system. 
"""

SUGGESTED_QUESTIONS = """
You can ask me, 
1. Find and display the process that is consuming the maximum CPU or memory resources.
2. Show me the pods that are currently not running in the Kubernetes cluster. Try to troubleshoot why the pods are not running.
3. Please list the top 10 largest files in the directory `/path/to/directory`.
4. Create a backup of the directory `/path/to/directory` and its contents.
5. find all files modified within the last 24 hours in the directory `/path/to/directory`.
"""

def is_command_harmful(command):
    harmful_keywords = [
        'rm', 'rm -rf', 'rm -r', 'rm --recursive', 'rm --force', 'rm -d', 'rmdir', 'rmdir --ignore-fail-on-non-empty',
        'unlink', 'shred', 'wipe',
        'mkfs', 'mkfs.ext4', 'mkfs.btrfs', 'mkfs.xfs', 'mkfs.vfat',
        'dd', 'dd if=', 'dd of=',
        ':(){ :|:& };:',
        'chmod', 'chmod 777', 'chmod -R', 'chmod --recursive', 'chmod --mode=777',
        'chown', 'chown -R', 'chown --recursive',
        'shutdown', 'shutdown -h', 'shutdown --halt', 'shutdown -r', 'shutdown --reboot', 'reboot', 'poweroff', 'init 0', 'init 6',
        'kill -9', 'killall', 'kill --signal 9', 'pkill',
        'wget', 'curl', 'nc -l', 'nc --listen', 'netcat -l',
        '| sh', '| bash', '| /bin/sh', '| /bin/bash', '| ksh', '| zsh', '| csh',
        '>', '>>', '1>', '2>', '&>', '>|', '2>&1',
        'iptables -F', 'iptables --flush', 'ufw reset', 'firewalld --reload',
        '/dev/null', '/dev/zero', '/dev/random', '/dev/sda', '/dev/sdb', '/dev/nvme',
        '/etc/passwd', '/etc/shadow', '/etc/group', '/etc/gshadow',
        'crontab -r', 'crontab --remove', 'crontab -d', 'crontab --delete',
        'systemctl stop', 'systemctl disable', 'systemctl mask',
        'echo', 'echo >', 'echo >>', ': >', 'cat >', 'cat >>',
        '`rm -rf`', '$(rm -rf)', '`mkfs`', '$(mkfs)',
        'ifconfig', 'route', 'ip link set', 'ip link delete',
        'mount', 'umount', 'mount -o remount,rw', 'mount -o remount,ro',
        'mv', 'mv -f', 'mv -i', 'mv --force', 'mv --interactive', 'rsync', 'cp -r', 'cp --recursive',
        'mv /', 'mv /*', 'mv /etc', 'mv /home', 'mv /usr', 'mv /bin', 'mv /sbin', 'mv /var', 'mv /lib', 'mv /opt'
    ]
    
    for keyword in harmful_keywords:
        if keyword in command:
            return True
    return False

def run_command(command):
    """Execute a command and capture the output.

    This function executes the given command using the `subprocess.run` method with shell=True.
    It captures the output of the command and returns it as a string.

    Example commands:
    1) "cd test_folder && pwd"
    2) "ls -l"
    3) "docker ps"

    Parameters
    ----------
    command : str
        The command to be executed.

    Returns
    -------
    str
        The output of the command.
    """
    if is_command_harmful(command):
        return f"you are not allowed to run `{command}`"
    
    response = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=3)
    return response.stderr.strip() + "\n" + response.stdout.strip()

def shell_agent():
    command_tool = FunctionTool.from_defaults(fn=run_command)

    llm = OpenAI(model="gpt-3.5-turbo-1106")
    agent = OpenAIAgent.from_tools(
        [command_tool], llm=llm, verbose=True, system_prompt=system_prompt
    )
    return agent


def process_query(agent: OpenAIAgent, prompt: str, history=None):

    response = agent.chat(prompt, chat_history=history)

    return str(response)


def process_memory(memory):
    output = ""
    for _message in memory:
        # if _message.role == "user":
        #     # output += f"#### User:\n{_message.content}\n\n"
        #     pass
        if _message.role == "assistant":
            if _message.content:
                output += f"{_message.content}\n\n"
            if "tool_calls" in _message.additional_kwargs:
                for tool_call in _message.additional_kwargs["tool_calls"]:
                    output += f"Command: `{json.loads(tool_call.function.arguments).get('command')}`\n\n"
                    output += "-" * 100 + "\n"
        elif _message.role == "tool":
            output += f"Output:\n```\n{_message.content}\n```\n\n"
            output += "-" * 100 + "\n"
    return output


#########################################################################
#                          Code starts here                             #
#########################################################################


st.markdown("## Bash Mate: Linux Command Assistant")
st.caption("A step towards LLM OS")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

if st.session_state.messages == []:
    st.markdown(SUGGESTED_QUESTIONS)

if "message_history" not in st.session_state:
    st.session_state.message_history = []

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# React to user input
if prompt := st.chat_input("What is up?"):
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})


    #######################
    #   Process prompt    #
    #######################

    agent = shell_agent()
    
    process_query(agent, prompt=prompt, history=st.session_state.message_history)

    st.session_state.message_history = [agent.chat_history[-1]]

    formatted_response = process_memory(agent.chat_history[1:])

    with st.chat_message("assistant"):
        st.markdown(formatted_response)
    # Add assistant response to chat history
    st.session_state.messages.append(
        {"role": "assistant", "content": formatted_response}
    )

if st.session_state.messages:
    if st.sidebar.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()
