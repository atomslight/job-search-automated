import os
import json
import re
import time
import pandas as pd

from crewai import Agent, Task, Crew, Process, LLM

from ingestion import (
    load_jobs,
    load_resume,
    get_jobs,
)


# ============================================================
# CONFIG
# ============================================================

OLLAMA_BASE_URL = os.getenv(
    "OLLAMA_BASE_URL",
    "http://localhost:11434/v1"
)

OLLAMA_MODEL = os.getenv(
    "OLLAMA_MODEL",
    "gemma4:31b-cloud"
)

JOB_LIMIT = 70
START_INDEX = 0

# Create a unique timestamped output filename
TIMESTAMP = time.strftime("%Y%m%d_%H%M%S")
OUTPUT_FILE = f"jobs_with_resume_match_{TIMESTAMP}.csv"


# ============================================================
# JSON PARSER
# ============================================================

def extract_json(text):

    text = str(text).strip()

    text = re.sub(
        r"```json|```",
        "",
        text,
        flags=re.IGNORECASE
    ).strip()

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    try:
        return json.loads(
            text[start:end + 1]
        )

    except json.JSONDecodeError:
        return None


# ============================================================
# FALLBACK
# ============================================================

def fallback_result(error):

    return {
        "relevance": "Not Relevant",
        "match_score": 0,
        "experience_required": "",
        "candidate_experience_fit": "",
        "experience_gap": "",
        "seniority_fit": "",
        "must_have_skills": [],
        "matching_skills": [],
        "transferable_skills": [],
        "missing_important_skills": [],
        "responsibility_match": "",
        "candidate_profile_sought": "",
        "why_this_role_matches": "",
        "main_concerns": [error],
        "direct_evidence_from_job": [],
        "evidence_from_resume": [],
        "final_reason": "Research failed."
    }


# ============================================================
# CREATE RESEARCHER
# ============================================================

def create_researcher():

    llm = LLM(
        model=f"openai/{OLLAMA_MODEL}",
        base_url=OLLAMA_BASE_URL,
        api_key="ollama",
    )

    return Agent(

        role="Technical Job Fit Researcher",

        goal=(
            "Evaluate each complete job record against the complete "
            "candidate resume and determine whether the job is HIGHLY "
            "RELEVANT. Act as a strict filter and keep only strong matches."
        ),

        backstory=(
            "You are an experienced technical recruiter and AI/ML "
            "hiring analyst. You evaluate actual experience, seniority, "
            "technical stack, responsibilities and candidate profile. "
            "You distinguish professional work, freelance work, "
            "internships, projects and education. You never invent "
            "skills or experience."
        ),

        llm=llm,

        verbose=True,

        max_iter=10,

        max_execution_time=300,

        allow_delegation=False,
    )


# ============================================================
# CREATE TASK
# ============================================================

