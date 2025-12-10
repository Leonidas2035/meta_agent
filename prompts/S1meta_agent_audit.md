\# CONTEXT



The Meta-Agent is used as a Dev/Automation AI layer to:



\- orchestrate Codex/OpenAI tasks over one or more target projects,

\- execute tasks like:

&nbsp; - DevOps automation,

&nbsp; - code generation / refactoring (Codegen),

&nbsp; - audits,

&nbsp; - documentation generation,

\- work both in:

&nbsp; - pipeline mode via `stages.yaml`,

&nbsp; - single-task mode via `--task-file` and/or a default task file.



Recent changes introduced:



\- YAML front matter task format,

\- support for `--task-file`,

\- support for a default single-task file (e.g. `prompts/task\_current.md`),

\- encrypted env handling via `.env.enc` with password `1111`,

\- a task archiver that routes prompt files into `prompts/archive/<job\_name>/...`,

&nbsp; including support for Supervisor-style filenames `S<number><job\_name>.md`.





---



\# SCOPE



Focus your analysis on the Meta-Agent project in `C:/meta\_agent`, in particular:



\- `meta\_agent.py`

\- `codex\_client.py`

\- `project\_scanner.py`

\- `prompt\_builder.py`

\- `file\_manager.py`

\- `task\_archiver.py`

\- `env\_crypto.py`

\- `stages.yaml`

\- `config.json`

\- `requirements.txt`



If there are other small helper modules referenced by these core files, you may

include them briefly where relevant, but the core description should center around

the modules above.





---



\# TASKS



Produce a single, coherent Markdown document that contains at least the following sections:



\## 1. High-level overview



\- What is the overall purpose of the Meta-Agent?

\- How does it fit into a larger system with:

&nbsp; - a trading bot (QuantumEdge),

&nbsp; - a future Supervisor Agent?

\- What are the main responsibilities and non-goals of the Meta-Agent?



\## 2. Execution modes and control flow



Describe in detail:



\- How the Meta-Agent is started from `meta\_agent.py`.

\- CLI modes:

&nbsp; - `--task-file <path>`

&nbsp; - any default task file (e.g. `prompts/task\_current.md`) if present

&nbsp; - legacy pipeline mode via `stages.yaml`

&nbsp; - `--encrypt-env`

\- The control flow for:

&nbsp; - single-task execution,

&nbsp; - stage pipeline execution,

&nbsp; - environment encryption.



For each mode, explain:



\- What inputs it expects (which file, which format),

\- What it does step by step,

\- What outputs it produces and where (e.g. `output/...`).



\## 3. Modules and their responsibilities



For each key module, provide a concise but clear description:



\- `meta\_agent.py`

&nbsp; - main entrypoint,

&nbsp; - orchestrates tasks and/or stages,

&nbsp; - how it uses `project\_scanner`, `prompt\_builder`, `codex\_client`, `task\_archiver`.



\- `codex\_client.py`

&nbsp; - how it loads secrets (env / `.env.enc`),

&nbsp; - how it builds and sends requests to OpenAI / Codex,

&nbsp; - how responses are returned to the rest of the system.



\- `project\_scanner.py`

&nbsp; - how it discovers files / context in target projects,

&nbsp; - any filtering / ignoring rules,

&nbsp; - what data it returns to `meta\_agent.py` or `prompt\_builder.py`.



\- `prompt\_builder.py`

&nbsp; - how it combines task prompt file + project context,

&nbsp; - how it handles YAML front matter (if applicable),

&nbsp; - how it prepares the final prompt for Codex.



\- `file\_manager.py`

&nbsp; - how it writes responses from Codex to disk,

&nbsp; - how it interprets file blocks in the format:

&nbsp;   - `===FILE: some/path.py===`

&nbsp;   - `<content>`

&nbsp; - how it handles overwrites, new files, etc.



\- `task\_archiver.py`

&nbsp; - how it archives:

&nbsp;   - pipeline stage prompt files from `stages.yaml`,

&nbsp;   - single-task prompt files from `--task-file`,

&nbsp; - how it derives `<job\_name>`,

&nbsp;   - from Supervisor-style filenames `S<number><job\_name>.md`,

&nbsp;   - or from `target\_project` / defaults,

&nbsp; - where exactly files end up:

&nbsp;   - `prompts/archive/<job\_name>/<original\_file\_name>.md`,

&nbsp; - how `stages.yaml` is cleared.



\- `env\_crypto.py`

&nbsp; - how it encrypts `.env` into `.env.enc` using password `"1111"`,

&nbsp; - which crypto primitives are used (e.g., PBKDF2 + Fernet),

&nbsp; - how `load\_decrypted\_env` works and when it is called.



\- `stages.yaml` and `config.json`

&nbsp; - what structure they expect,

&nbsp; - how they drive the pipeline and configure project paths.



\## 4. Data flow and lifecycle of a single task



Describe end-to-end what happens when a single task is executed, for example:



\- Input:

&nbsp; - a task file with YAML front matter in `prompts/...`,

&nbsp; - possibly named with Supervisor pattern (e.g. `S1ai\_scalper\_bot.md`),

\- Steps:

&nbsp; - how YAML front matter is parsed,

&nbsp; - how `target\_project` and `mode` are used,

&nbsp; - how `project\_scanner` collects code context,

&nbsp; - how `prompt\_builder` constructs the final prompt for Codex,

&nbsp; - how `codex\_client` sends the request and receives the reply,

&nbsp; - how `file\_manager` writes output and/or updated files,

&nbsp; - how `task\_archiver` moves the `.md` to `prompts/archive/<job\_name>/...`,

\- Output:

&nbsp; - response log in `output/...`,

&nbsp; - any generated/updated files,

&nbsp; - archived prompt file.



This section should read like a step-by-step narrative for someone

who wants to understand exactly how one task flows through the system.





\## 5. Security, secrets, and risk considerations



Provide a short audit-style subsection:



\- How API keys and secrets are handled:

&nbsp; - `.env`, `.env.enc`, `env\_crypto.py`, environment variables.

\- How safe this is in terms of:

&nbsp; - not committing secrets to git,

&nbsp; - encryption at rest (even with a simple password),

&nbsp; - risk if `.env` is left undeleted.

\- How safe the file-writing behavior is:

&nbsp; - could the Meta-Agent accidentally overwrite important files?

&nbsp; - what protections are in place (or missing)?

\- Any recommendations to improve robustness and safety.



\## 6. Limitations and extension points



List:



\- Current limitations of the Meta-Agent (e.g., performance of project scanning,

&nbsp; possible timeouts, lack of fine-grained access control, etc.).

\- Natural extension points for future work, particularly integration with:

&nbsp; - a Supervisor Agent,

&nbsp; - a trading bot like QuantumEdge.



Focus on concrete, code-based observations.





---



\# OUTPUT FORMAT



You must produce \*\*one Markdown documentation file\*\* inside the project, using the Meta-Agent file block convention.



Return your answer as:



```text

===FILE: output/meta\_agent\_audit\_and\_description.md===

<full markdown content of the audit and description>

Guidelines:



Use clear headings and subsections as described above.



The document should be understandable to a developer who has never seen

the Meta-Agent before.



Do NOT modify any other files in this stage.



Do NOT include any other file blocks besides output/meta\_agent\_audit\_and\_description.md.

