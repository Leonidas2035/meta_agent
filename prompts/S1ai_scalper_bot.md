\# ROLE



You are Codex running \*\*inside the Meta-Agent project at C:/meta\_agent\*\*.



Your task in THIS STAGE is to upgrade the Meta-Agent so that it can be

safely controlled by an external \*\*Supervisor Agent\*\* and execute tasks

via Codex/OpenAI API in a predictable, automated, non-interactive way.



You must:

\- Add a \*\*task-file mode\*\* (CLI) controlled by `--task-file`.

\- Standardize the \*\*task prompt format\*\* using YAML front matter.

\- Integrate \*\*encrypted .env handling\*\* with a fixed password `1111`.

\- Keep \*\*existing stage-based behavior\*\* working as before.





---



\# CONTEXT



The Meta-Agent is a Dev/Automation agent, not a trading bot.



It is used to:

\- perform DevOps AI tasks,

\- generate and refactor code (Codegen),

\- audit code (Audit),

\- generate documentation (Documentation),



by orchestrating Codex/OpenAI over one or more target projects,

such as `C:/ai\_scalper\_bot` or `C:/meta\_agent` itself.



A future \*\*Supervisor Agent\*\* will:



\- generate task files in `C:/meta\_agent/prompts`

\- call `python meta\_agent.py --task-file <path>`

\- then read the results from `output/` or elsewhere.



You must therefore make the Meta-Agent:



\- controllable via CLI,

\- predictable (no interactive questions),

\- deterministic in its file I/O behavior,

\- safe in how it uses API keys (encrypted .env).





---



\# OBJECTIVES



1\. \*\*Task-file mode for Supervisor control\*\*



&nbsp;  Add a clear code path in `meta\_agent.py` so that it can be run as:



