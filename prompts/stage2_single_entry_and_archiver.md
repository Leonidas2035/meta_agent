\## ROLE



You are Codex running \*\*inside the Meta-Agent project at C:/meta\_agent\*\*.



Your task in THIS STAGE is to upgrade the Meta-Agent task execution model so that:



1\. It can be used via a \*\*single “key” task file\*\* (for easy Supervisor integration).

2\. It automatically \*\*archives all consumed .md prompt files\*\* into a structured `prompts/archive/<job\_name>/...` hierarchy.

3\. It \*\*clears stages.yaml\*\* after running a stage pipeline, so each project run leaves a clean slate.

4\. It understands a \*\*Supervisor-specific task naming convention\*\* for `--task-file`:

&nbsp;  - filenames of the form `S<number><job\_name>.md`

&nbsp;  - where:

&nbsp;    - `S` prefix means the task was created by Supervisor,

&nbsp;    - `<number>` is an integer sequence (1, 2, 3, ...),

&nbsp;    - `<job\_name>` is the logical project/component name

&nbsp;      (e.g. `ai\_scalper\_bot`, `quantumedge\_risk`, etc.)

5\. It keeps all previously added features:

&nbsp;  - `--task-file` single-task mode,

&nbsp;  - YAML front matter parsing,

&nbsp;  - encrypted env using `.env.enc` with password `1111`.





---



\# OBJECTIVES



\## 1. Single “key task file” support



Introduce a default single-task file, for example:



\- `DEFAULT\_TASK\_FILE = "prompts/task\_current.md"`



in `meta\_agent.py` (near other module-level constants).



Update the CLI behavior in `main()` so that:



1\. If `--encrypt-env` is provided → keep existing behavior (encrypt and exit).



2\. Else if `--task-file` is provided → keep existing behavior:

&nbsp;  - run `MetaAgent().run\_task\_file(args.task\_file)`

&nbsp;  - exit with 0/1 according to success.



3\. Else (no special flags):

&nbsp;  - If `DEFAULT\_TASK\_FILE` exists on disk:

&nbsp;    - log something like:  

&nbsp;      `"\[INFO] Single-task mode: using prompts/task\_current.md"`

&nbsp;    - run exactly `MetaAgent().run\_task\_file(DEFAULT\_TASK\_FILE)`,

&nbsp;    - exit according to the result.

&nbsp;  - Else:

&nbsp;    - fall back to the legacy stage pipeline:

&nbsp;      - `MetaAgent().run\_stage\_pipeline()`, as it works now.



Requirements:



\- Do NOT break `--task-file` or `--encrypt-env`.

\- Single-task mode via `DEFAULT\_TASK\_FILE` must be fully non-interactive.

\- If `DEFAULT\_TASK\_FILE` does not exist, the behavior must be exactly as before

&nbsp; (stage pipeline using `stages.yaml`).





\## 2. Supervisor naming convention for --task-file and job\_name



Tasks submitted by the future Supervisor Agent will use a filename pattern:



\- `S<number><job\_name>.md`



Examples:



\- `S1ai\_scalper\_bot.md`

\- `S2quantumedge\_risk.md`

\- `S10meta\_refactor.md`



You must implement a helper that extracts `job\_name` from such filenames, e.g.:



