# Fact ledger: AI Automations Engineer resume (synthetic persona)

Checked 2026-11-26. Every date below comes from a fetched source, not memory. Verdicts: **OK** (claim holds), **FIX** (wrong or would be read as wrong by a practitioner), **RISKY** (defensible only with a caveat or rewording). Anything I could not source is marked **UNVERIFIED** and collected again at the bottom.

Method notes that affect confidence:
- Claude Code version numbers come from the official CHANGELOG.md, which has no dates. Dates for those versions come from a third-party tracker (havoptic.com) and, where available, Anthropic blog posts. They agree wherever both exist.
- Anthropic's BAA article was read through a summarising fetch tool. The coverage tables are reported as that tool returned them; re-read the page before quoting it verbatim.
- Company-name checks are web searches only. No trademark or business-registry lookup was done.

## 1. Ledger

### 1a. Claude Code

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| Claude Code existed and was usable from mid-2025 | Job C, skills (1.5 yrs) | "Limited research preview" announced 2025-02-24 with Claude 3.7 Sonnet. Generally available 2025-05-22 (changelog 1.0.0: "Claude Code is now generally available"). | https://www.anthropic.com/news/claude-3-7-sonnet ; https://www.anthropic.com/news/claude-4 | OK | n/a |
| Claude Code subagents | Job C | Custom subagents shipped in v1.0.60 ("You can now create custom subagents... Run /agents"), dated 2025-07-24 by tracker. | https://raw.githubusercontent.com/anthropics/claude-code/main/CHANGELOG.md ; https://www.havoptic.com/r/claude-code/diff?from=1.0.1&to=latest | OK | Job C started 2025-06, so subagents arrive about 2 months in. Fine. |
| Claude Code hooks, incl. PreToolUse | Job C, Projects | "Released hooks" in v1.0.38, dated 2025-06-30 by tracker. PreToolUse is one of the original events; v2.0.10 (2025-10-07) added "PreToolUse hooks can now modify tool inputs". | same changelog ; https://code.claude.com/docs/en/hooks-guide | OK | n/a |
| Claude Code Agent Skills | Job C, Projects | Agent Skills announced 2025-10-16 (API beta header skills-2025-10-02). Claude Code v2.0.20 "Added support for Claude Skills", 2025-10-16. | https://platform.claude.com/docs/en/release-notes/api ; https://claude.com/blog/skills ; https://www.havoptic.com/releases/claude-code/2025/10 | RISKY | True for Job C only from Oct 2025. Any date on the "n8n Workflow Guard Skill Pack" project must be late 2025 or 2026. Do not imply Skills work before 2025-10-16. |
| Claude Code slash commands (candidate addition) | candidate | Custom slash commands from .claude/commands appear in v0.2.31, during the research preview (before 1.0.0 on 2025-05-22). Exact date of 0.2.31: UNVERIFIED. | same changelog | OK | Safe to add under Job C. |
| Claude Code plugins (candidate addition) | candidate | Plugins public beta 2025-10-09 (v2.0.12 "Plugin System Released"). Bundles slash commands, agents, MCP servers, hooks. | https://claude.com/blog/claude-code-plugins | OK | Safe under Job C from Oct 2025. "Packaged the skills and hooks as a Claude Code plugin" is the natural phrasing for a "Skill Pack". |
| "PreToolUse hooks that inspect exported n8n workflow JSON" | Projects | PreToolUse fires "before a tool call executes. Can block it". Matchers are tool names (Bash, Edit or Write, mcp__.*). It does not fire on a file or a deployment as such; it fires on a tool call Claude Code is about to make. Docs examples: block edits to protected files, block Bash commands matching a pattern. PostToolUse fires after a tool succeeds and cannot undo it; docs use it for format/lint after Edit or Write. | https://code.claude.com/docs/en/hooks-guide | RISKY | Anchor the hook to a tool call: "PreToolUse hooks that block n8n import/deploy commands until a validator script passes on the exported workflow JSON." See section 2. |
| Claude Code used at a HIPAA-covered practice | Job C | Anthropic BAA: Claude Code via a Console API key is covered "only with ZDR enabled"; IDE extensions, cloud sessions, Code Review are not covered. Skills API is "not covered and not accessible" on a HIPAA-ready API org. | https://privacy.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers | RISKY | Say what Claude Code touched: "for workflow QA on exported workflow JSON and synthetic fixtures (no PHI)". The current wording "for workflow QA" is close; add the no-PHI qualifier. |

