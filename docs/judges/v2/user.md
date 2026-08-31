# Judge v2: user (google/gemini-3.1-pro-preview)
_2026-08-31 12:14 UTC_

As a new engineer inheriting this codebase, here is my honest assessment of these wiki pages. 

### Would I trust this enough to make my first commit?
**No.** I would use this as a highly accurate treasure map to open the right files, but I wouldn't trust it to understand the *blast radius* of my changes. It tells me exactly *where* things are, but explains almost nothing about the invariants, edge cases, or state management required to modify them safely. 

### Where do I start?
I start at the **Data Flow** section in `module-src-requests.md`. 
This is the single best piece of documentation provided. It breaks the request lifecycle into four concrete steps (User creates request -> Session prepares it -> Adapter sends it -> Server returns response). This immediately gives me the mental model I need to read the code.

### What are the load-bearing pieces?
According to the docs, the core triad is:
1. **`models.py`**: Holds the state of the request/response cycle (builder, finalized request, server response).
2. **`sessions.py`**: The heavy lifter for state. It manages the persistent connection pool, cookies, auth, proxies, and redirect chains.
3. **`adapters.py`**: The actual transport layer that talks to `urllib3` and handles retries.

### What breaks if I change `Session.send`?
**The docs completely fail to answer this.** 
The word `send` does not appear anywhere in these pages. I can infer from the Data Flow section that `sessions.py` hands off to `adapters.py` (Step 2 to Step 3), and that redirects (`sessions.py:127-392`) and auth (`auth.py:85-113`) are involved in the lifecycle, but I have no idea what methods call what. There is no call graph or method-level documentation.

### What's the most useful page?
**`module-src-requests.md`**. 
While `overview.md` is just a glorified table of contents with a basic README-style quickstart, the module page actually attempts to explain how the system fits together via the "Data Flow" and "Key Interactions" sections. Knowing that Adapters use `utils.py` for content-length headers is exactly the kind of tribal knowledge I need.

### What's missing that I need on day one?
1. **Actual Class and Function Names!** 
   The way these citations are injected is actively hostile to human reading. Look at this sentence from the Data Flow section: 
   > *"1. User creates `src/requests/models.py:284-375`"*
   
   Creates *what*? A `Request` object? A `PreparedRequest`? The generator replaced the actual symbol names with line numbers. I cannot grep the codebase for `src/requests/models.py:284-375`. I need it to say: *"User creates a `Request` object (`models.py:284-375`)"*.
2. **Exception / Error Handling:** What happens when a connection drops? What custom exceptions does this library raise? 
3. **Testing Instructions:** `overview.md` tells me tests live in `tests/test_requests.py`, but doesn't tell me how to run them (e.g., `pytest`, `tox`?). I can't make a commit if I don't know how to run the test suite.

---

### End-to-End Quality Score: 11 / 20

**The Good (+11):** 
It successfully maps a complex codebase into logical domains (Transport, Sessions, Models, Auth). The "Data Flow" and "Key Interactions" sections are genuinely valuable for onboarding. If I need to figure out how redirects work, I know exactly where to look (`sessions.py:127-392`).

**The Bad (-9):** 
The prose is practically unreadable because it strips out the actual nouns (class/method names) and replaces them with raw file coordinates. It reads like a machine-generated debugging log rather than an engineering guide. It gives me the boundaries of the code blocks, but zero context on the *logic* inside them, leaving me blind to the side-effects of any changes I might make.