```python

def extract\_job\_name\_from\_path(path: str) -> Optional\[str]:

&nbsp;   """

&nbsp;   If the basename of the given path matches the Supervisor pattern

&nbsp;   S<number><job\_name>.md, return <job\_name> (string).

&nbsp;   Otherwise return None.

&nbsp;   """

Rules:



Work on the basename only, e.g. S1ai\_scalper\_bot.md.



Pattern:



Starts with S



Followed by one or more digits (\\d+)



Followed by <job\_name> (one or more non-empty characters up to .md).



<job\_name> is everything AFTER the numeric part and BEFORE the .md extension.



For S1ai\_scalper\_bot.md → job\_name = ai\_scalper\_bot.



If the filename does not match this pattern, return None.



Integration:



When archiving a single task file (see below), first try to get job\_name

from extract\_job\_name\_from\_path(task\_path).



If job\_name is None, fall back to deriving job\_name from target\_project

(see next section) or "default" if needed.



This naming logic is especially important for tasks launched via --task-file

by Supervisor; it will allow us to track activity by <job\_name> in the archive

structure.



3\. Structured archiving of prompts and clearing stages.yaml

You already had a basic archive\_completed\_tasks in task\_archiver.py.

We will refactor it into a richer module.



3.1. Implement/replace task\_archiver.py

Create or update task\_archiver.py with the following behavior:



Provide two main functions:



python

Копіювати код

from typing import List, Dict, Optional



def archive\_stage\_prompts(

&nbsp;   stages: List\[Dict],

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   stages\_path: str = "stages.yaml",

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   ...

python

Копіювати код

def archive\_task\_file(

&nbsp;   task\_path: str,

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   ...

Keep a thin compatibility wrapper:



python

Копіювати код

def archive\_completed\_tasks(

&nbsp;   stages: Optional\[List\[Dict]] = None,

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   stages\_path: str = "stages.yaml",

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   """

&nbsp;   Backward compatible wrapper.

&nbsp;   If stages is None, try to load stages.yaml itself.

&nbsp;   Then delegate to archive\_stage\_prompts(...).

&nbsp;   """

&nbsp;   ...

3.2. Job name selection and archive folder

Both archive\_stage\_prompts and archive\_task\_file must use the same job-name logic:



Try to derive job\_name from Supervisor filename pattern:



For archive\_task\_file(...), call extract\_job\_name\_from\_path(task\_path).



For archive\_stage\_prompts(...), you may:



either ignore Supervisor pattern and use only target\_project,



or additionally attempt pattern matching on each stage\["prompt"] basename

(optional but allowed).



If a valid job\_name is found, use it.



If no Supervisor-style name is present (or pattern did not match):



If target\_project is given:



derive job\_name from os.path.basename(os.path.abspath(target\_project)),

or "default" if that’s empty.



If target\_project is None, use "default".



Destination directory:



python

Копіювати код

dest\_dir = os.path.join(archive\_root, job\_name)

os.makedirs(dest\_dir, exist\_ok=True)

3.3. Archiving stage prompts

In archive\_stage\_prompts(...):



Iterate over stages list.



For each entry:



prompt = stage.get("prompt")



If prompt is a non-empty string and the file exists:



src = prompt



dst = os.path.join(dest\_dir, os.path.basename(prompt))



If dst already exists, add a numeric suffix (filename(1).md, filename(2).md, etc.).



Move via shutil.move(src, dst).



Log:



"\[INFO] Archived prompt {src} -> {dst}"



After archiving all prompts:



Clear stages\_path by overwriting it with an empty list:



python

Копіювати код

with open(stages\_path, "w", encoding="utf-8") as handle:

&nbsp;   handle.write("\[]\\n")

If writing fails, log a warning and continue; do not crash the Meta-Agent.



3.4. Archiving a single task file

In archive\_task\_file(...):



If task\_path does not exist, log a warning and return.



Determine job\_name as described in 3.2 (Supervisor pattern first, then target\_project, then "default").



Compute dst = os.path.join(dest\_dir, os.path.basename(task\_path)).



Handle collisions like in archive\_stage\_prompts.



Move via shutil.move(task\_path, dst).



Log a short info message on success.



4\. Integrate archiver and naming into Meta-Agent

Update meta\_agent.py:



Change imports:



python

Копіювати код

\# existing (if present)

from task\_archiver import archive\_completed\_tasks



\# updated

from task\_archiver import (

&nbsp;   archive\_completed\_tasks,

&nbsp;   archive\_stage\_prompts,

&nbsp;   archive\_task\_file,

)

In run\_stage\_pipeline(self):



You already load stages and target\_project (or similar).



After the pipeline successfully finishes, instead of:



python

Копіювати код

try:

&nbsp;   archive\_completed\_tasks()

except Exception as exc:

&nbsp;   print(f"\[WARN] Archiving failed: {exc}")

use:



python

Копіювати код

try:

&nbsp;   archive\_stage\_prompts(stages, target\_project=target\_project)

except Exception as exc:

&nbsp;   print(f"\[WARN] Archiving failed: {exc}")

In run\_task\_file(self, task\_path: str):



Once the task has successfully completed (after you print something like

\[INFO] Task {task\_id} completed.), add:



python

Копіювати код

try:

&nbsp;   archive\_task\_file(task\_path, target\_project=target\_project)

except Exception as exc:

&nbsp;   print(f"\[WARN] Failed to archive task file {task\_path}: {exc}")

Here, target\_project should be the one you derive from the YAML front

matter (target\_project field), or None if absent.



This ensures:



Any single-task execution (via --task-file or via DEFAULT\_TASK\_FILE)

will result in the .md moving into prompts/archive/<job\_name>/...,

where <job\_name> comes from the Supervisor pattern when available.



5\. Preserve existing behavior

Do NOT remove or break:



--task-file CLI argument.



YAML front matter handling via load\_task\_from\_file.



Encrypted env behavior via .env.enc and password 1111.



Existing stage pipeline logic when no DEFAULT\_TASK\_FILE is present.



Do NOT modify any code outside C:/meta\_agent.



Keep the business logic minimal: the goal is orchestration and archiving,

not changing Codex prompt semantics.



OUTPUT FORMAT

Return the complete updated code files using the Meta-Agent file block convention.



Your response MUST consist of one or more file blocks of the form:



text

Копіювати код

===FILE: meta\_agent.py===

<full updated content of meta\_agent.py>



===FILE: task\_archiver.py===

<full updated content of task\_archiver.py>

Include any other changed files (if absolutely necessary) in the same format.

Do NOT include files you did not change.



All Python must be valid for Python 3.12–3.14.



yaml

Копіювати код

&nbsp;ROLE



You are Codex running \*\*inside the Meta-Agent project at C:/meta\_agent\*\*.



Your task in THIS STAGE is to upgrade the Meta-Agent task execution model so that:



1\. It can be used via a \*\*single “key” task file\*\* (for easy Supervisor integration).

2\. It automatically \*\*archives all consumed .md prompt files\*\* into a structured `prompts/archive/<job\_name>/...` hierarchy.

3\. It \*\*clears stages.yaml\*\* after running a stage pipeline, so each project run leaves a clean slate.

4\. It understands a \*\*Supervisor-specific task naming convention\*\* for `--task-file`:

&nbsp;  - filenames of the form `S<number><job\_name>.md`

&nbsp;  - where:

&nbsp;    - `S` prefix means the task was created by Supervisor,

&nbsp;    - `<number>` is an integer sequence (1, 2, 3, ...),

&nbsp;    - `<job\_name>` is the logical project/component name

&nbsp;      (e.g. `ai\_scalper\_bot`, `quantumedge\_risk`, etc.)

5\. It keeps all previously added features:

&nbsp;  - `--task-file` single-task mode,

&nbsp;  - YAML front matter parsing,

&nbsp;  - encrypted env using `.env.enc` with password `1111`.





---



\# OBJECTIVES



\## 1. Single “key task file” support



Introduce a default single-task file, for example:



\- `DEFAULT\_TASK\_FILE = "prompts/task\_current.md"`



in `meta\_agent.py` (near other module-level constants).



Update the CLI behavior in `main()` so that:



1\. If `--encrypt-env` is provided → keep existing behavior (encrypt and exit).



2\. Else if `--task-file` is provided → keep existing behavior:

&nbsp;  - run `MetaAgent().run\_task\_file(args.task\_file)`

&nbsp;  - exit with 0/1 according to success.



3\. Else (no special flags):

&nbsp;  - If `DEFAULT\_TASK\_FILE` exists on disk:

&nbsp;    - log something like:  

&nbsp;      `"\[INFO] Single-task mode: using prompts/task\_current.md"`

&nbsp;    - run exactly `MetaAgent().run\_task\_file(DEFAULT\_TASK\_FILE)`,

&nbsp;    - exit according to the result.

&nbsp;  - Else:

&nbsp;    - fall back to the legacy stage pipeline:

&nbsp;      - `MetaAgent().run\_stage\_pipeline()`, as it works now.



Requirements:



\- Do NOT break `--task-file` or `--encrypt-env`.

\- Single-task mode via `DEFAULT\_TASK\_FILE` must be fully non-interactive.

\- If `DEFAULT\_TASK\_FILE` does not exist, the behavior must be exactly as before

&nbsp; (stage pipeline using `stages.yaml`).





\## 2. Supervisor naming convention for --task-file and job\_name



Tasks submitted by the future Supervisor Agent will use a filename pattern:



\- `S<number><job\_name>.md`



Examples:



\- `S1ai\_scalper\_bot.md`

\- `S2quantumedge\_risk.md`

\- `S10meta\_refactor.md`



You must implement a helper that extracts `job\_name` from such filenames, e.g.:



```python

