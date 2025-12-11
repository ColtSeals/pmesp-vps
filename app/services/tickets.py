from typing import List
from sqlalchemy.orm import Session

from .. import models
from ..schemas import TicketCreate, TicketRead


def create_ticket(db: Session, data: TicketCreate) -> TicketRead:
    """Cria um novo chamado vinculado ao usuário."""
    user = db.query(models.User).filter_by(username=data.username).first()
    if not user:
        raise ValueError("Usuário não encontrado")

    ticket = models.Ticket(
        user_id=user.id,
        title=data.title,
        description=data.description,
        status="ABERTO",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    return TicketRead(
        id=ticket.id,
        user_id=user.id,
        username=user.username,
        title=ticket.title,
        description=ticket.description,
        status=ticket.status,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def list_tickets(db: Session) -> List[TicketRead]:
    """Lista todos os chamados."""
    tickets = db.query(models.Ticket).order_by(models.Ticket.id.desc()).all()
    result: list[TicketRead] = []

    for t in tickets:
        user = t.user  # relação
        result.append(
            TicketRead(
                id=t.id,
                user_id=t.user_id,
                username=user.username if user else "desconhecido",
                title=t.title,
                description=t.description,
                status=t.status,
                created_at=t.created_at,
                updated_at=t.updated_at,
            )
        )
    return result
