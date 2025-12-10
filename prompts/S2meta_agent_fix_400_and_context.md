---

task\_id: S2meta\_agent\_fix\_400\_and\_context

task\_type: devops

target\_project: C:/meta\_agent

mode: write\_dev

output\_path: output/meta\_agent\_fix\_400\_and\_context.md

---



\# ROLE



You are Codex running \*\*inside the Meta-Agent project at C:/meta\_agent\*\*.



Your task in THIS STAGE is to \*\*debug and fix the Meta-Agent so that it no longer sends oversized prompts to OpenAI/Codex\*\*, and instead:



1\. Uses the `target\_project` correctly.

2\. Limits and truncates project context to a safe size.

3\. Handles OpenAI HTTP 400 errors gracefully and with clear logging.



You are allowed to MODIFY code in this stage (write\_dev mode), but ONLY within `C:/meta\_agent`.





---



\# CURRENT SYMPTOMS



The user ran:



```bash

cd C:\\meta\_agent

python meta\_agent.py --task-file "prompts\\S1meta\_agent\_audit.md"

Console output:



text

Копіювати код

\[INFO] Running task S1meta\_agent\_audit (mode=readonly) from prompts\\S1meta\_agent\_audit.md

\[INFO] Collecting project context from C:/ai\_scalper\_bot...

\[INFO] Collected project context (131311916 chars).

\[INFO] Sending prompt to Codex for task S1meta\_agent\_audit...

\[INFO] Codex response received for task S1meta\_agent\_audit.

\[ERROR] Codex call failed for task S1meta\_agent\_audit: \[ERROR] CodexClient failed: Error code: 400

Problems:



Project context is HUGE (~131M characters).



Codex/OpenAI returns HTTP 400 (likely invalid\_request\_error for exceeding max context length).



The task does not complete successfully and does not produce the expected audit file.



FILES TO REVIEW AND MODIFY

You MUST review and, if required, modify:



meta\_agent.py



project\_scanner.py



prompt\_builder.py



codex\_client.py



file\_manager.py (only if needed)



task\_archiver.py (only if needed)



Do NOT touch any files outside C:/meta\_agent in this stage.



OBJECTIVES

1\. Use target\_project properly for context collection

Currently, the log shows:



text

Копіювати код

\[INFO] Collecting project context from C:/ai\_scalper\_bot...

even though the YAML front matter for the audit task sets:



yaml

Копіювати код

target\_project: C:/meta\_agent

You must:



Ensure that in MetaAgent.run\_task\_file(...) and MetaAgent.run\_stage\_pipeline(...):



target\_project is taken primarily from task metadata YAML (front matter, metadata.get("target\_project")) when running a single task via --task-file.



For stage pipeline, target\_project can come from config.json or a similar config, but the logic should be explicit and consistent.



Pass the correct target\_project to ProjectScanner:



python

Копіювати код

scanner = ProjectScanner(target\_dir=target\_project)

project\_context = scanner.collect\_project\_files()

Log clearly:



text

Копіювати код

\[INFO] Collecting project context from <target\_project>...

\[INFO] Collected project context (<N> chars).

So that if the task explicitly asks to audit C:/meta\_agent, it does NOT scan C:/ai\_scalper\_bot unless explicitly configured.



2\. Limit and truncate project context size

You must protect the OpenAI request from being too large.



Introduce a conservative limit like:



python

Копіювати код

MAX\_CONTEXT\_CHARS = 120\_000  # or similar, around 100-200k chars

Apply this limit at one or more of these points:



In ProjectScanner.collect\_project\_files(...):



Option A (preferred): allow it to collect all allowed files, but if the cumulative result length would exceed MAX\_CONTEXT\_CHARS, stop adding more and log something like:



text

Копіювати код

\[WARN] Project context truncated from <full\_len> to <MAX\_CONTEXT\_CHARS> chars (too large).

Option B: accumulate into a list and slice the final string to MAX\_CONTEXT\_CHARS.



In PromptBuilder.build\_prompt(...):



Ensure that the combined # Task Instructions + # Project Context does NOT exceed a sane limit.



If necessary, truncate project\_context before building the final prompt, with a log message as well.



The simplest robust solution is:



Let ProjectScanner produce a full string,



In MetaAgent, after collecting, measure its length,



If it exceeds MAX\_CONTEXT\_CHARS, truncate it:



python

Копіювати код

full\_len = len(project\_context)

if full\_len > MAX\_CONTEXT\_CHARS:

&nbsp;   project\_context = project\_context\[:MAX\_CONTEXT\_CHARS]

&nbsp;   print(f"\[WARN] Project context truncated from {full\_len} to {MAX\_CONTEXT\_CHARS} chars.")

This ensures we never send hundreds of MB to OpenAI.



3\. Fix prompt chunking / request building in CodexClient

Inspect CodexClient in codex\_client.py.



Current behavior (simplified):



It builds messages as a list of chunks:



python

Копіювати код

messages = \[{"role": "system", "content": "..."}]

for chunk in self.\_chunk\_prompt(prompt):

&nbsp;   messages.append({"role": "user", "content": chunk})

response = self.client.chat.completions.create(

&nbsp;   model=self.model,

&nbsp;   messages=messages,

&nbsp;   max\_tokens=4096,

&nbsp;   temperature=0

)

Potential issues:



If \_chunk\_prompt(prompt) yields many huge chunks, the sum of all chunk sizes still explodes the context limit and yields 400.



Chunking must protect total size, not just per-chunk size.



Your job:



Implement a clear, deterministic size limit for the entire prompt sent to OpenAI.



Concrete guidance:



Add a constant, e.g.:



python

Копіювати код

MAX\_PROMPT\_CHARS = 160\_000  # combined across all user messages

Ensure that the concatenation of all chunk strings does not exceed that limit.



A simple and acceptable solution:



Do NOT split into many user messages.



Instead, truncate the raw prompt string to MAX\_PROMPT\_CHARS and send it as a single user message:



python

Копіювати код

trimmed = prompt\[:MAX\_PROMPT\_CHARS]

messages = \[

&nbsp;   {"role": "system", "content": self.system\_prompt},

&nbsp;   {"role": "user", "content": trimmed},

]

Log if truncation happens:



python

Копіювати код

if len(prompt) > MAX\_PROMPT\_CHARS:

&nbsp;   print(f"\[WARN] Prompt truncated from {len(prompt)} to {MAX\_PROMPT\_CHARS} chars before sending to Codex.")

You can keep \_chunk\_prompt if already used elsewhere, but for the main chat.completions call it is acceptable (and simpler) to send ONE user message with a truncated prompt.



Improve error logging for HTTP errors:



Catch OpenAI HTTP errors explicitly (e.g. openai.APIError or generic Exception but inspect attributes).



If the exception has details like e.status\_code, e.response, or e.message, print them.



For a 400 error, include a line like:



python

Копіювати код

print(f"\[ERROR] OpenAI request failed (status={status}, type={error\_type}, message={error\_message})")

Still return a string starting with "\[ERROR] CodexClient failed: ..." for compatibility, but include more debugging detail.



4\. Keep YAML front matter, archiving, and encryption working

Make sure your changes do NOT break:



YAML front matter parsing and usage of fields:



task\_id,



task\_type,



target\_project,



mode,



output\_path.



Archiving behavior in task\_archiver.py:



Single-task .md files are archived into prompts/archive/<job\_name>/...,



<job\_name> is derived from Supervisor-like filenames S<number><job\_name>.md

or from target\_project or a "default" fallback.



Encrypted env logic:



env\_crypto.py with .env.enc and password "1111",



CodexClient calling \_bootstrap\_env() and using env vars for OpenAI keys.



Existing CLI flags:



--task-file,



--encrypt-env,



default behavior when no flags given (stage pipeline).



5\. Logging for long operations

To make the behavior less “mysterious” when it is slow:



Add/log messages before and after:



project context collection,



prompt building,



Codex request.



You already have some logs; just ensure they are consistent and present even after refactors.



OUTPUT FORMAT

Return updated files using the Meta-Agent file block convention.



Your response MUST be of the form:



text

Копіювати код

===FILE: meta\_agent.py===

<full updated content of meta\_agent.py>



===FILE: project\_scanner.py===

<full updated content of project\_scanner.py>



===FILE: prompt\_builder.py===

<full updated content of prompt\_builder.py>



===FILE: codex\_client.py===

<full updated content of codex\_client.py>

Include task\_archiver.py or other files ONLY if you actually change them:



text

Копіювати код

===FILE: task\_archiver.py===

<full updated content of task\_archiver.py>

Rules:



Always output full file contents, not diffs.



Do NOT include files you did not modify.



All Python must be valid for Python 3.12–3.14.