### 1b. Claude API

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| "Claude tool-use JSON schemas" in Job A (2024-01 to 2024-09) | Job A | Tool use public beta on Claude 3 used header tools-2024-04-04; press coverage 2024-04-05. GA 2024-05-30 ("out of beta across the Claude API, Bedrock, Vertex"). Claude 3 itself launched 2024-03-04. So Jan to Mar 2024 predates both Claude 3 and public tool use. | https://platform.claude.com/docs/en/release-notes/api ; https://www.anthropic.com/news/tool-use-ga ; https://the-decoder.com/anthropic-makes-its-claude-3-family-more-versatile-through-tool-use/ | RISKY | Holds only if the enrichment work sits in Apr to Sep 2024. Do not make it the first bullet of a job that starts 2024-01, or add "(from Q2 2024)" in supporting notes. |
| Forcing JSON via tool-use schemas was a known practice in mid-2024 | Job A, Job B | Anthropic cookbook "Extracting structured JSON using Claude and tool use" published 2024-04-03; tool_choice cookbook 2024-05-15 describes forcing a tool to get well-formed JSON. | https://platform.claude.com/cookbook/tool-use-extracting-structured-json ; https://platform.claude.com/cookbook/tool-use-tool-choice | OK | n/a |
| Models current during Job A | Job A | Claude 3 Opus/Sonnet 2024-03-04; Claude 3.5 Sonnet 2024-06-20. Model before March 2024: UNVERIFIED here (not fetched). | https://www.anthropic.com/news/claude-3-family ; API release notes | OK | If a model is named for Job A, use Claude 3 Haiku/Sonnet or 3.5 Sonnet. |
| Models current during Job B (2024-10 to 2025-05) | Job B | Upgraded Claude 3.5 Sonnet 2024-10-22; Claude 3.5 Haiku 2024-11-04; Claude 3.7 Sonnet 2025-02-24; Claude Opus 4 / Sonnet 4 2025-05-22. | API release notes | OK | n/a |
| "Claude API structured outputs" over inquiries "in the last 12 months" | Job C | Structured outputs launched in public beta 2025-11-14 for Sonnet 4.5 and Opus 4.1 (Haiku 4.5 added 2025-12-04). Out of beta 2026-01-29 for Sonnet 4.5, Opus 4.5, Haiku 4.5. "Last 12 months" from 2026-11-26 starts 2025-11-26, twelve days after the beta opened. On the BAA side, structured outputs is listed as a covered Messages API feature only under BAA versions accepted after 2026-04-01; before that, API BAA coverage ran through zero data retention. | https://platform.claude.com/docs/en/release-notes/api ; https://claude.com/blog/structured-outputs-on-the-claude-developer-platform ; https://privacy.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers ; https://www.aptible.com/hipaa/claude-baa | RISKY | "using Claude tool-use schemas, migrated to structured outputs in 2026". A healthcare practice adopting a two-week-old beta on patient data for the full 12 months is the part a reviewer will doubt. |
| Prompt caching (candidate addition) | candidate | Beta 2024-08-14 (Claude 3.5 Sonnet, Claude 3 Haiku). GA 2024-12-17. Listed as BAA-covered Messages API feature. | API release notes ; https://www.anthropic.com/news/prompt-caching | OK | Natural in Job B (from Dec 2024) and Job C. In Job A it only fits the last six weeks, as a beta; leave it out of Job A. |

