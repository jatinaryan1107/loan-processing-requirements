# Coursework decisions and context

## Original source and project framing
The attached `Problem Statement.docx` is the exact original project brief the student uploaded. Both copies previously uploaded were byte-for-byte identical. Its subject is a financial-sector Agentic AI / LLM-assisted requirements-engineering and SDLC-selection system. Section 18 encourages starting with one representative financial use case, such as loan processing, and expanding later.

We selected **loan processing as the REQUIREMENTS DOMAIN**. The software we are implementing assists teams designing a loan-processing application; it does not originate, approve or disburse loans.

## Project names
- Full title: Agentic AI-Based Automated Requirement Gathering and SDLC Recommendation System for Financial Institutions (Loan Processing Domain)
- Compressed title: AI-Based Loan Processing Requirements Management
- Name used in UML: Loan Processing Requirement System

## Agreed four functionalities
1. **Requirement Gathering:** obtain software requirements from stakeholders via questionnaires, conversations and documents.
2. **Requirement Analysis and Validation:** structure and classify requirements; identify ambiguities, missing details, duplications and conflicts; obtain human validation.
3. **Compliance Verification:** identify source-backed regulatory/security/policy constraints and gaps; seek authorised human review.
4. **SDLC Model Recommendation:** analyse risk, project complexity and change frequency, recommend and justify a lifecycle model with human approval.

## Four actors shown in UML
- Business Analyst
- Compliance Officer
- Project Manager
- Software Developer

## UML outputs discussed in class
- **Use case diagram:** the four actors connect to appropriate combinations of four functionality use cases inside the system boundary.
- **Class diagram:** teacher instructed placing a top-level `Loan Processing Requirement System` class above four subcomponents corresponding to the four functionalities; example course diagram showed associations and multiplicities. This is a **coursework representation**; implementation design should use technically appropriate service and entity models rather than force inheritance.
- **Sequence diagram:** one actor and one functionality. Selected **Business Analyst** interacting with **Requirement Gathering**. Earlier illustrated diagram showed entering details, passing request to controller, storing in database and showing confirmation. A real MVP should also include the extraction/clarification agent if implemented.

## Notes about historical diagrams
The reference images are illustrative, AI-generated diagrams and might contain imperfect multiplicities, naming or semantics. Do not reproduce flaws blindly. In particular, a previous class diagram incorrectly centred a `LoanApplication` data entity as if this were operational lending software. That is outside the intended scope. Preserve the lecturer's broad diagram format while keeping the real architecture aligned to the original document.

## Still not formally finalised
No framework, database, AI API, hosting provider, university submission deadline, required architecture complexity or approved regulation dataset has yet been specified by the student. Pick a practical local MVP stack and disclose assumptions. Do not claim legal compliance from unsupported sources.
