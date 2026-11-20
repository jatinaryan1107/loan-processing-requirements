"""Synthetic, reviewable startup example."""

from . import rules, storage
from .services import add_source

SYSTEM = {"name": "Synthetic demo seed", "role": "system"}


def seed_demo(conn):
    if conn.execute("SELECT COUNT(*) FROM projects").fetchone()[0]:
        return
    project = storage.new_project(
        "Loan platform discovery",
        "Synthetic coursework case: define a staff workspace for a proposed loan-processing application, with traceable requirements and review gates.",
        "India (legal applicability unverified)",
        synthetic=True,
    )
    source = add_source(
        project,
        "The system shall authenticate staff before exposing restricted application records.\nThe system shall enforce role-based access for analysts and managers.\nThe system shall record approval decisions in an audit trail with actor and timestamp.\nThe system shall display application status quickly.\nThe system shall retain application records for 30 days.\nThe system shall retain application records for 90 days.\nThe system shall comply with applicable RBI and KYC requirements.\nThe system shall record approval decisions in an audit trail with actor and timestamp.",
        "Synthetic stakeholder workshop",
        "Demo lending operations team",
        synthetic=True,
    )
    rules.extract_source(project, source)
    rules.quality(project)
    rules.compliance(project)
    rules.recommend(project, dict(zip(rules.FACTORS, [2, 4, 5, 5, 4, 4, 4, 5, 4])))
    storage.audit(
        project,
        SYSTEM,
        "demo_seeded",
        "Created synthetic input, unapproved requirements, rule findings and advisory recommendations.",
    )
    storage.save_project(conn, project)