### 1c. MCP

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| MCP existed during Job B | Job B | Announced 2024-11-25, with "specification and SDKs", "local MCP server support in the Claude Desktop apps", and a repo of reference servers. Job B started 2024-10, so MCP work can begin Dec 2024 at the earliest. | https://www.anthropic.com/news/model-context-protocol | OK | Keep the MCP bullet out of the first position for Job B; it cannot be the first thing done there. |
| Python MCP server in Job B | Job B | python-sdk v1.0.0 published 2024-11-25 ("first stable release", stdio and SSE transports). | https://api.github.com/repos/modelcontextprotocol/python-sdk/releases/tags/v1.0.0 | OK | n/a |
| TypeScript MCP server in Job C | Job C | typescript-sdk 1.0.0 published 2024-11-25. | https://api.github.com/repos/modelcontextprotocol/typescript-sdk/releases/tags/1.0.0 | OK | n/a |
| "letting 6 account managers pull lead status and source reports in Claude" | Job B | At launch "all Claude.ai plans support connecting MCP servers to the Claude Desktop app", local servers only. The setup path was Settings, Developer, Edit Config, then editing claude_desktop_config.json and restarting. Remote MCP ("Integrations") arrived 2025-05-01 in beta for Max, Team, Enterprise. One-click Desktop Extensions came later (format renamed .dxt to .mcpb on 2025-09-11; original launch date not confirmed here). So between Dec 2024 and May 2025 a non-developer could use a custom server only if someone installed the runtime and edited the JSON config on each machine. | https://www.anthropic.com/news/model-context-protocol ; https://support.claude.com/en/articles/10949351-getting-started-with-local-mcp-servers-on-claude-desktop ; https://claude.com/blog/integrations ; https://www.anthropic.com/engineering/desktop-extensions | RISKY | "Shipped the agency's first Python MCP server over its intake database and set it up in Claude Desktop for 6 account managers, who used it to pull lead status and source reports." Say "Claude Desktop", not "Claude", and own the per-machine setup. |
| TypeScript MCP server "exposing 7 scheduling/eligibility/intake-status tools to Claude" at a healthcare practice | Job C | Anthropic BAA: "External MCP: available to use but sending data to 3rd parties via this feature isn't covered". On Enterprise, MCPs/connectors are "available, but third-party data flows not covered". Free, Pro, Max, Team plans have no BAA. | https://privacy.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers | RISKY | State the consumer and the data: "TypeScript MCP server, hosted inside the practice's environment, exposing 7 scheduling, eligibility and intake-status tools that return record IDs and status codes rather than PHI." |

### 1d. n8n

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| Self-hosted n8n | Job C, skills (2.8 yrs) | Self-hosting is a standard n8n deployment. For PHI it is the expected one: secondary sources say n8n publishes no BAA for n8n Cloud, and self-hosting moves compliance to your own BAA-covered infrastructure. No official n8n statement found. | https://www.accountablehq.com/post/is-n8n-hipaa-compliant-baa-self-hosting-best-practices | OK | n/a (n8n's own position on a Cloud BAA is UNVERIFIED) |
| n8n AI Agent node (candidate addition) | candidate | "LangChain in n8n (beta)" 2023-10-04; LangChain general availability in n8n 1.19.0, 2023-11-29 (docs say use 1.19.4+). From 1.82.0 all AI Agent nodes run as Tools Agent. Whether the node carried the name "AI Agent" at 1.19: UNVERIFIED. | https://docs.n8n.io/advanced-ai/ ; https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.agent/ | OK | Usable in all three jobs. |
| n8n MCP Client Tool / MCP Server Trigger (candidate addition) | candidate | Both nodes shipped in n8n 1.88.0, announced 2025-04-10. SSE only at launch. | https://community.n8n.io/t/we-re-adding-mcp-client-tool-mcp-trigger-nodes-try-them-now/99338 | RISKY | Add only to Job C. In Job B they existed for the final six weeks at most. |
| n8n retry-on-fail, Error Trigger, error workflows (candidate addition) | candidate | Official docs: an "error workflow" is set in Workflow Settings and "must start with the Error Trigger"; "Stop And Error" forces a failure. Node-level "On Error" options are Stop Workflow, Continue, Continue (using error output), confirmed present in n8n 1.35.0 (April 2024). "Retry On Fail" is a per-node setting. First-release versions of each: UNVERIFIED. | https://docs.n8n.io/flow-logic/error-handling/ ; https://github.com/n8n-io/n8n/issues/9236 | OK | Safe in all three jobs. |
| "missing error branches" | Projects | The phrase "error branch" does not appear in n8n's error-handling docs. Community threads do use it informally ("Error branch on Execute SQL node", "errors to success branch instead of error branch"). Official terms are error workflow, Error Trigger, error output, On Error. | https://docs.n8n.io/flow-logic/error-handling/ ; https://community.n8n.io/t/edit-fields-node-outputting-errors-to-success-branch-instead-of-error-branch/122029 | RISKY | "workflows with no error workflow assigned and nodes with unhandled error outputs" |
| "hard-coded credentials" in exported workflow JSON | Projects | n8n docs: "Exported workflow JSON files include credential names and IDs. While IDs aren't sensitive, the names could be." Also: "HTTP Request nodes may contain authentication headers when imported from cURL." So stored credentials are not embedded, but inline secrets are a documented risk. | https://docs.n8n.io/workflows/export-import/ | RISKY | "secrets pasted inline into HTTP Request headers, query strings or Code nodes instead of n8n credentials". "Hard-coded credentials" invites the objection that n8n exports do not contain credentials. |
| "unpinned community nodes" | Projects | n8n docs: community nodes are "unverified code from a public source" with "full access to the machine that n8n runs on"; upgrading can break workflows. Version choice happens at install time (npm install n8n-nodes-x@2.1.0), not in the workflow file. Two unverified community nodes were hit in the Shai-Hulud npm attack. Verified community nodes launched with n8n 1.94.0 (May 2025). That a workflow export carries no package version is my reading of the format: UNVERIFIED by a fetched source. | https://docs.n8n.io/integrations/community-nodes/risks/ ; https://docs.n8n.io/integrations/community-nodes/installation/manual-install/ ; https://blog.n8n.io/community-nodes-available-on-n8n-cloud/ | FIX | "community nodes that are unverified or missing from the team's pinned-version allowlist". A check that reads only workflow JSON can see which community node types are used; it cannot see whether the installed package is pinned. |

