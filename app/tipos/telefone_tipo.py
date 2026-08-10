import re
from sqlalchemy import types

class Telefone(types.TypeDecorator):
    """Tipo personalizado para validar e formatar telefones no SQLAlchemy puro."""
    
    # Define que no banco de dados o telefone será um VARCHAR(11)
    impl = types.String(11)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Prepara o dado ANTES de salvar no banco (limpa a string)."""
        if value is None:
            return None
        
        # Remove parênteses, traços e espaços
        string_limpa = re.sub(r'\D', '', str(value))
        
        # Valida se possui tamanho de telefone brasileiro (DDD + 8 ou 9 dígitos)
        if len(string_limpa) not in (10, 11):
            raise ValueError("Telefone inválido! Deve conter DDD + 8 ou 9 dígitos.")
            
        return string_limpa

    def process_result_value(self, value, dialect):
        """Formata o dado APÓS buscar do banco (retorna string formatada)."""
        if value is None:
            return None
            
        # Retorna no formato (XX) XXXXX-XXXX ou (XX) XXXX-XXXX
        if len(value) == 11:
            return f"({value[:2]}) {value[2:7]}-{value[7:]}"
        return f"({value[:2]}) {value[2:6]}-{value[6:]}"
