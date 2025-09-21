from dataclasses import dataclass
from typing import Optional

@dataclass
class User:
    id: int
    nombre: str
    email: str
    password_hash: str

    # Métodos requeridos por Flask-Login
    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_active(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False