def extract\_job\_name\_from\_path(path: str) -> Optional\[str]:

&nbsp;   """

&nbsp;   If the basename of the given path matches the Supervisor pattern

&nbsp;   S<number><job\_name>.md, return <job\_name> (string).

&nbsp;   Otherwise return None.

&nbsp;   """

Rules:



Work on the basename only, e.g. S1ai\_scalper\_bot.md.



Pattern:



Starts with S



Followed by one or more digits (\\d+)



Followed by <job\_name> (one or more non-empty characters up to .md).



<job\_name> is everything AFTER the numeric part and BEFORE the .md extension.



For S1ai\_scalper\_bot.md → job\_name = ai\_scalper\_bot.



If the filename does not match this pattern, return None.



Integration:



When archiving a single task file (see below), first try to get job\_name

from extract\_job\_name\_from\_path(task\_path).



If job\_name is None, fall back to deriving job\_name from target\_project

(see next section) or "default" if needed.



This naming logic is especially important for tasks launched via --task-file

by Supervisor; it will allow us to track activity by <job\_name> in the archive

structure.



3\. Structured archiving of prompts and clearing stages.yaml

You already had a basic archive\_completed\_tasks in task\_archiver.py.

We will refactor it into a richer module.



3.1. Implement/replace task\_archiver.py