### 1e. Certificate

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| "Claude Code in Action" exists | Cert | Course is live on Skilljar (pages titled "Anthropic Academy Courses"), on Coursera (about 3 hours, shareable certificate) and mirrored on DataCamp. | https://anthropic.skilljar.com/claude-code-in-action ; https://www.coursera.org/learn/claude-code-in-action | OK | n/a |
| Course existed in 2025, issuer "Anthropic Academy" | Cert | A university IT post dated 2025-07-11 lists "Claude Code in Action" among courses "hosted on Anthropic Academy's Build with Claude track", each "culminating in a certificate of completion". Earliest certificate verification page seen in search results: completed 2025-10-08, issuer shown as "Anthropic Education". Several 2026 blogs say Anthropic Academy "launched" 2026-03-02; that reads as a relaunch or expansion, since the name is attested in July 2025. As of today anthropic.com/learn redirects to academy.claude.com, branded "Claude Academy". Exact course launch date: UNVERIFIED (on or before 2025-07-11). | https://rits.shanghai.nyu.edu/ai/announcing-claude-developer-training-courses-with-certificates/ ; https://academy.claude.com/ ; https://verify.skilljar.com/c/3tksvw6w582c | RISKY | "Claude Code in Action, certificate of completion, Anthropic Academy (2025)". It is a course-completion certificate, not a certification, so label it that way or list it under Training. The persona's completion date should be July 2025 or later. |

### 1f. Healthcare compliance (Job C)

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| Claude API can be used with PHI | Job C | Anthropic "provides a BAA covering our HIPAA-ready services, such as use of our first-party API... or Enterprise plans". For the API the org's Primary Owner signs the BAA and asks Anthropic to enable it. BAAs signed before 2025-12-02 covered API use only, via zero data retention. From 2026-04-01 a non-ZDR HIPAA-ready API org exists with a fixed list of covered Messages API features: prompt caching, structured outputs, memory, web search, bash tool, text editor tool. Not covered and not accessible: Batch API, Files API, Skills API, code execution, web fetch. When Anthropic first offered an API BAA: UNVERIFIED. Whether plain client-side tool use and PDF input are covered: UNVERIFIED (not in the list as returned). | https://privacy.claude.com/en/articles/8114513-business-associate-agreements-baa-for-commercial-customers ; https://www.aptible.com/hipaa/claude-baa | RISKY | The resume never mentions a BAA. Add it: "under the practice's Anthropic BAA". Avoid claiming Batch API or Files API on this job. |
| "PHI redaction ... before every Claude API call" alongside extracting insurance, referral and symptom fields | Job C | HHS Safe Harbor de-identification means removing 18 identifier types (names, dates, phone, address, health plan beneficiary numbers and so on). Symptoms are not on the list, but an insurance member ID is. If the model must read symptoms and insurance details tied to one person, the payload is still PHI and the call still needs a BAA. "Redaction before every call" overstates what happened. | https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html | FIX | "Masked direct identifiers (name, date of birth, phone, address, member ID) with tokens before each Claude API call and re-linked results by record ID" plus "under a BAA". |
| "HIPAA-aligned audit logging" | Job C | HHS "does not certify, endorse, or accredit any... product, or program as HIPAA compliant". "HIPAA-aligned" has no regulatory definition; it is vendor phrasing. The actual requirement is audit controls, 45 CFR 164.312(b): record and examine activity in systems holding ePHI. | https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html | RISKY | "audit logging of every model call (user, record ID, timestamp, prompt version; no payloads) to meet the Security Rule's audit-control requirement" |
| "quarterly compliance reviews" at a small outpatient practice | Job C | The Security Rule requires "periodic" evaluation (164.308(a)(8)) and periodic risk analysis; no cadence is set. Nothing found that says small practices typically run quarterly reviews. | https://www.hhs.gov/hipaa/for-professionals/compliance-enforcement/audit/protocol/index.html | RISKY | "Supplied access-log exports and data-flow diagrams for the practice's annual security risk analysis and quarterly access reviews." Typical small-practice cadence: UNVERIFIED. |
| GoHighLevel pipelines holding patient inquiries | Job C | HighLevel sells a HIPAA add-on at US$297 per month with a signed BAA, available on any agency plan; cannot be disabled once bought. Launch date of the add-on: UNVERIFIED. | https://help.gohighlevel.com/support/solutions/articles/48000983084-hipaa-compliance-with-highlevel | RISKY | "GoHighLevel (HIPAA-enabled account)". Without that the practice is putting PHI in a CRM with no BAA. |
| Google Chat alerts | Job C | Google Chat is in Google Workspace's HIPAA Included Functionality under a signed BAA. Third-party apps and add-ons are excluded. | https://support.google.com/a/answer/3407054 ; https://workspace.google.com/terms/2015/1/hipaa_functionality.html | RISKY | "PHI-free Google Chat alerts (record ID and deep link only)" |
| Fax inquiries reaching n8n | Job C | Cloud fax vendors (eFax, Documo, WestFax) deliver inbound faxes as PDF by email, API or webhook, some with OCR. Plain email delivery of PHI is flagged as weaker than API delivery. Files API is not BAA-covered; PDF input coverage is UNVERIFIED. No n8n fax-intake template found. | https://www.documo.com/intelligent-document-processing/ ; https://www.efax.com/ | RISKY | "web forms and cloud-fax PDFs (webhook delivery, OCR to text) into a self-hosted n8n pipeline". Name the OCR step; do not imply raw fax images go to Claude. |

