from equipamentos.models import Equipamento

from .models import Chamado


def criar_relato(*, token, problema, descricao):
    equipamento = Equipamento.objects.get(qr_token=token)
    return Chamado.objects.create(
        equipamento=equipamento, problema=problema, descricao=descricao.strip(),
    )