def create_task(
    researcher,
    job_record,
    resume_text
):

    job_json = json.dumps(
        job_record,
        indent=2,
        ensure_ascii=False
    )

    task_description = f"""
You are evaluating ONE job against ONE candidate.

============================================================
CANDIDATE RESUME
============================================================

{resume_text}


============================================================
COMPLETE JOB RECORD
============================================================

{job_json}


============================================================
YOUR TASK
============================================================

Your ONLY purpose is to identify whether this job is HIGHLY RELEVANT
to the candidate.

Return exactly one of:

- Highly Relevant
- Not Relevant


============================================================
1. EXPERIENCE
============================================================

Determine the experience requirement from the complete job record.

Pay particular attention to:

- fresher
- graduate
- 0-1 years
- 1-2 years
- 1-3 years
- 2-5 years
- 3-5 years
- 5+ years
- senior
- lead
- principal
- manager
- internship
- entry level
- mid level

Compare it against the candidate's actual timeline.

Do not treat internships as automatically equal to professional
experience.

The candidate has freelance / independent work as well as internships.
Understand those separately.

Do not invent years of experience.

A major experience or seniority mismatch means NOT RELEVANT.

For fresher / 0-1 roles, having more experience does not automatically
make the role Not Relevant if the actual technical work is strongly aligned.


============================================================
2. TECHNICAL STACK
============================================================

Compare the complete job requirements with the resume.

Consider:

- Python
- Node.js
- TypeScript
- SQL
- REST APIs
- LLMs
- Generative AI
- Agentic AI
- AI Agents
- LangChain
- CrewAI
- MCP
- LangGraph
- RAG
- Qdrant
- Pgvector
- ChromaDB
- Reranking
- AI evaluation
- LLM-as-a-Judge
- PyTorch
- TensorFlow
- Transformers
- Diffusion Models
- LoRA
- Docker
- AWS
- GCP
- Git/GitHub
- databases
- cloud
- automation
- infrastructure
- NLP
- computer vision

Do not limit the analysis to this list.

Do not claim a skill matches simply because a similar skill exists.

There must be meaningful evidence in the resume.


============================================================
3. RESPONSIBILITIES
============================================================

Compare what the employer actually expects the person to do with what
the candidate has actually done.

Do not rely on the job title alone.

The actual responsibilities must strongly align with the candidate's
background.

A major responsibility mismatch means NOT RELEVANT.


============================================================
4. CANDIDATE PROFILE
============================================================

Determine what type of person the employer is seeking.

Examples:

- Fresher with strong fundamentals
- Early-career AI engineer
- Production GenAI engineer
- Agentic AI engineer
- ML researcher
- Backend engineer
- Senior software engineer
- Technical lead
- Automation engineer

The candidate profile must be strongly compatible with the role.


============================================================
5. STRICT FILTER
============================================================

Return HIGHLY RELEVANT only when ALL of these are reasonably satisfied:

- Strong responsibility match
- Reasonable experience match
- Reasonable seniority match
- Strong core technical match
- Candidate has evidence of similar work
- No major must-have gap
- Employer is looking for a profile substantially similar to the candidate

If any major requirement is not satisfied:

Return:

"Not Relevant"

Do not use "Relevant" as a middle category.

This is a strict shortlist filter.


============================================================
6. FACTS VS INFERENCE
============================================================

DIRECT JOB EVIDENCE:
Facts explicitly present in the job record.

RESUME EVIDENCE:
Facts explicitly present in the resume.

INFERENCE:
Your conclusion based on those facts.

Never present inference as direct fact.


============================================================
7. OUTPUT
============================================================

Return ONLY valid JSON.

{{
    "relevance": "Highly Relevant | Not Relevant",
    "match_score": 0,
    "experience_required": "",
    "candidate_experience_fit": "",
    "experience_gap": "",
    "seniority_fit": "",
    "must_have_skills": [],
    "matching_skills": [],
    "transferable_skills": [],
    "missing_important_skills": [],
    "responsibility_match": "",
    "candidate_profile_sought": "",
    "why_this_role_matches": "",
    "main_concerns": [],
    "direct_evidence_from_job": [],
    "evidence_from_resume": [],
    "final_reason": ""
}}

Rules:

- match_score must be between 0 and 100
- relevance must be exactly "Highly Relevant" or "Not Relevant"
- never invent experience
- never invent skills
- never write anything outside the JSON
"""

    return Task(
        description=task_description,
        expected_output=(
            "Valid JSON containing the complete "
            "job-to-resume analysis."
        ),
        agent=researcher,
    )


# ============================================================
# MAIN
# ============================================================