### 1g. Legal intake (Job B)

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| Flags statute-of-limitations dates | Job B | Texas: two years for personal injury and wrongful death, Tex. Civ. Prac. & Rem. Code 16.003; tolling for minors and unsound mind under 16.001. Intake guides list "statute of limitations runway" as a standard screening factor. A marketing agency can flag the incident date; deciding the deadline is legal judgment. Shorter government-claim notice periods: UNVERIFIED (not searched). | https://statutes.capitol.texas.gov/docs/cp/htm/cp.16.htm | RISKY | "flags incident dates within 90 days of the Texas two-year limitations period for attorney review" |
| Flags "existing-client name matches for conflict review" | Job B | ABA Formal Opinion 506 (2023-06-07): a lawyer may train and supervise a nonlawyer to do intake "including... performing an initial conflict check". The conflict decision stays with the firm's lawyers. Texas does not accept screening to cure a firm conflict (Ethics Op. 569). Nothing found on marketing agencies holding firm client lists. | https://www.americanbar.org/news/abanews/aba-news-archives/2023/06/guidance-legal-assistants/ ; https://legalethicstexas.com/resources/opinions/opinion-569/ | RISKY | "flags possible name matches against each firm's own CRM contacts (prospect and adverse party) so the firm can run its conflict check". Make clear matching is per firm, never across the 9 clients. |
| "Practice area" classification | Job B | No source found on how PI-only agencies label leads. All 9 clients are PI firms, so "practice area" is a single value. Intake guides screen by case facts (liability, injury severity, coverage). | https://www.evenuplaw.com/guides/understanding-personal-injury-intake-process/ | FIX | "case type (motor vehicle, trucking, premises, workplace, medical malpractice)" |
| Lead volumes | Job B | No reliable per-firm monthly lead benchmark found. Only conversion data: 17.6% lead-to-client across 58,395 leads (MyCase 2024); PI intake-to-retention quoted at 15 to 30% by vendors. | https://mycase.com/wp-content/uploads/2024/09/MyCase-BenchmarkReport-Part2-2024.pdf | UNVERIFIED | Any per-firm lead count on the resume is unsourced. Keep totals modest and internally consistent with 9 firms. |

