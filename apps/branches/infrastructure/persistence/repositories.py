from apps.branches.domain.entities import Branch
from apps.branches.infrastructure.persistence.models import BranchModel
from core.repositories import BaseRepository


class DjangoBranchRepository(BaseRepository[Branch, BranchModel]):
    def __init__(self, db_alias: str = "default") -> None:
        super().__init__(BranchModel, Branch, db_alias)
