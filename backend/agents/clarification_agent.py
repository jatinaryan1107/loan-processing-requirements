"""Build follow-up questions and retain interview history across revisions."""

from ..storage import digest, run, uid


def prepare(project, requirements, flags):
    def question_key(question):
        return question["text"], tuple(sorted(question["requirement_ids"]))

    old = {question_key(q): q for q in project["questions"]}
    questions = []
    for f in flags:
        candidate = dict(id=uid("Q"), requirement_ids=f["requirement_ids"], text=f["question"], status="open")
        relevant = [r for r in requirements if not f["requirement_ids"] or r["id"] in f["requirement_ids"]]
        context = digest(
            [
                {key: r[key] for key in ("id", "statement", "categories", "acceptance_criteria")}
                for r in relevant
            ]
        )
        previous = old.get(question_key(candidate))
        if previous and (previous.get("context_sha256") == context or previous["status"] == "open"):
            candidate = previous
        elif previous and previous["status"] == "answered":
            # Keep the historical answer separately; it cannot resolve changed evidence.
            candidate["supersedes_question_id"] = previous["id"]
        candidate["context_sha256"] = context
        questions.append(candidate)
    # Keep prior answers as the permanent interview record even after a flag disappears.
    questions += [
        q
        for q in project["questions"]
        if (q["status"] == "answered" or q.get("origin") == "llm")
        and q["id"] not in {x["id"] for x in questions}
    ]
    project["questions"] = questions
    run(
        project,
        "ClarificationAgent",
        [f["id"] for f in flags],
        f"Prepared {sum(q['status'] == 'open' for q in questions)} context-linked follow-up questions.",
        0.65,
    )