### 1h. Shopify (Job A)

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| "n8n workflows on Shopify Admin API webhooks to triage support tickets" | Job A | Shopify webhooks emit commerce events: orders/create, orders/updated, orders/fulfilled, refunds/create, returns/request ("return is requested"), returns/approve. Shopify has no ticket object. Tickets are Gorgias objects; Gorgias HTTP integrations fire on ticket-created and ticket-message-created and POST a templated body to a URL. n8n has no first-party Gorgias node, so the n8n side is a Webhook node plus HTTP Request calls to the Gorgias REST API. | https://shopify.dev/docs/apps/build/orders-fulfillment/returns-apps ; https://hookdeck.com/webhooks/platforms/guide-to-gorgias-webhooks-features-and-best-practices ; https://www.ringly.io/blog/n8n-gorgias-integration | FIX | "Built n8n workflows triggered by Gorgias ticket-created webhooks that pull order, fulfillment and return status from the Shopify Admin API and tag tickets by return eligibility and refund risk." |
| REST vs GraphQL in 2024 | Job A | Shopify marked the REST Admin API legacy on 2024-10-01; new public apps must use GraphQL from 2025-04-01. Job A ended 2024-09, so REST was still the normal path. | https://www.shopify.com/partners/blog/all-in-on-graphql | OK | Plain "Shopify Admin API" is right for 2024. |
| Returns webhooks existed in 2024 | Job A | Return-request handling is tagged to API version 2023-01 in Shopify's changelog. The version that first shipped the returns/* webhook topics: UNVERIFIED. | https://shopify.dev/changelog/return-request-actions-available-to-merchants-in-the-admin | OK | n/a |
| Gorgias as the helpdesk | Job A | Gorgias positions itself as the ecommerce helpdesk for Shopify, BigCommerce and Magento. "Most popular" is unproven; "natural fit" is fair. | https://hookdeck.com/webhooks/platforms/guide-to-gorgias-webhooks-features-and-best-practices | OK | n/a |

### 1i. Company names

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| "Tidewell Supply Co." | Job A | No business with this exact name found. "Tidewell" is the name of Tidewell Hospice, a real not-for-profit hospice in Sarasota, Florida (part of Empath Health). Different industry and country from the fictional employer. | https://www.floridahospices.org/company/tidewell-hospice/ | RISKY | Low risk, but the coined word belongs to a real Florida healthcare brand and Job C is a Florida healthcare employer. Alternatives with no hits in searches: Saltgum Supply Co., Quollridge Outfitters, Banksia Bluff Gear Co. |
| "Casefront Legal Marketing" | Job B | No company or product named Casefront found. Nearest names: CaseFox (legal billing software), DocketLaunch (intake implementer). | (searches returned no match) | OK | Spare names with no hits in searches: Docketlight Legal Marketing, Gavelbrook Legal Marketing, Caseharbor Legal Marketing. Note real firms named Gavel (document automation) and Harbor (legal consulting) exist. |
| "Those Who Care Co" | Job C | Near match: For Those Who Care, Inc., a real home health agency in Winter Haven / Clermont, Florida, NPI 1457779696. Same state, same sector. | https://npifinder.com/1457779696/for-those-who-care-inc | RISKY | Rename, or move the fictional practice out of Florida. No alternatives were checked for this one. |

### 1j. Skill-year sanity (as of 2026-11-26)

| Claim | Where on resume | What the source says (with date) | Source URL | Verdict | Suggested rewording if not OK |
|---|---|---|---|---|---|
| Claude Code 1.5 yrs | Skills | Research preview 2025-02-24, so 1.75 years is the ceiling. Job C from 2025-06 gives 1.4 to 1.5. | https://www.anthropic.com/news/claude-3-7-sonnet | OK | Passes. Fails if Job C started later than about 2025-06-01. |
| Claude API tool use / structured outputs 2.5 yrs | Skills | Tool use public beta 2024-04-04, ceiling 2.6 years. 2.5 implies starting by late May 2024, inside Job A. Structured outputs as a named feature began 2025-11-14, ceiling 1.0 year. | API release notes | RISKY | Split the line: "Claude API tool use (2.5 yrs), structured outputs (1 yr)". As a combined label it claims 2.5 years of a feature that is one year old. |
| MCP servers 1.8 yrs | Skills | MCP announced 2024-11-25, ceiling 2.0 years. 1.8 implies starting about Feb 2025, inside Job B. | https://www.anthropic.com/news/model-context-protocol | OK | Passes with three months of margin. |
| n8n self-hosted 2.8 yrs | Skills | Jobs A to C run 2024-01 to 2026-11, about 2.9 years. Only Job C says "self-hosted". | n/a | RISKY | Passes on time. Say "self-hosted" somewhere in Job A or B, or drop "self-hosted" from the skill label. |
| TypeScript 1.5 yrs | Skills | Only Job C (2025-06 onward, 1.4 to 1.5 years) shows TypeScript. | n/a | OK | Borderline. 1.4 would be safer. |
| GitHub Actions 1.0 yr | Skills | Supported by the eval-kit project; no tool-age limit. | n/a | OK | n/a |

