from langchain_classic.agents import create_tool_calling_agent, AgentExecutor

from src.models import get_llm
from src.agent.prompts import prompt_v2
from src.tools.file_tools import read_file, list_directory, search_files, project_tree
from src.tools.code_tools import search_code, find_todos, find_possible_bugs, analyze_file, generate_tests
from src.tools.system_tools import cpu_usage, memory_usage, disk_usage, running_processes, largest_files
from src.tools.shell_tools import remove_file, modify_file, delete_file, current_directory, current_user, system_power_sleep

llm = get_llm()

tools = [
    read_file,
    list_directory,
    search_files,
    project_tree,
    generate_tests,
    search_code,
    find_todos,
    analyze_file,
    find_possible_bugs,
    cpu_usage,
    memory_usage,
    disk_usage,
    running_processes,
    largest_files,
    remove_file,
    modify_file,
    delete_file,
    system_power_sleep,
    current_directory,
    current_user
]

agent = create_tool_calling_agent(
    llm=llm,
    tools=tools,
    prompt=prompt_v2
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    return_intermediate_steps=True,
    name="Local Assistant"
)