from groq import Groq
import os
import json
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ---- TOOL ----
def search_jobs(keywords, location):
    """Search for jobs based on keywords and location"""
    mock_jobs = [
        {"title": "Python Developer", "company": "TechCorp", "location": "Austin, TX", "salary": "$120k"},
        {"title": "Python Engineer", "company": "StartupXYZ", "location": "Austin, TX", "salary": "$110k"},
        {"title": "Java Developer", "company": "BigBank", "location": "Austin, TX", "salary": "$130k"},
        {"title": "Python Developer", "company": "RemoteCo", "location": "Remote", "salary": "$115k"},
    ]
    results = [
        job for job in mock_jobs
        if keywords.lower() in job["title"].lower()
        and (location.lower() in job["location"].lower() or location.lower() == "remote")
    ]
    return results

# ---- AGENT LOOP ----
def run_agent(user_goal):
    
    conversation_history = [
        {
            "role": "system",
            "content": """You are an agent operating inside a ReAct loop.
            Your output is parsed directly by code using json.loads().
            If you return anything other than pure JSON the system will crash.
            You have exactly two tools:
            1. {"action": "search_jobs", "keywords": "...", "location": "..."}
            2. {"action": "final_answer", "answer": "..."}

            STRICT RULES:
            - Only search for exactly what the user asked for. Nothing else.
            - If search_jobs returns results, IMMEDIATELY use final_answer to report them.
            - If search_jobs returns empty, IMMEDIATELY use final_answer to say no results found.
            - Never run more than one search.
            - Never invent additional searches."""
        },
        {
            "role": "user",
            "content": user_goal
        }
    ]

    print(f"\nAgent starting for goal: {user_goal}\n")

    # ---- REACT LOOP ----
    while True:
        
        # THINK - ask LLM what to do next
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=conversation_history
        )
        
        llm_output = response.choices[0].message.content
        print(f"LLM decided: {llm_output}\n")
        
        try:
            decision = json.loads(llm_output)
        except json.JSONDecodeError:
            print("LLM returned invalid JSON, retrying...")
            conversation_history.append({"role": "assistant", "content": llm_output})
            conversation_history.append({"role": "user", "content": "Your last response was not valid JSON. Please respond with only a JSON object."})
            continue

        # Check termination condition
        if decision["action"] == "final_answer":
            print(f"Agent finished: {decision['answer']}")
            break
        
        # ACT - run the tool
        if decision["action"] == "search_jobs":
            results = search_jobs(decision["keywords"], decision["location"])
            print(f"Tool returned: {results}\n")
            
            # OBSERVE - feed results back to LLM
            conversation_history.append({"role": "assistant", "content": llm_output})
            conversation_history.append({"role": "user", "content": f"Search results: {json.dumps(results)}"})

# ---- RUN ----
run_agent("Find me Python developer jobs in India")