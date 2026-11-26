# Numbers ledger and story bible: PH-TECH-MID-002 (Ace Canacan, fictional persona)

Purpose: a consistency reference for the ResumeForge record. Every number on the resume has a row here saying what it counts, over what period, and how it squares with the other numbers. Nothing here is on the resume itself.

## Timeline (fixed)
| Dates | Employer | Type | Months |
|---|---|---|---|
| 2023-05 → 2023-11 | Eskwelabs | Internship | 7 |
| 2024-01 → 2024-09 | Saltgum Supply (fictional AU outdoor-gear Shopify brand) | Freelance | 9 |
| 2024-10 → 2025-05 | Casefront Legal Marketing (fictional Texas PI-firm marketing agency) | Contract | 8 |
| 2025-06 → 2026-11 (ended; owner's decision 2026-11-27) | Those Who Care Co (fictional Florida outpatient practice) | Full-time | 18 |

Covered months: 42 → 3.5 years. Gap months: 2023-12 only.

## Experience claims in the summary
| Claim | Check |
|---|---|
| "3.5 years in Python and workflow automation" | 42 covered months; Python used from the internship onward. |
| "2.5 years shipping Claude API integrations and self-hosted n8n workflows" | n8n from 2024-01 (2.9 yrs). Claude tool use from its 2024-04 beta, used at Saltgum from 2024-05 (2.5 yrs). Agents proper start at Casefront (2024-10), so the summary says "integrations" for the 2.5 years and "Builds AI agents" separately. |

## Those Who Care Co (2025-06 → 2026-11)
Setting: outpatient practice with a 4-person intake team. Before Ace: web forms and faxes read by hand, replies typed from templates in GoHighLevel.
Hosting: n8n self-hosted on Docker in a US AWS region, so patient data stays in the US.
Data flow: web forms and cloud-fax PDFs → OCR → pattern-based masking of direct identifiers (name, DOB, phone, member ID; member ID is parsed by rule, never by the model) → Claude extracts payer, referral, and visit reason from the masked text → results re-linked by record ID.
Build order: intake pipeline (2025-07 to 09) → identifier masking and request logging (2025-08, before go-live with patient data) → routing agent (2025-10 to 12) → eval harness and prompt versioning (2025-11 onward) → MCP server (2026-Q1) → Claude Code standardization with Agent Skills (after their 2025-10 release; in place by 2026-Q1).

| Number | What it counts | Consistency |
|---|---|---|
| 1,900 yearly web forms and faxes | Web-form plus fax inquiries through the pipeline in the latest 12 months | ≈158/month, ≈7.5 per working day across 4 intake staff, who also schedule and verify insurance. |
| 96% staff-verified accuracy | Share of extracted fields that intake staff confirm without correction | Field-level, not inquiry-level; 3 fields named (payer, referral, visit reason). |
| 13 → 6 minutes, in 3 months | Median business-hours first-reply time on web inquiries, the 3 months before vs. after the routing agent | Baseline 13 is the post-pipeline figure, so it does not clash with any earlier number. |
| 7 tools, 3 systems | MCP tools: 3 scheduling, 2 eligibility, 2 intake-status. Systems: GoHighLevel, the scheduling system, the eligibility tracker | Tools serve the routing agent and return record IDs and status codes only. |
| 72% → 91% | Share of AI first drafts that staff approve without rewriting, first vs. latest release | Measured from the approval step; the eval harness is what drove prompt changes. |
| 250 drafts per release | Size of the replayed draft set scored by the harness each release | Separate from the open-source kit's 120 synthetic scenarios. |
| 14 releases, 9 → 4 working days | n8n automations shipped in 18 months; build-to-live time before vs. after the Claude Code setup | ≈0.8 releases a month, realistic for one engineer. |

Unquantified bullet: identifier masking and HIPAA audit-control logging (scope bullet, no number).

## Casefront Legal Marketing (2024-10 → 2025-05)
Setting: agency serving roughly 30 law-firm clients; 9 personal-injury firms opted into AI triage. Ace was the only engineer.
Build order: triage agent (2024-10 to 12) → deadline and name-match flags (2025-01) → approval queue (2025-01 onward) → MCP server (2025-02 to 04; MCP was released 2024-11-25, used through Claude Desktop local config; read-only database role).

| Number | What it counts | Consistency |
|---|---|---|
| 9 firms, 3,200 web leads | Leads triaged over 8 months | 400/month, ≈44 per firm per month. |
| misclassifying under 3% | Leads later re-tagged to a different case type by firm staff | Fewer than 96 leads. |
| 25 → 8 minutes | Intake staff screening time per lead, before vs. after pre-filled flags (adverse-party names, incident dates near the 2-year limit) | 3,200 × 17 min ≈ 900 staff hours saved across 9 firms over 8 months. |
| 84% of 2,100 drafts | AI-drafted follow-ups sent without edits | 2,100 of 3,200 leads got a draft (the rest were spam, duplicates, or declined at triage); queue ran from 2025-01. |

Unquantified bullet: first MCP server and account-manager onboarding (scope bullet).

## Saltgum Supply (2024-01 → 2024-09)
Setting: Australian outdoor-gear brand on Shopify with a 6-person CX team using Gorgias.
Hosting: n8n self-hosted on Docker. Trigger: Gorgias HTTP integrations call n8n on ticket events; n8n reads return status from the Shopify GraphQL Admin API.
Build order: CX queue audit and ticket triage (2024-01 to 04) → refund routing (2024-04 to 06) → listing enrichment with Claude tool use (2024-06 to 08; tool use entered public beta 2024-04-04 and went GA 2024-05-30).

| Number | What it counts | Consistency |
|---|---|---|
| 2,400 monthly tickets, 6-person team | Gorgias tickets tagged by the triage workflows | 400 per agent per month, ≈19 per working day. |
| 1,150 variant listings | Variant-level listings enriched | 3 days → 5 hours is per catalog drop. |
| 4.2 → 1.6 days | Average time from refund request to resolution | Same unit both sides. |

## Eskwelabs (2023-05 → 2023-11)
| Number | What it counts | Consistency |
|---|---|---|
| 240 firms → 180 accounts → 18 quote requests | Researched, qualified, and converted counts for the construction-supply partner | 75% qualified; 10% of qualified accounts requested a quote. |
| 4 hours weekly | Manual list preparation time removed by the Python scripts | Small, intern-scale saving. |

## Projects
| Number | What it counts | Consistency |
|---|---|---|
| 37 risky changes, 3 Git repositories | Workflow changes denied by the PreToolUse hook before release | Built after Agent Skills shipped (2025-10-16); repositories are the practice's workflow repos. |
| 120 scenarios, under 4 minutes | Synthetic cases in the open kit and its CI run time | Synthetic data only, so structured outputs are used here with no patient data. |

## Skill years (as of 2026-11; stored in the record, not printed)
| Skill | Years | Ceiling |
|---|---|---|
| Claude Code (Subagents, Hooks, Agent Skills) | 1.4 | Role start 2025-06; GA 2025-05-22. |
| Claude API (Tool Use, Prompt Engineering) | 2.5 | Tool use beta 2024-04-04. |
| MCP Servers | 1.8 | MCP released 2024-11-25 (2.0 max). |
| Structured Outputs | 0.8 | Beta 2025-11-14 (1.0 max); used only with synthetic data in the eval kit. |
| n8n (Self-Hosted, Error Handling) | 2.8 | Since 2024-01 (2.9 max). |
| REST APIs, Webhooks | 2.8 each | Since 2024-01. |
| GoHighLevel (CRM) | 1.4 | Those Who Care Co role only. |
| Shopify Admin API (GraphQL) | 0.7 | Saltgum only (9 months). |
| Python | 3.5 | Since the internship. |
| TypeScript / JavaScript (Node.js) | 1.4 | Those Who Care Co role (MCP server). |
| PostgreSQL (SQL) | 0.6 | Casefront. |
| Docker | 2.8 | Self-hosted n8n since 2024-01. |
| AWS | 1.4 | Those Who Care Co role (US-region hosting). |
| GitHub Actions | 1.0 | Eval kit CI. |
| Evals / Human-in-the-Loop Review | 1.9 | Approval queue from 2025-01 at Casefront. |
| PHI Masking / HIPAA Audit Controls | 1.4 | Those Who Care Co role. |