def main(csv_file):

    print("\n")
    print("=" * 70)
    print("JOB → RESUME RESEARCHER")
    print("=" * 70)

    # --------------------------------------------------------
    # LOAD EXACT CSV PASSED BY AUTOMATION
    # --------------------------------------------------------

    df = load_jobs(csv_file)

    # --------------------------------------------------------
    # LOAD RESUME
    # --------------------------------------------------------

    resume_text = load_resume()

    print("\nInput CSV:")
    print(csv_file)

    print("\nTotal records:")
    print(len(df))

    print("\nResume characters:")
    print(len(resume_text))

    # --------------------------------------------------------
    # CREATE RESEARCHER
    # --------------------------------------------------------

    researcher = create_researcher()

    # --------------------------------------------------------
    # FINAL RESULTS
    # --------------------------------------------------------

    final_rows = []

    end_index = min(
        START_INDEX + JOB_LIMIT,
        len(df)
    )

    # ========================================================
    # PROCESS EACH RECORD
    # ========================================================

    for index, job_record in get_jobs(df):

        if index < START_INDEX:
            continue

        if index >= end_index:
            break

        print("\n")
        print("=" * 70)
        print(
            f"PROCESSING RECORD {index + 1} / {len(df)}"
        )
        print("=" * 70)

        print(
            "\nTitle:",
            job_record.get("title", "")
        )

        print(
            "Company:",
            job_record.get("company", "")
        )

        print(
            "Location:",
            job_record.get("location", "")
        )

        print(
            "Experience:",
            job_record.get("experience_range", "")
        )

        # ----------------------------------------------------
        # CREATE TASK
        # ----------------------------------------------------

        task = create_task(
            researcher,
            job_record,
            resume_text
        )

        # ----------------------------------------------------
        # RUN CREWAI
        # ----------------------------------------------------

        try:

            print(
                "\nResearcher analyzing..."
            )

            crew = Crew(
                agents=[researcher],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
                max_rpm=20
            )

            result = crew.kickoff()

            analysis = extract_json(
                str(result)
            )

            if analysis is None:

                print(
                    "\nWARNING: Invalid JSON returned."
                )

                analysis = fallback_result(
                    "Invalid JSON returned by Ollama."
                )

        except Exception as error:

            print(
                "\nRESEARCHER ERROR:"
            )

            print(
                type(error).__name__,
                str(error)
            )

            analysis = fallback_result(
                str(error)
            )

        # ----------------------------------------------------
        # SHOW FILTER RESULT
        # ----------------------------------------------------

        print(
            "\nRELEVANCE:"
        )

        print(
            analysis.get(
                "relevance",
                "Not Relevant"
            )
        )

        print(
            "\nMATCH SCORE:"
        )

        print(
            analysis.get(
                "match_score",
                0
            )
        )

        print(
            "\nFINAL REASON:"
        )

        print(
            analysis.get(
                "final_reason",
                ""
            )
        )

        # ----------------------------------------------------
        # ONLY SAVE HIGHLY RELEVANT
        # ----------------------------------------------------

        if analysis.get("relevance") == "Highly Relevant":

            output_row = job_record.copy()

            output_row.pop(
                "_row_index",
                None
            )

            output_row.update({

                "relevance": "Highly Relevant",

                "match_score": analysis.get(
                    "match_score",
                    0
                ),

                "experience_required": analysis.get(
                    "experience_required",
                    ""
                ),

                "candidate_experience_fit": analysis.get(
                    "candidate_experience_fit",
                    ""
                ),

                "experience_gap": analysis.get(
                    "experience_gap",
                    ""
                ),

                "seniority_fit": analysis.get(
                    "seniority_fit",
                    ""
                ),

                "must_have_skills": json.dumps(
                    analysis.get(
                        "must_have_skills",
                        []
                    ),
                    ensure_ascii=False
                ),

                "matching_skills": json.dumps(
                    analysis.get(
                        "matching_skills",
                        []
                    ),
                    ensure_ascii=False
                ),

                "transferable_skills": json.dumps(
                    analysis.get(
                        "transferable_skills",
                        []
                    ),
                    ensure_ascii=False
                ),

                "missing_important_skills": json.dumps(
                    analysis.get(
                        "missing_important_skills",
                        []
                    ),
                    ensure_ascii=False
                ),

                "responsibility_match": analysis.get(
                    "responsibility_match",
                    ""
                ),

                "candidate_profile_sought": analysis.get(
                    "candidate_profile_sought",
                    ""
                ),

                "why_this_role_matches": analysis.get(
                    "why_this_role_matches",
                    ""
                ),

                "main_concerns": json.dumps(
                    analysis.get(
                        "main_concerns",
                        []
                    ),
                    ensure_ascii=False
                ),

                "direct_evidence_from_job": json.dumps(
                    analysis.get(
                        "direct_evidence_from_job",
                        []
                    ),
                    ensure_ascii=False
                ),

                "evidence_from_resume": json.dumps(
                    analysis.get(
                        "evidence_from_resume",
                        []
                    ),
                    ensure_ascii=False
                ),

                "final_reason": analysis.get(
                    "final_reason",
                    ""
                )
            })

            final_rows.append(
                output_row
            )

            print(
                "\n✅ HIGHLY RELEVANT → SAVED"
            )

        else:

            print(
                "\n❌ NOT RELEVANT → DISCARDED"
            )

        print(
            "\nRecord completed. Moving to next..."
        )

        time.sleep(1)

    # ========================================================
    # SAVE FINAL CSV
    # ========================================================

    if not final_rows:

        print(
            "\nNo Highly Relevant jobs found."
        )

        return

    final_df = pd.DataFrame(
        final_rows
    )

    final_df.to_csv(
        OUTPUT_FILE,
        index=False,
        encoding="utf-8-sig"
    )

    # ========================================================
    # SUMMARY
    # ========================================================

    print("\n")
    print("=" * 70)
    print("RESEARCH COMPLETE")
    print("=" * 70)

    print(
        "\nHighly Relevant jobs:",
        len(final_df)
    )

    print(
        "\nSaved:"
    )

    print(
        OUTPUT_FILE
    )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    import sys

    if len(sys.argv) < 2:

        raise Exception(
            "CSV path was not provided."
        )

    csv_file = sys.argv[1]

    main(csv_file)
