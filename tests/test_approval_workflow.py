from app.models.approval import ApprovalStatus, ApprovalWorkflow
from app.models.tender import Tender, TenderStatus
from app.models.user import User, UserRole
from app.services.approval_service import init_approval_workflow, process_approval


class FakeQuery:
    def __init__(self, db, model_cls, items=None):
        self.db = db
        self.model_cls = model_cls
        self.items = list(items or [])
        self._filters = []

    def filter(self, *args, **kwargs):
        self._filters.append((args, kwargs))
        return self

    def count(self):
        if not self._filters:
            return len(self.items)
        result = []
        for item in self.items:
            if self._matches(item):
                result.append(item)
        return len(result)

    def all(self):
        if not self._filters:
            return list(self.items)
        return [item for item in self.items if self._matches(item)]

    def order_by(self, *args, **kwargs):
        return self

    def first(self):
        matches = self.all()
        return matches[0] if matches else None

    def _matches(self, item):
        for args, kwargs in self._filters:
            if getattr(item, "tender_id", None) != 7:
                return False
            if getattr(item, "status", None) is None:
                continue
            if getattr(item, "status", None) != ApprovalStatus.PENDING:
                return False
        return True


class FakeDB:
    def __init__(self, workflows=None):
        self.workflows = list(workflows or [])
        self.added = []
        self.committed = False
        self.rolled_back = False

    def query(self, model_cls):
        if model_cls is ApprovalWorkflow:
            return FakeQuery(self, model_cls, self.workflows)
        raise AssertionError(f"Unexpected model: {model_cls}")

    def add_all(self, items):
        self.added.extend(items)

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        return None


def test_init_approval_workflow_uses_single_department_head_step():
    db = FakeDB()
    tender = Tender(id=7, title="Test", budget=1000, deadline=None, created_by=1)

    steps = init_approval_workflow(db, tender)

    assert len(steps) == 1
    assert steps[0].step == 1
    assert tender.approval_status == "pending_approval"
    assert db.added == steps


def test_process_approval_completes_on_department_head_approval():
    workflow = ApprovalWorkflow(id=1, tender_id=7, step=1, status=ApprovalStatus.PENDING)
    db = FakeDB(workflows=[workflow])
    tender = Tender(id=7, title="Test", budget=1000, deadline=None, created_by=1)
    approver = User(id=2, email="head@example.com", role=UserRole.DEPARTMENT_HEAD)

    result = process_approval(db, tender, approver, approved=True, comment="ok")

    assert result.status == ApprovalStatus.APPROVED
    assert tender.approval_status == "approved"
    assert tender.status is None