## 2. Phrasing a practitioner would actually use

**Job A, Tidewell Supply Co. (2024-01 to 2024-09)**
- Instead of "n8n workflows on Shopify Admin API webhooks to triage support tickets": "Built n8n workflows triggered by Gorgias ticket-created webhooks that look up order, fulfillment and return status through the Shopify Admin API and tag each ticket by return eligibility and refund risk."
- Keep "Enriched 1,150 product listings using Claude tool-use JSON schemas", and treat it as Q2 to Q3 2024 work. An even plainer version: "Enriched 1,150 product listings with Claude, forcing a tool call so every record matched one JSON schema."
- For return and refund routing: "Routed return and refund requests from Shopify returns/request and refunds/create webhooks into Gorgias and a Google Sheets log."

**Job B, Casefront Legal Marketing (2024-10 to 2025-05)**
- "Built case-intake triage in n8n with Claude tool use for 9 personal-injury firms, classifying each lead by case type (motor vehicle, trucking, premises, workplace) as structured JSON before CRM sync."
- "Flagged incident dates close to the Texas two-year limitations period, and possible name matches in each firm's CRM, for attorney and conflict review."
- "Shipped the agency's first Python MCP server over its intake database and set it up in Claude Desktop for 6 account managers, who use it to pull lead status and source reports." Date this to 2025.
- "Routed AI-drafted follow-ups through a Slack approval queue before sending" is fine as written.

**Job C, Those Who Care Co (2025-06 to present)**
- "Run a self-hosted n8n patient-intake pipeline, under BAAs with Anthropic, HighLevel and Google Workspace, that extracts insurance, referral and symptom fields from 1,900 web and cloud-fax inquiries a year using Claude tool-use schemas (structured outputs since 2026)."
- "Mask direct identifiers (name, date of birth, phone, address, member ID) before each Claude API call and re-link results by record ID; log every call (user, record, time, prompt version) for Security Rule audit controls."
- "Route triaged inquiries into HIPAA-enabled GoHighLevel pipelines and send PHI-free Google Chat alerts."
- "Built a TypeScript MCP server inside the practice's environment exposing 7 scheduling, eligibility and intake-status tools that return IDs and status codes rather than PHI."
- "Supplied access-log exports and data-flow diagrams for the practice's annual security risk analysis and quarterly access reviews."
- "Standardized Claude Code subagents, hooks and Agent Skills for workflow QA on exported workflow JSON and synthetic fixtures, with no PHI in the loop."

**Project, n8n Workflow Guard Skill Pack (date it late 2025 or 2026)**
- "Claude Code plugin bundling Agent Skills and a PreToolUse hook: the hook blocks n8n import and deploy commands until a validator script passes on the exported workflow JSON. The validator rejects workflows with no error workflow assigned, nodes with unhandled error outputs, secrets pasted inline into HTTP Request or Code nodes, and community nodes missing from a pinned-version allowlist."
- Why this wording: PreToolUse intercepts a tool call (a Bash command, a file write, an MCP tool), so name the call it guards. If the check should run after Claude edits a workflow file, the event is PostToolUse on Edit or Write. The same validator belongs in a pre-commit hook or the CI job, which is where a team would enforce it for people not using Claude Code.

**Project, Intake Reply Eval Kit**
- No factual problem found. "pytest suite that replays synthetic intake scenarios against Claude prompts and fails the GitHub Actions check on regressions" is the usual phrasing; a required status check is what blocks the merge.

**Certificate**
- "Claude Code in Action, certificate of completion, Anthropic Academy (2025)".

**Skills line**
- "Claude API tool use (2.5 yrs), structured outputs (1 yr), prompt caching", "MCP servers, Python and TypeScript (1.8 yrs)", "n8n, self-hosted (2.8 yrs)".

## 3. UNVERIFIED items