&nbsp;  ```bash

&nbsp;  python meta\_agent.py --task-file "prompts/task\_2025-12-05\_001\_audit\_quantumedge.md"

In this mode the Meta-Agent must:



parse the provided task file,



extract metadata from YAML front matter,



execute EXACTLY this single task,



write outputs to the location specified in the metadata,



exit with code 0 on success, non-zero on failure,



avoid any interactive prompts or manual confirmation.



Standardized task file format (YAML front matter)



Define a stable task-file format that the Supervisor will generate

and the Meta-Agent will consume.



Example format:



markdown

Копіювати код

---

task\_id: 2025-12-05\_001

task\_type: audit          # audit | devops | codegen | docs

target\_project: C:/ai\_scalper\_bot

mode: readonly            # readonly | write\_dev | write\_prod

output\_path: output/audit/report\_2025-12-05\_001.md

---



\# ROLE

You are Codex running inside Meta-Agent...



\# GOAL

\- Audit the risk engine in QuantumEdge

\- Suggest improvements...



\# CONSTRAINTS

\- Do not touch production configs

Requirements:



Use the block between the first and second --- as YAML front matter.



Parse it via pyyaml (add dependency if needed).



Make the front-matter keys accessible to the rest of the Meta-Agent.



The rest of the file (after the second ---) is the prompt body

to be sent to Codex/OpenAI (with any additional context you already add).



The Meta-Agent must at minimum understand and use:



task\_id (for logging and output file naming),



task\_type (audit/devops/codegen/docs; used for future routing),



target\_project (path to the project to operate on),



mode (readonly | write\_dev | write\_prod; enforce basic semantics),



output\_path (preferred output location inside C:/meta\_agent).



Behavior for mode:



readonly: do not modify any files in target\_project, only read and

produce reports in output/.



write\_dev: allowed to write/update files in target\_project (e.g. when

the Supervisor is using a dev clone).



write\_prod: keep the code ready but do NOT introduce any hard-coded

write-prod specific hacks; just treat it same as write\_dev for now, but

keep the field wired for future policy enforcement.



If a task file has no YAML front matter, treat it as legacy format and

fall back to the existing pipeline behavior (if any).



CLI integration and non-interactive execution



In meta\_agent.py:



Add argument parsing via argparse or similar.



Support at least:



--task-file PATH : run exactly one task described by a single file.



(Optionally) --once to make it explicit the agent should run

once and exit.



Behavior:



If --task-file is provided:



Skip the old stages.yaml pipeline,



Run only this one task,



Exit afterward.



If --task-file is NOT provided:



Keep current behavior (stage-based pipeline using stages.yaml),

so that existing usage is not broken.



Make sure:



No interactive input() calls or prompts in task-file mode.



Any errors are logged clearly and cause a non-zero exit code.



Logging remains readable in console and/or output/.



Encrypted .env handling with fixed password 1111



Introduce encrypted environment handling so that API keys are not stored

in plain .env files on disk.



Requirements:



Create a new module in the Meta-Agent project, e.g.:



env\_crypto.py (in the root of C:/meta\_agent or inside a utils/ folder)



This module must provide at least:



python

Копіювати код

def encrypt\_env(

&nbsp;   plain\_path: str = ".env",

&nbsp;   enc\_path: str = ".env.enc",

&nbsp;   password: str = "1111",

) -> None:

&nbsp;   ...

Reads environment variables from plain\_path (typical .env format).



Encrypts the content into enc\_path.



Uses a fixed password "1111" as the encryption password.

(Security strength is not the goal; only encryption-at-rest.)



python

Копіювати код

def load\_decrypted\_env(

&nbsp;   enc\_path: str = ".env.enc",

&nbsp;   password: str = "1111",

) -> None:

&nbsp;   ...

Decrypts enc\_path using the same password.



Loads the resulting key-value pairs into os.environ.



Use a well-known crypto library, do NOT roll your own encryption.

Suggested:



cryptography package (e.g. from cryptography.fernet import Fernet)



Derive a key from the password "1111" using a standard KDF

(e.g. PBKDF2-HMAC-SHA256) and use it for encryption/decryption.



Behavior expectations:



Prefer .env.enc + load\_decrypted\_env() over plain .env.



Still allow plain .env as a fallback if needed (e.g. if .env.enc

does not exist).



Add a simple CLI mode to meta\_agent.py or a small utility script,

e.g.:



bash

Копіювати код

python meta\_agent.py --encrypt-env

Which would:



Call encrypt\_env(".env", ".env.enc", "1111")



Optionally warn the user that .env can be safely deleted.



Integrate this with the existing codex\_client.py so that:



OpenAI/Codex API keys are loaded from os.environ,



load\_decrypted\_env() is called early (before creating the client),



The keys never need to be stored in plain .env in normal operation.



Dependencies and requirements



If there is no requirements.txt in C:/meta\_agent, create one.

If it exists, update it as needed.



Ensure it contains at least:



openai or the appropriate OpenAI client version you are using,



python-dotenv (if still needed),



pyyaml (for YAML front matter),



cryptography (for encrypted .env).



Example minimal:



text

Копіювати код

openai>=1.30

python-dotenv>=1.0

pyyaml>=6.0

cryptography>=41.0

Do not remove other legitimate dependencies that already exist in the file.



Targeted file changes only in the Meta-Agent project



You must only modify files inside C:/meta\_agent, for example:



meta\_agent.py



codex\_client.py



project\_scanner.py (if needed to support task-file mode)



prompt\_builder.py (if it needs to become task-aware)



new env\_crypto.py



requirements.txt (create or update)



Do NOT touch other external projects such as C:/ai\_scalper\_bot

from this stage. The Supervisor will manage paths and dev/prod separation.



IMPLEMENTATION HINTS (NON-BINDING)

These are suggestions; use them only if they align well with the existing code:



In meta\_agent.py:



Wrap the existing logic in a MetaAgent class or keep the current one.



Add an entrypoint that parses CLI args and either:



runs the legacy stages.yaml pipeline, or



runs a single task from --task-file.



For YAML front matter parsing:



Implement a small helper:



python

Копіювати код

def load\_task\_from\_file(path: str) -> tuple\[dict, str]:

&nbsp;   """

&nbsp;   Returns (metadata, body\_text).

&nbsp;   metadata: dict parsed from YAML front matter.

&nbsp;   body\_text: rest of the prompt file after the second '---'.

&nbsp;   """

&nbsp;   ...

Integrate task\_type and mode into your internal routing logic but

avoid over-complicating; wiring the fields through is enough for now.



OUTPUT FORMAT

Return the complete updated code files using the Meta-Agent file block convention.



Your response MUST consist of one or more file blocks of the form:



text

Копіювати код

===FILE: meta\_agent.py===

<full updated content of meta\_agent.py>



===FILE: codex\_client.py===

<full updated content of codex\_client.py>



===FILE: env\_crypto.py===

<full content of the new file>



===FILE: requirements.txt===

<full content of the (new or updated) file>



... (any other updated files if needed)

Rules:



Always output full file contents, not diffs.



Include ALL files that you modify or create.



Do NOT include files you did not change.



Do NOT modify any files outside the Meta-Agent project.



Make sure the new code is syntactically valid Python for the

currently used Python version (3.12–3.14).

