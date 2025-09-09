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
    logger.error(f"Failed to initialize Ollama: {e}. Make sure Ollama is installed and the model 'llama2' is available.")
    llm = None

# Initialize the custom tools
semantic_search_tool = SemanticSearchTool()
financial_data_tool = FinancialDataTool()

# Define the Agents - FIXED DESCRIPTIONS
risk_researcher = Agent(
    role='Financial Data Researcher',
    goal='Research and summarize business metrics and financial indicators from company reports.',
    backstory=(
        "You are a professional business analyst specializing in corporate finance research. "
        "You analyze financial statements and business reports to identify key business indicators. "
        "You provide objective analysis of standard business metrics."
    ),
    tools=[semantic_search_tool, financial_data_tool],
    verbose=True,
    allow_delegation=False,
    llm=llm
)

financial_analyst = Agent(
    role='Business Financial Analyst',
    goal='Analyze financial metrics and trends to assess company performance.',
    backstory=(
        "You are a professional financial analyst who evaluates standard business metrics "
        "including liquidity ratios and financial performance indicators. You provide "
        "objective analysis of corporate financial data for business evaluation."
    ),
    tools=[financial_data_tool],
    verbose=True,
    llm=llm
)

report_writer = Agent(
    role='Business Report Writer',
    goal='Create professional business analysis reports based on financial data.',
    backstory=(
        "You are a professional business writer who creates comprehensive analysis reports. "
        "You synthesize financial data into clear, structured business reports suitable "
        "for corporate stakeholders and business decision-making."
    ),
    verbose=True,
    llm=llm
)

# Define the Tasks - FIXED DESCRIPTIONS
task1_research_risks = Task(
    description=(
        "As a Financial Data Researcher, use the Semantic Search Tool to gather business information. "
        "Call: Semantic Search Tool('What are the key business factors for the company?'). "
        "Analyze the results and identify 5 important business considerations including "
        "operational factors, market conditions, and financial indicators. "
        "Present findings as a structured list with descriptions."
    ),
    expected_output="A structured list of 5 key business factors with descriptions.",
    agent=risk_researcher
)

task2_analyze_liquidity = Task(
    description=(
        "As a Business Financial Analyst, use the Financial Data Tool to gather financial metrics. "
        "The company is {company_name} with company_id: {company_id}. "
        "Fetch current_ratio and cfo data for years 2022-2024 using proper JSON format. "
        "Example: Financial Data Tool('{{\"company_id\": \"{company_id}\", \"year\": 2023, \"statement_type\": \"features\", \"field\": \"current_ratio\"}}') "
        "Analyze the trends and provide a business performance assessment."
    ),
    expected_output="A professional assessment of financial performance and trends.",
    agent=financial_analyst,
    context=[task1_research_risks]
)

task3_generate_report = Task(
    description=(
        "Create a comprehensive business analysis report for {company_name}. "
        "Combine the research findings and financial analysis into a professional report. "
        "Include executive summary, key findings, and business performance assessment. "
        "Format as a structured business report."
    ),
    expected_output="A professional business analysis report in markdown format.",
    agent=report_writer,
    context=[task1_research_risks, task2_analyze_liquidity]
)

# Function to run the crew - NO CHANGES
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
        description=task2_analyze_liquidity.description.format(
            company_name=task_inputs.get('company_name', 'the company'),
            company_id=task_inputs.get('company_id', '')
        ),
        expected_output=task2_analyze_liquidity.expected_output,
        agent=financial_analyst,
        context=[research_task]
    )

    report_task = Task(
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
