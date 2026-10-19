"""Policy models: the sections of the store manual."""
from pydantic import BaseModel, ConfigDict


class PolicySection(BaseModel):
    """One numbered section of the manual, such as "3.1 Regras de Parcelamento".

    `parent_title` is the title of the enclosing section ("Formas de Pagamento" for 3.1), which
    gives a short subsection the context it needs to be understood on its own.
    """

    model_config = ConfigDict(frozen=True)

    number: str
    title: str
    parent_title: str | None = None
    text: str

    @property
    def heading(self) -> str:
        """The number and title, plus the parent title: `3.1 Regras de Parcelamento (Formas de Pagamento)`."""
        suffix = f" ({self.parent_title})" if self.parent_title else ""
        return f"{self.number} {self.title}{suffix}"
