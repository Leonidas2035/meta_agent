\# ROLE

You are Codex running inside the Meta-Agent.



Your task is to update the Meta-Agent project to support automatic task archiving

and simple task management.



\# TASK

Make the following modifications:



1\. Create a new file task\_archiver.py with this exact content:



<INSERT SCRIPT HERE — meta-agent will replace automatically>



2\. Modify meta\_agent.py:

&nbsp;  - Import archive\_completed\_tasks at the top:

&nbsp;       from task\_archiver import archive\_completed\_tasks

&nbsp;  - At the very end of the run() method, add:

&nbsp;       print("\\n=== Archiving completed tasks ===")

&nbsp;       archive\_completed\_tasks()



3\. Do not modify any other logic.

4\. Ensure that after each stage, all prompt files are automatically moved

&nbsp;  from prompts/ to archives/ with a timestamp prefix.



\# OUTPUT FORMAT

Return a single file block with updated code files exactly in this format:



===FILE: task\_archiver.py===

<content>



===FILE: meta\_agent.py===

<updated content>



