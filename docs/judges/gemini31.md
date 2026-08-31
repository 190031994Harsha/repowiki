# Judge: gemini31 (google/gemini-3.1-pro-preview)
_Role: enduser-realist · 2026-08-31 05:35 UTC_

Here is the critique from the perspective of the intended user—the new engineer who just inherited this codebase.

### 1. Verdict
Repowiki brilliantly solves the "hallucinated line numbers" problem with its deterministic AST resolver, making it a wiki I can actually trust, but its 4MB file cap and shallow regex-parsing for non-Python languages mean it will likely choke on the massive, polyglot enterprise monorepo I was actually hired to work on.

### 2. Score Breakdown: 16/20 (End-to-End Quality)
As a user, I don't care about the prompt engineering; I care if this saves me two weeks of archaeology. 

*   **Trust & Grounding (5/5):** *Would I actually read this?* Yes. The fact that I can click a link and land on the exact line of code—and trust that the tool verified it—is a game-changer. Standard LLM docs rot instantly; these are anchored.
*   **Answering Real Questions (4/5):** 
    *   *Where do I start?* Yes, the `overview` and `onboarding` pages handle this perfectly.
    *   *What breaks if I touch X?* Mostly yes. The module deep-dives and import graphs help, but the reliance on static call graphs means it misses dynamic edges (metaprogramming, dependency injection), which is exactly where I need the most help.
    *   *Why is it built this way?* **No.** It tells me *what* the code does, but an AST parser cannot infer business logic, historical tech debt, or product requirements. 
*   **Completeness & Missing Pages (3/5):** *What page is missing?* Two critical ones: **"Testing & CI/CD"** (how do I actually run and deploy this thing?) and **"Historical Context / Gotchas"** (why didn't we just use Postgres?). Also, consolidating the "long tail" of modules into a single `module-other` page hides the weird edge cases I usually get assigned to fix first.
*   **Real-World Applicability (4/5):** The 4MB truncation cap is a massive blind spot for real-world enterprise use. If I inherit a 50MB repository, this tool gives up on the bulk of it.

### 3. The 3 Most Likely Reasons This Loses
1.  **The 4MB / Monorepo Cap:** You built a tool for "the engineer who just inherited a codebase," but real inherited codebases are often massive. Truncating at 4MB and skeletonizing files means the LLM is missing the very complexity the engineer needs help untangling. 
2.  **Python Bias (Second-Class Polyglot Support):** Modern codebases are rarely one language. If my backend is Python but my frontend is a massive TypeScript React app, the TS side only gets "honest structural scanning" (regex). Missing the call graph for JS/TS/Java/Go severely cripples the `data-flow` pages for the majority of enterprise users.
3.  **Missing the "Why" (Context Vacuum):** The wiki is perfectly grounded in the AST, but code is only half the story. Because it only reads code, it hallucinates or ignores the *business intent*. It maps the territory but doesn't explain why the borders were drawn that way.

### 4. The 3 Highest-Leverage Fixes
1.  **Swap Regex for Tree-sitter:** You mentioned this in your "What we would do with another week" section, and you are 100% right. Implementing Tree-sitter would immediately give you robust ASTs, call graphs, and exact line ranges for JS, TS, Go, Rust, and Java. This elevates the tool from a "Python tool" to a "Universal tool."
2.  **Map-Reduce / Hierarchical Generation for Large Repos:** Instead of a hard 4MB cap, implement a map-reduce pipeline. Have the LLM summarize individual directories first, then roll those summaries up into the global context. This solves the monorepo problem without blowing up the context window.
3.  **Ingest Non-Code Context:** Allow the ingest step to optionally pull the last 50 merged PR descriptions or closed Issues from GitHub. Injecting this into the planner LLM's context would allow it to generate a "Historical Context" page, finally answering *why* the code looks the way it does.

### 5. What Would Make This WIN
The gap between this and a first-prize submission is the transition from a **"Code Summarizer"** to a **"Tribal Knowledge Engine."** 

Right now, Repowiki is an incredibly robust, hallucination-free code summarizer. To win, it needs to handle a 50MB polyglot monorepo without breaking a sweat (via Tree-sitter and Map-Reduce) and it needs to bridge the gap between the AST and the business logic. If you can prove that Repowiki not only maps the code but accurately explains *why* a bizarre architectural decision was made (by synthesizing code with commit history/PRs), no other submission would even come close. 

*(Note: Your `repowiki/advanced.py` file in the submission bundle truncates abruptly at `Write architecture.md: c`. While judges will likely overlook this as a copy-paste error in the bundle compilation, ensure your actual repo is intact!)*