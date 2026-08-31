# Judge v3: repro (google/gemini-3.1-pro-preview)
_2026-08-31 13:17 UTC_

Here is the blind reproducibility audit based strictly on the provided `README.md`, `REPRODUCE.md`, `requirements.txt`, and `Makefile`. 

### 1. Step-by-Step Walkthrough & Friction Points

**Step 1: Setup**
*   `git clone <this-repo> && cd repowiki`
    *   **Friction (Placeholder):** `<this-repo>` is a placeholder. The judge must manually find and copy the repo URL.
    *   **Friction (Assumed Knowledge):** If the repository is named something like `micro1-challenge`, `cd repowiki` will fail unless the judge explicitly cloned it into a directory named `repowiki` (e.g., `git clone <url> repowiki`).
*   `python -m venv .venv && source .venv/bin/activate`
    *   *Pass.* (Good OS-specific note for Windows included).
*   `pip install -r requirements.txt`
    *   **Friction (Missing Prerequisite):** The `Makefile` includes a `test` target that runs `pytest`, but `pytest` is missing from `requirements.txt`.
*   `cp .env.example .env`
    *   **Friction (OS-Specific):** `cp` is a Unix command. While the docs specify "Windows 11 (git-bash)", a judge running standard Windows CMD or PowerShell will hit an error here.
    *   **Friction (Missing Prerequisite / Assumed Knowledge):** The setup instructs the user to put their API key in `.env`. However, **`python-dotenv` is missing from `requirements.txt`**. Standard Python and the `openai` package do *not* automatically load `.env` files. Unless the codebase contains a custom `.env` parser, every LLM call will fail with `openai.AuthenticationError` because the environment variable is never actually loaded into the shell.

**Step 2: Smoke test**
*   `python -m repowiki index https://github.com/psf/requests`
    *   *Pass.* (Assuming the package structure is correct and this truly requires no LLM/API key as claimed).

**Step 3: One wiki**
*   `python -m repowiki generate https://github.com/psf/requests --mode advanced`
    *   **Friction (Execution Failure):** If `python-dotenv` is missing and the user didn't manually `export` the variables from `.env`, this will immediately crash with an Authentication Error.

**Step 4: The full evaluation**
*   `python -m evals.runner --repos https://github.com/psf/requests,<starter-repo-url>`
    *   **Friction (Wrong Command):** The README explicitly states the evaluation script is `evals/parallel_runner.py`. The REPRODUCE guide tells the user to run `python -m evals.runner`. This will likely throw a `ModuleNotFoundError: No module named evals.runner`.
    *   **Friction (Placeholder):** `<starter-repo-url>` is a placeholder. The judge has to guess what repo to put here to make the command run.
    *   **Friction (Time/Output Surprise):** The text claims this runs "12 repos × 2 modes" and takes "~40 minutes". However, the command explicitly restricts the run to exactly **2 repos** via the `--repos` flag. 

**Step 5: Trajectories**
*   `python -c "from repowiki.trajectory import render_file; print(render_file('<path>.jsonl'))"`
    *   **Friction (Placeholder):** `<path>.jsonl` is a placeholder. The judge must manually list the `trajectories/` directory, copy a generated filename, and paste it into this inline script.

---

### 2. Core Questions

**Does the README's own eval command actually work as written?**
**No.** 
1. It uses a placeholder (`<starter-repo-url>`) which will cause a parsing error or a failed git clone.
2. There is a module name mismatch (`evals.runner` vs `evals/parallel_runner.py`). 
3. It will likely fail with an `AuthenticationError` because the `.env` file is created but never loaded (missing `python-dotenv` or `source .env` instructions).

**Does the claimed output match what the commands produce?**
**No.** 
The REPRODUCE guide claims the eval command will produce a summary table for "12 repos × 2 modes". However, the provided command (`--repos https://github.com/psf/requests,<starter-repo-url>`) explicitly limits the evaluation to only 2 repositories. Furthermore, the README claims the evaluation was run on "10 repos" in one section, and "12 public repos" in another, creating a documentation inconsistency.

---

### 3. Reproducibility Score: 8 / 15

**Breakdown:**
*   **Documentation & Clarity (+4/5):** Excellent conceptual documentation. The "honesty notes" are a fantastic touch, and the architecture is explained clearly. Lost a point for inconsistent repo counts (10 vs 12) and heavy use of placeholders instead of copy-pasteable commands.
*   **Setup & Dependencies (+2/5):** Pinned dependencies are good, but missing `python-dotenv` is a fatal flaw for a tool relying on a `.env` file. Missing `pytest` breaks the Makefile.
*   **Execution & Correctness (+2/5):** The eval command is broken as written (module mismatch + placeholder). The output of the eval command will not match the 12-repo claim. 

**Judge's Advice:** 
To fix this, add `python-dotenv` to `requirements.txt`, ensure `evals.runner` matches the actual filename, remove all `<placeholders>` in favor of exact copy-pasteable commands, and align the 10 vs 12 repo claims.