# Start Here: ResumeForge

ResumeForge is a set of AI skills for making resumes that get past ATS (applicant tracking system) filters. It does two things:

1. **Your own resume.** Builds a real, truthful, ATS-safe PDF for you and scores it against the job you want.
2. **The resume game.** Generates fictional, realistic Filipino "gold-standard" resumes for a game's resume pool, each one ATS-checked and independently reviewed.

It works best in **Claude Code**. Codex, Gemini CLI and other agents that read `AGENTS.md` can use it too.

## Setup (once, about 2 minutes)

You need:
- **uv**, the Python runner. Install: `curl -LsSf https://astral.sh/uv/install.sh | sh` on macOS/Linux, or `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows.
- **Google Chrome** (or Edge or Chromium), used to make the PDF.

Then unzip this folder, open a terminal in it, and run:

```bash
./setup.sh
```

On Windows, run `powershell -ExecutionPolicy Bypass -File setup.ps1`. You can also open the folder in Claude Code and type `/setup`.

## Make your resume

Open the folder in Claude Code and type:

```
/make-my-resume
```

Paste the job post you're aiming for, plus your old resume if you have one. Claude interviews you for anything missing and checks the draft. It ATS-scores the draft against the job, then hands you a PDF in `my_resumes/<your-name>/`.

Your details stay in `my_resumes/` on your computer. They never go into the game database.

## Check a resume you already have

```
/ats-check path/to/your-resume.pdf
```

Claude turns the job post into keywords and scores your file (0–100, aim for 80+). It also checks that an ATS can actually read the PDF.

## All commands

| Command | What it does |
|---|---|
| `/setup` | Installs and checks everything |
| `/make-my-resume` | Builds your own resume, ATS-checked, as a PDF |
| `/ats-check <file or resume code>` | Scores any resume against a job post |
| `/scout-niche` | Game: research PH job niches and role types |
| `/ingest-resume` | Game: learn structure from a pasted public resume (personal info is stripped) |
| `/draft-resume` | Game: create a fictional gold-standard resume |
| `/review-resume` | Game: independent audit and promotion to `gold_standard` |
| `/query-resumes` | Game: browse the pool and export JSON for the game engine |

## No AI agent? Use the command line

```bash
uv run resumeforge mine new "your name"
uv run resumeforge mine check my_resumes/your-name/resume.json
uv run resumeforge mine ats my_resumes/your-name/resume.json --job templates/job-keywords.example.json --one-page
uv run resumeforge ats score --resume some-resume.pdf --job job-keywords.json
```

## How the ATS score works

The score is deterministic (no AI) and weighted like common ATS matchers:
- **40%** job-post keywords found
- **20%** required skills present
- **15%** headline matches the posted job title
- **15%** standard sections and contact info
- **10%** clean, newest-first dates

A separate parse check reads the PDF's text layer the way an ATS does, and flags unreadable text, missing headings and broken ligatures.

The skills never add a keyword you don't actually have. An honest 75 beats a stuffed 95, because a human reads the resume after the ATS does.
