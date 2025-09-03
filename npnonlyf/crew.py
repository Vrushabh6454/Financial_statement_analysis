# crew.py

import os
from crewai import Agent, Task, Crew, Process
from langchain_community.llms import Ollama
from tools import SemanticSearchTool, FinancialDataTool
import logging
from typing import Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the LLM to use
try:
    ollama_model = "ollama/llama2"
    llm = Ollama(model=ollama_model)
    logger.info(f"Using Ollama with model: {ollama_model}.")
except Exception as e:
    logger.error(f"Failed to initialize Ollama: {e}. Make sure Ollama is installed and the model 'llama3' is available.")
    llm = None
    # exit(1)

# Initialize the custom tools
semantic_search_tool = SemanticSearchTool()
financial_data_tool = FinancialDataTool()

# Define the Agents
risk_researcher = Agent(
    role='Financial Risk Researcher',
    goal='Identify and summarize all major financial and operational risks mentioned in a specific company\'s annual reports.',
    backstory=(
        "You are a seasoned expert in corporate finance, specializing in risk analysis. "
        "You meticulously scour financial notes and management discussions to uncover potential "
        "threats to a company's stability. You are thorough and detail-oriented."
    ),
    tools=[semantic_search_tool, financial_data_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

financial_analyst = Agent(
    role='Banking Financial Analyst',
    goal='Analyze key financial metrics and their trends to assess a bank\'s financial health.',
    backstory=(
        "You are a sharp-witted financial analyst with a deep understanding of banking metrics "
        "like liquidity ratios and asset quality. You synthesize data from financial statements "
        "to provide a concise and insightful overview of a company's performance."
    ),
    tools=[financial_data_tool],
    verbose=True,
    llm=llm
)

report_writer = Agent(
    role='Financial Report Writer',
    goal='Synthesize research findings and analysis into a clear, structured, and professional report.',
    backstory=(
        "You are an eloquent report writer with a talent for translating complex financial "
        "data into digestible insights. Your reports are well-organized, easy to read, "
        "and perfect for an executive audience."
    ),
    verbose=True,
    llm=llm
)

# Define the original Tasks (for their descriptions and expected_output)
task1_research_risks = Task(
    description=(
        "As a Financial Risk Researcher, your first step is to use the 'Semantic Search Tool' with a clear query. "
        "Your search query should be a single, concise sentence like 'What are the main risk factors for the company?'. "
        "Once you get the results from the tool, analyze the text and identify the top 5 risk factors mentioned. "
        "Focus on risks related to liquidity, credit, market, and operations. "
        "The final output of this task should be a detailed, bulleted list of these risks, each with a brief description based on the search results."
    ),
    expected_output="A bulleted list of the top 5 risk factors with a brief description for each.",
    agent=risk_researcher
)

task2_analyze_liquidity = Task(
    description=(
        "As a Banking Financial Analyst, you must use the 'Financial Data Tool' to gather key financial metrics for the company. "
        "The company is {company_name} with company_id: {company_id}. "
        "You must perform a series of single tool calls for EACH year from 2022 to 2024. "
        "For each year, first fetch the `current_ratio` from the 'features' dataset, then fetch the `cfo` from the 'cashflow' dataset. "
        "Each call must be a perfectly formed JSON string with the following keys: `company_id`, `year`, `statement_type`, and `field`. "
        "Example of a correct tool call: `Financial Data Tool.fetch_data('{{\"company_id\": \"{company_id}\", \"year\": 2023, \"statement_type\": \"features\", \"field\": \"current_ratio\"}}')`"
        "After gathering all data for all years, analyze the trends and summarize the company's liquidity health. "
        "The final answer must be a clear, concise paragraph summarizing the company's liquidity health and trends, citing the data you found."
    ),
    expected_output="A clear, concise paragraph summarizing the company's liquidity health and trends.",
    agent=financial_analyst,
    context=[task1_research_risks]
)

task3_generate_report = Task(
    description=(
        "Combine the risk research and liquidity analysis into a single, comprehensive report for {company_name}. "
        "Start with a brief executive summary, then present the key findings, and conclude with "
        "an overall assessment of the company's financial health. "
    ),
    expected_output="A well-structured financial report in markdown format.",
    agent=report_writer,
    context=[task1_research_risks, task2_analyze_liquidity]
)

# Function to run the crew
def run_analysis_crew(task_inputs: Dict):
    """
    Runs the CrewAI analysis with provided inputs.
    """
    research_task = Task(
        description=task1_research_risks.description,
        expected_output=task1_research_risks.expected_output,
        agent=risk_researcher
    )
    
    analysis_task = Task(
        # The fix is here: pass the formatted string directly to the description
        description=task2_analyze_liquidity.description.format(
            company_name=task_inputs.get('company_name', 'the company'),
            company_id=task_inputs.get('company_id', '')
        ),
        expected_output=task2_analyze_liquidity.expected_output,
        agent=financial_analyst,
        context=[research_task]
    )

    report_task = Task(
        # The fix is here: pass the formatted string directly to the description
        description=task3_generate_report.description.format(
            company_name=task_inputs.get('company_name', 'the company')
        ),
        expected_output=task3_generate_report.expected_output,
        agent=report_writer,
        context=[research_task, analysis_task]
    )

    financial_crew = Crew(
        agents=[risk_researcher, financial_analyst, report_writer],
        tasks=[research_task, analysis_task, report_task],
        process=Process.sequential,
        verbose=True
    )
    
    result = financial_crew.kickoff()
    
    return str(result)