from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.models.exercicio import Exercicio, StatusExercicio


class ExercicioRepositorio:
    """Classe de repositório para operações de banco de dados relacionadas a exercícios."""

    def __init__(self, session: Session):
        self.session = session

    def criar_exercicio(self, exercicio: Exercicio) -> Exercicio:
        """Cria um novo exercício no banco de dados."""
        self.session.add(exercicio)
        self.session.commit()
        self.session.refresh(exercicio)
        return exercicio

    def obter_exercicio_por_id(self, exercicio_id: str) -> Exercicio | None:
        """Obtém um exercício pelo ID."""
        stmt = select(Exercicio).where(Exercicio.id == exercicio_id)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def obter_exercicio_por_external_id(self, id_externo: str) -> Exercicio | None:
        """Obtém um exercício pelo ID externo."""
        stmt = select(Exercicio).where(Exercicio.id_externo == id_externo)
        result = self.session.execute(stmt).scalar_one_or_none()
        return result

    def buscar_exercicios(
        self,
        nome: str | None = None,
        categoria: str | None = None,
        grupo_muscular: str | None = None,
        limite: int = 10,
    ) -> list[Exercicio]:
        """Busca exercícios ativos com base em critérios opcionais.

        Quando `nome` é informado, a busca é feita em todos os campos textuais
        (nome em inglês, categoria, rótulo, grupo muscular e equipamento em PT-BR)
        usando OR — permitindo que o usuário pesquise tanto em inglês quanto em
        português sem necessidade de tradução prévia.
        """
        stmt = select(Exercicio).where(Exercicio.status == StatusExercicio.ATIVO.value)

        if nome:
            termo = f"%{nome}%"
            stmt = stmt.where(
                or_(
                    Exercicio.nome.ilike(termo),
                    Exercicio.categoria.ilike(termo),
                    Exercicio.rotulo.ilike(termo),
                    Exercicio.grupo_muscular.ilike(termo),
                    Exercicio.equipamento.ilike(termo),
                )
            )

        if categoria:
            stmt = stmt.where(Exercicio.categoria.ilike(f"%{categoria}%"))

        if grupo_muscular:
            stmt = stmt.where(Exercicio.grupo_muscular.ilike(f"%{grupo_muscular}%"))

        stmt = stmt.limit(limite)
        result = self.session.execute(stmt).scalars().all()
        return result

    def atualizar_exercicio(self, exercicio: Exercicio) -> Exercicio:
        """Atualiza um exercício existente no banco de dados."""
        self.session.commit()
        self.session.refresh(exercicio)
        return exercicio