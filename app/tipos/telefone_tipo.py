import re
from sqlalchemy.types import TypeDecorator, String


class TelefoneValue:

    """Classe para representar um telefone com DDD e número, garantindo validação e formatação."""

    def __init__(self, numero_texto: str):

        """Inicializa o objeto TelefoneValue a partir de uma string de telefone."""

        # Remove parênteses, espaços e traços para limpar a string
        numero_limpo = re.sub(r'\D', '', numero_texto)
        
        # Valida se tem 10 (fixo) ou 11 (celular) dígitos
        if len(numero_limpo) not in [10, 11]:
            raise ValueError("Telefone inválido! Deve conter DDD + 8 ou 9 dígitos.")
            
        self.ddd = numero_limpo[:2]
        self.numero = numero_limpo[2:]

    def __str__(self):

        """Retorna o telefone formatado como string."""

        # Retorna o telefone formatado padrão: (XX) XXXXX-XXXX
        if len(self.numero) == 9:
            return f"({self.ddd}) {self.numero[:5]}-{self.numero[5:]}"
        return f"({self.ddd}) {self.numero[:4]}-{self.numero[4:]}"

    def __repr__(self):
        return f"TelefoneValue('{self.ddd}{self.numero}')"

    def __eq__(self, other):
        if isinstance(other, TelefoneValue):
            return self.ddd == other.ddd and self.numero == other.numero
        return NotImplemented

    def __hash__(self):
        return hash((self.ddd, self.numero))


class Telefone(TypeDecorator):
    """Tipo personalizado para validar e formatar telefones no SQLAlchemy puro."""
    
    impl = String(20) # Armazena como string no banco de dados, com tamanho máximo
    cache_ok = True

    def process_bind_param(self, value, dialect):
        """Converte o objeto TelefoneValue para string para armazenamento no banco."""
        if value is None:
            return None
        if isinstance(value, TelefoneValue):
            return f"{value.ddd}{value.numero}" # Armazena apenas os dígitos limpos
        raise TypeError(f"Esperado TelefoneValue, recebido {type(value)}")

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        return TelefoneValue(value)

if __name__ == "__main__":
    # Exemplo de uso:
    meu_tel = TelefoneValue("11999998888")
    print(meu_tel)  # Saída: (11) 99999-8888