Create or update task\_archiver.py with the following behavior:



Provide two main functions:



python

Копіювати код

from typing import List, Dict, Optional



def archive\_stage\_prompts(

&nbsp;   stages: List\[Dict],

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   stages\_path: str = "stages.yaml",

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   ...

python

Копіювати код

def archive\_task\_file(

&nbsp;   task\_path: str,

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   ...

Keep a thin compatibility wrapper:



python

Копіювати код

def archive\_completed\_tasks(

&nbsp;   stages: Optional\[List\[Dict]] = None,

&nbsp;   target\_project: Optional\[str] = None,

&nbsp;   stages\_path: str = "stages.yaml",

&nbsp;   prompts\_root: str = "prompts",

&nbsp;   archive\_root: str = "prompts/archive",

) -> None:

&nbsp;   """

&nbsp;   Backward compatible wrapper.

&nbsp;   If stages is None, try to load stages.yaml itself.

&nbsp;   Then delegate to archive\_stage\_prompts(...).

&nbsp;   """

&nbsp;   ...

3.2. Job name selection and archive folder

Both archive\_stage\_prompts and archive\_task\_file must use the same job-name logic:



Try to derive job\_name from Supervisor filename pattern:



For archive\_task\_file(...), call extract\_job\_name\_from\_path(task\_path).



For archive\_stage\_prompts(...), you may:



either ignore Supervisor pattern and use only target\_project,



or additionally attempt pattern matching on each stage\["prompt"] basename

(optional but allowed).



If a valid job\_name is found, use it.



If no Supervisor-style name is present (or pattern did not match):



If target\_project is given:



derive job\_name from os.path.basename(os.path.abspath(target\_project)),

or "default" if that’s empty.



If target\_project is None, use "default".



Destination directory:



python

Копіювати код

dest\_dir = os.path.join(archive\_root, job\_name)

os.makedirs(dest\_dir, exist\_ok=True)

3.3. Archiving stage prompts

In archive\_stage\_prompts(...):



Iterate over stages list.



For each entry:



prompt = stage.get("prompt")



If prompt is a non-empty string and the file exists:



src = prompt



dst = os.path.join(dest\_dir, os.path.basename(prompt))



If dst already exists, add a numeric suffix (filename(1).md, filename(2).md, etc.).



Move via shutil.move(src, dst).



Log:



"\[INFO] Archived prompt {src} -> {dst}"



After archiving all prompts:



Clear stages\_path by overwriting it with an empty list:



python

Копіювати код

with open(stages\_path, "w", encoding="utf-8") as handle:

&nbsp;   handle.write("\[]\\n")

If writing fails, log a warning and continue; do not crash the Meta-Agent.



3.4. Archiving a single task file

In archive\_task\_file(...):



If task\_path does not exist, log a warning and return.



Determine job\_name as described in 3.2 (Supervisor pattern first, then target\_project, then "default").



Compute dst = os.path.join(dest\_dir, os.path.basename(task\_path)).



Handle collisions like in archive\_stage\_prompts.



Move via shutil.move(task\_path, dst).



Log a short info message on success.



4\. Integrate archiver and naming into Meta-Agent

Update meta\_agent.py:



Change imports:



python

Копіювати код

\# existing (if present)

from task\_archiver import archive\_completed\_tasks



\# updated

from task\_archiver import (

&nbsp;   archive\_completed\_tasks,

&nbsp;   archive\_stage\_prompts,

&nbsp;   archive\_task\_file,

)

In run\_stage\_pipeline(self):



You already load stages and target\_project (or similar).



After the pipeline successfully finishes, instead of:



python

Копіювати код

try:

&nbsp;   archive\_completed\_tasks()

except Exception as exc:

&nbsp;   print(f"\[WARN] Archiving failed: {exc}")

use:



python

Копіювати код

try:

&nbsp;   archive\_stage\_prompts(stages, target\_project=target\_project)

except Exception as exc:

&nbsp;   print(f"\[WARN] Archiving failed: {exc}")

In run\_task\_file(self, task\_path: str):



Once the task has successfully completed (after you print something like

\[INFO] Task {task\_id} completed.), add:



python

Копіювати код

try:

&nbsp;   archive\_task\_file(task\_path, target\_project=target\_project)

except Exception as exc:

&nbsp;   print(f"\[WARN] Failed to archive task file {task\_path}: {exc}")

Here, target\_project should be the one you derive from the YAML front

matter (target\_project field), or None if absent.



This ensures:



Any single-task execution (via --task-file or via DEFAULT\_TASK\_FILE)

will result in the .md moving into prompts/archive/<job\_name>/...,

where <job\_name> comes from the Supervisor pattern when available.



5\. Preserve existing behavior

Do NOT remove or break:



--task-file CLI argument.



YAML front matter handling via load\_task\_from\_file.



Encrypted env behavior via .env.enc and password 1111.



Existing stage pipeline logic when no DEFAULT\_TASK\_FILE is present.



Do NOT modify any code outside C:/meta\_agent.



Keep the business logic minimal: the goal is orchestration and archiving,

not changing Codex prompt semantics.



OUTPUT FORMAT

Return the complete updated code files using the Meta-Agent file block convention.



Your response MUST consist of one or more file blocks of the form:



text

Копіювати код

===FILE: meta\_agent.py===

<full updated content of meta\_agent.py>



===FILE: task\_archiver.py===

<full updated content of task\_archiver.py>

Include any other changed files (if absolutely necessary) in the same format.

Do NOT include files you did not change.



All Python must be valid for Python 3.12–3.14.



yaml

Копіювати код



