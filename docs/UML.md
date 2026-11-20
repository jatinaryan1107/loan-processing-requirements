# Loan Processing Requirement System UML

These diagrams describe the prototype's four user-facing capabilities. The class view is a logical design: service boxes group Python functions and FastAPI routes; they are not claims that every box is a Python class. There is no operational loan application, credit decision or payment entity.

## Use cases

Mermaid flowchart notation expresses the actor/use-case relationships. Permission enforcement occurs in the API, not just in the interface.

```mermaid
flowchart LR
    BA[Business Analyst]
    CO[Compliance Officer]
    PM[Project Manager]
    DEV[Software Developer]
    subgraph System[Loan Processing Requirement System]
        G([Requirement Gathering])
        A([Requirement Analysis and Validation])
        C([Compliance Verification])
        S([SDLC Model Recommendation])
        X([Read or export approved artefacts])
    end
    BA -->|create project, capture source, answer questions| G
    BA -->|analyse, edit, approve or reject requirements| A
    BA -->|request checks| C
    CO -->|inspect evidence, amend and review mappings| C
    PM -->|inspect analysed requirements| A
    PM -->|set factors, rank and decide| S
    PM -->|final export after gates pass| X
    DEV -->|read approved requirements| A
    DEV -->|read lifecycle workflow| S
    DEV -->|approved view| X
```

## Logical component and entity diagram

The top-level system associates with four capability services, as requested by the coursework. The services collaborate; they do not inherit from the system. Projects own requirements and their provenance rather than customer lending records.

```mermaid
classDiagram
    class LoanProcessingRequirementSystem {
        +authenticateDemoRole()
        +authoriseAction()
        +loadProject()
    }
    class RequirementGathering {
        +createProject()
        +addSource()
        +parseUpload()
        +answerQuestion()
    }
    class RequirementAnalysisAndValidation {
        +extractDraftRequirements()
        +classifyRequirements()
        +checkQuality()
        +editRequirement()
        +reviewRequirement()
    }
    class ComplianceVerification {
        +retrieveLocalClauses()
        +proposeMappings()
        +reviewMapping()
    }
    class SDLCModelRecommendation {
        +rankModels()
        +generateWorkflow()
        +recordDecision()
    }
    class Project {
        id
        name
        jurisdiction
        synthetic
    }
    class Source {
        id
        source_name
        stakeholder
        text
        created_at
    }
    class Requirement {
        id
        source_id
        original_text
        statement
        kind
        categories
        acceptance_criteria
        status
        history
    }
    class ClarificationQuestion {
        id
        requirement_ids
        text
        status
        answer
    }
    class ComplianceMapping {
        id
        requirement_ids
        control
        status
        interpretation
        history
    }
    class EvidenceClause {
        id
        title
        clause
        text
        jurisdiction
        version
        effective_date
        applicability
        synthetic
    }
    class LifecycleDecision {
        factors
        rankings
        selected_model
        status
        workflow
        history
    }
    class AgentRun {
        id
        agent
        version
        provider
        input_ids
        outcome
        confidence
        evidence
        at
    }
    class AuditEntry {
        id
        actor
        role
        action
        details
        at
    }
    LoanProcessingRequirementSystem --> RequirementGathering
    LoanProcessingRequirementSystem --> RequirementAnalysisAndValidation
    LoanProcessingRequirementSystem --> ComplianceVerification
    LoanProcessingRequirementSystem --> SDLCModelRecommendation
    RequirementGathering --> Project
    RequirementAnalysisAndValidation --> Requirement
    ComplianceVerification --> ComplianceMapping
    SDLCModelRecommendation --> LifecycleDecision
    Project "1" *-- "0..*" Source
    Project "1" *-- "0..*" Requirement
    Source "1" <-- "0..*" Requirement : provenance
    Project "1" *-- "0..*" ClarificationQuestion
    Requirement "0..*" -- "0..*" ClarificationQuestion
    Project "1" *-- "0..*" ComplianceMapping
    Requirement "0..*" -- "0..*" ComplianceMapping : interpreted coverage
    ComplianceMapping "0..*" --> "0..1" EvidenceClause : cited snapshot
    Project "1" *-- "0..1" LifecycleDecision
    Project "1" *-- "0..*" AgentRun
    Project "1" *-- "0..*" AuditEntry
```

## Business Analyst and Requirement Gathering sequence

The implementation separates source capture from explicit analysis. Upload parsing or adding text alone does not silently call an external model. Answering a clarification question adds a linked source. Short answers remain interview context; complete statements can be analysed explicitly by the analyst.

```mermaid
sequenceDiagram
    actor BA as Business Analyst
    participant UI as React interface
    participant API as FastAPI routes
    participant Store as SQLite storage
    participant Rules as Extraction and quality rules
    participant LLM as Optional model boundary

    BA->>UI: Choose Business Analyst demo identity
    UI->>API: POST /api/session {role: ba}
    API->>Store: Store session token hash, role and expiry
    API-->>UI: Bearer token and demo user
    BA->>UI: Create project
    UI->>API: POST /api/projects
    API->>API: Validate session, BA permission and fields
    API->>Store: Persist project and audit entry
    API-->>UI: Project aggregate
    BA->>UI: Enter statement and source details
    UI->>API: POST /api/projects/{id}/sources
    API->>API: Validate and normalise input
    API->>Store: Save original source, ID, timestamp and audit entry
    API-->>UI: Updated project and captured source
    BA->>UI: Run analysis
    UI->>API: POST /api/projects/{id}/analyse
    API->>Store: Load unextracted sources and existing requirements
    alt Explicit LLM request and enabled provider
        API->>LLM: Send masked source as untrusted data
        LLM-->>API: Structured extraction response
        API->>API: Validate response schema and source linkage
    else Deterministic mode
        API->>Rules: Extract statements and classify draft requirements
        Rules-->>API: Drafts with source references and suggested criteria
    end
    API->>Rules: Check ambiguity, omissions, duplication and conflicts
    Rules-->>API: Flags and clarification questions
    API->>Store: Save requirements, questions, agent runs and audit
    API-->>UI: Updated project aggregate
    UI-->>BA: Draft requirements, evidence and questions
    BA->>UI: Answer a clarification question
    UI->>API: POST /api/projects/{id}/questions/{qid}/answer
    API->>Store: Save answer as source and mark question answered
    API-->>UI: Updated project
    BA->>UI: Analyse complete answer statements and review drafts
```

Review and export are subsequent workflows. Requirement edits invalidate their previous approval; compliance decisions require the Compliance Officer role; lifecycle decisions require the Project Manager role. Final exports are checked server-side.

## Implementation boundaries

`app.py` assembles the application. `routes.py` exposes the calls shown above; `schemas.py` validates their bodies and `auth.py` enforces permissions. `services.py` loads a project snapshot, checks the client revision, applies the operation outside the writer lock and commits only if the stored revision is unchanged. `ingestion.py` parses documents in FastAPI worker threads. The frontend uses separate screen components and a shared `useWorkspace` hook, which handles expiry, server logout and stale revisions.