1. Exact release date of Claude Code v0.2.31 (custom slash commands). Known only to predate GA on 2025-05-22.
2. Exact launch date of the "Claude Code in Action" course. Attested by 2025-07-11. The "Anthropic Academy launched 2026-03-02" claim in 2026 blogs conflicts with the July 2025 attestation and was not resolved against an Anthropic primary source.
3. Skilljar certificate issuer string ("Anthropic Education") is from search-result snippets; the verification page itself returned 403.
4. When Anthropic first offered a BAA for the API. Confirmed only that pre-2025-12-02 API BAAs were ZDR-based.
5. Whether plain client-side tool use and PDF input are BAA-covered Messages API features. Neither was in the covered list as returned.
6. Launch date of GoHighLevel's HIPAA add-on, and whether US$297 is per agency or per sub-account (sources conflict).
7. n8n's own position on a BAA for n8n Cloud (secondary sources only).
8. First-release versions of n8n Retry On Fail, Error Trigger and the On Error error output. All present by April 2024.
9. Whether the node was named "AI Agent" at n8n 1.19 (Nov 2023).
10. That exported n8n workflow JSON carries no community-package version. Format knowledge, not a fetched source.
11. Typical monthly web-lead volume for a personal-injury firm.
12. Typical compliance-review cadence at small outpatient practices.
13. Texas government-claim notice periods shorter than two years (not searched).
14. The Claude model current before 2024-03-04 and the Claude 3 Haiku release date (not fetched).
15. API version that first shipped Shopify returns/* webhook topics.
16. Original launch date of Claude Desktop Extensions.
17. Company-name checks are web-search only; no trademark, ASIC, or state business-registry lookups. Alternatives for "Those Who Care Co" were not generated or checked.

## 4. Resolution: what the final resume says (2026-11-26)

The verdicts in section 1 were written against the draft before the rewrite. Every FIX and RISKY row was then resolved as follows; the final text passed three review rounds.

| Ledger item | Final resume wording / decision |
|---|---|
| Tickets are Gorgias objects, not Shopify webhooks | Saltgum bullet 1: n8n workflows "triggered by Gorgias HTTP integrations ... using Shopify GraphQL Admin API return status". |
| "PHI redaction before every call" incoherent with extraction | Masking of direct identifiers happens "in form and OCR text before each Claude API call under a BAA"; Claude extracts only payer, referral, and visit reason; member ID is parsed by rule. Skill renamed "PHI Masking / HIPAA Audit Controls". |
| "Practice area" at an all-PI agency | Now "case type (motor vehicle, trucking, premises)". |
| "Unpinned community nodes" | Now "unlisted community nodes" (checked against an allowlist). |
| Structured outputs with patient data too early / BAA coverage | Removed from the healthcare pipeline. Structured outputs appear only in the Intake Reply Eval Kit, which uses synthetic scenarios. Listed as its own skill (0.8 yrs). |
| Tool use / structured outputs years bundled | Split: "Claude API (Tool Use, Prompt Engineering)" 2.5 yrs; "Structured Outputs" 0.8 yrs. |
| Job A tool use only valid Apr–Sep 2024 | Kept; the enrichment build is dated 2024-06 to 08 in the numbers ledger. |
| Job B MCP "in Claude" | Now "onboarded account managers in Claude Desktop"; server is "read-only". |
| Job C MCP server and third-party data flows | Now "in-house" server whose tools "give the routing agent only record IDs and status codes". |
| PreToolUse wording | Project: "A PreToolUse Bash hook that denies n8n import:workflow and API pushes until a validator clears the exported JSON ...". |
| Agent Skills shipped 2025-10-16 | Used only in the current role and the project; both dated after release. |
| Claude Code at the practice | Bullet says "PHI-free n8n QA in Claude Code". |
| "Error branches" | Now "retries and error workflows"; skill "n8n (Self-Hosted, Error Handling)". |
| "Hard-coded credentials" | Now "inline secrets". |
| "HIPAA-aligned audit logging" | Now "logging every request for HIPAA audit controls". |
| "Quarterly compliance reviews" | Claim removed. |
| GoHighLevel / Google Chat / fax | "HIPAA-enabled GoHighLevel pipelines", "Google Chat alerts without PHI", "OCR'd faxes". |
| SOL and conflicts | "adverse-party names for each firm's conflict check and incident dates nearing Texas's two-year statute of limitations". |
| Certificate naming | "Claude Code in Action (Certificate of Completion)", Anthropic Academy, 2025. |
| n8n self-hosted 2.8 yrs but only Job C said so | Saltgum bullet 1 now says "self-hosted n8n workflows on Docker". |
| Florida rule on where patient data is stored (raised in review) | Bullet 1 now says the pipeline runs "on US-region AWS". |
| "Tidewell" name clash (real Florida hospice) | Renamed to "Saltgum Supply" (search-clean). |
| "Those Who Care Co" resembles a real Florida home health agency | Kept by the owner's decision (2026-11-26): it is an established persona fact. Closed. |

Still UNVERIFIED (unchanged from section 3, none contradicted by a source): exact course launch date; the date Anthropic first offered an API BAA and whether client tool use is on its covered-feature list; GoHighLevel HIPAA add-on launch date; typical PI lead volumes; name checks were web search only.
