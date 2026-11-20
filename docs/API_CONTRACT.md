# API contract

All paths start `/api`. JSON bodies/responses, except multipart upload and Markdown export. Business errors use `{detail:string}`; field validation errors use FastAPI's `{detail:[...]}` array. Auth: `Authorization: Bearer <token>`. Every mutation below returns the complete updated project unless specified. All GETs need auth except health.

The UI sends `If-Match: <project.updated_at>` on project writes and exports. A stale value returns 409 without applying the operation. Scripts may omit this header; commit-time revision comparison still protects changes that overlap in flight. `DELETE /session` revokes the current token and returns `{ok:true}`. BA users can `POST /projects/{id}/sources/{sid}/exclude` with `{note}` to exclude a pending source while preserving its evidence. Already-extracted sources must be handled through requirement review instead.

- `GET /health`: mode, llm_available, version.
- `POST /session` body `{role:"ba"|"compliance"|"pm"|"developer"}` → `{token,user:{id,name,role},mode}`. Explicit local demo identity, no password.
- `GET /projects` → array `{id,name,description,jurisdiction,synthetic,created_at,requirement_count,approved_count}`.
- `POST /projects` body `{name,description?,jurisdiction?}` (BA) → full project.
- `GET /projects/{id}` → full project aggregate below.
- `PUT /projects/{id}/context` replaces the name, description and jurisdiction (BA). A description or jurisdiction change clears compliance mappings and reopens the lifecycle decision. Renaming alone preserves reviews.
- `POST /projects/{id}/sources` body `{text,source_name,stakeholder?}` (BA).
- `POST /projects/{id}/upload` multipart `file` (BA), TXT/DOCX/PDF, 5 MB.
- `POST /projects/{id}/analyse` body `{use_llm?:boolean}` (BA). Extracts new sources, reruns checks.
- `PATCH /projects/{id}/requirements/{rid}` body `{statement?,priority?,acceptance_criteria?:string[],justification?}` (BA), resets approval.
- `POST /projects/{id}/requirements/{rid}/review` body `{decision:"approved"|"rejected",note}` (BA).
- `POST /projects/{id}/questions/{qid}/answer` body `{answer}` (BA); answer retained as linked source, question resolved; rerun analysis explicitly.
- `POST /projects/{id}/compliance` empty body (BA/CO).
- `POST /projects/{id}/mappings/{mid}/review` body `{decision:"approved"|"rejected",note,interpretation?:string}` (CO). Unknown sources cannot be approved as verified mappings.
- `POST /projects/{id}/sdlc` body `{factors:{stability,complexity,regulatory,security,stakeholders,change,legacy,testing,cadence}}` (PM), all integers 1–5.
- `POST /projects/{id}/sdlc/decision` body `{model,decision:"approved"|"rejected",note}` (PM).
- `GET /projects/{id}/export?format=markdown|json&final=false|true` → Markdown text or JSON object; BA/CO/PM draft, PM final only, developer approved-only draft. Final requires reviewed requirements, completed compliance disposition and approved lifecycle.

Full project:
```
{id,name,description,jurisdiction,synthetic,created_at,updated_at,
 sources:[{id,source_name,stakeholder,text,created_at,extracted,synthetic}],
 requirements:[{id,source_id,original_text,statement,kind,categories:string[],priority,acceptance_criteria:string[],justification,dependencies:string[],assumptions:string[],risk,confidence,status,history:[],created_at,updated_at}],
 flags:[{id,requirement_ids:string[],type,severity,message,question}],
 questions:[{id,requirement_ids:string[],text,status,answer?,source_id?}],
 mappings:[{id,requirement_ids:string[],control,status,reason,interpretation,source:null|{id,title,clause,text,jurisdiction,version,effective_date,applicability,synthetic},history:[]}],
 sdlc:null|{factors,rankings:[{model,score,max_score,rationale:string[]}],uncertainty,selected_model,status,workflow:[{phase,activities:string[],roles:string[],deliverables:string[],security_checkpoint,approval_gate,entry,exit}],history:[]},
 audit:[{id,at,actor,role,action,details}],
 runs:[{id,at,agent,version,provider,input_ids:string[],outcome,confidence,evidence:string[]}],
 mode:"deterministic demo", final_ready:boolean,final_blockers:string[]}
```

States: requirement `draft/approved/rejected`; question `open/answered`; mapping `proposed/unsupported/approved/rejected`; SDLC `draft/approved/rejected`. A source-backed mapping proposes coverage only; it does not establish legal compliance. Score is a weighted rules score, never probability. Synthetic policy is explicitly labelled.
