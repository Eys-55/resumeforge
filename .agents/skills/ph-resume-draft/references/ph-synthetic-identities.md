# Synthetic Filipino Identities & Naming Conventions

All resumes stored in ResumeForge represent **100% fictional characters** tailored for the game pool.

## Mandatory Synthetic Contact Rules (Enforced by `tools/pii_guard.py`)

- **Email:** `<firstname>.<lastname>@example.ph` (allowed domains: `example.ph`, `example.com`, `synthetic.ph`).
- **Phone:** `+63 9XX 000 XXXX` where the middle 3 digits are **strictly `000`** (e.g., `+63 917 000 4821`, `+63 928 000 7319`, `+63 995 000 1046`).
- **LinkedIn / Portfolio:** Slug-only (`linkedin_slug`: `firstname-lastname-role`) and synthetic URL (`https://example.ph/portfolio/<slug>`).
- **Location:** City + Region only (e.g., `Cebu City, Central Visayas`, `Taguig City, Metro Manila`, `Davao City, Davao Region`, `Pasig City, Metro Manila`, `Angeles City, Central Luzon`, `Iloilo City, Western Visayas`).

## Avoiding Cliché & Duplicate Personas

- **Never use:** `Juan Dela Cruz`, `Maria Clara`, `Pedro Penduko`, `Jose Rizal`, `John Doe`, `Jane Doe`.
- **Culturally authentic variety:** Mix contemporary Filipino first names and realistic Spanish/Filipino/Chinese-Filipino surnames naturally (e.g., `Paolo Mercado`, `Clarisse Villanueva`, `Miguelito Tan`, `Bianca Pangilinan`, `Jericho Dizon`, `Camille Navarro`, `Lorenzo Soriano`, `Trisha Magbanua`, `Rafael Bautista`, `Kristel Ocampo`).
- **Query SQL first** (`uv run resumeforge resume list`) to avoid repeating surnames, universities, or synthetic employer names inside the same niche.
- **Regional coherence:** Match degree alma mater plausibly with early-career city unless the candidate relocated to BGC/Makati/Cebu or works remotely from their home province (e.g., a UP Cebu or USC graduate working remotely from Cebu or relocating to Taguig).
