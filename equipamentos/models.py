from django.db import models


class Equipamento(models.Model):
    """
    Representa um equipamento acadêmico inventariado na universidade
    (computadores, projetores, instrumentos de bancada, microscópios, etc.)
    """

    # Opções de Status Operacional
    STATUS_OPERACIONAL = 'OPERACIONAL'
    STATUS_MANUTENCAO = 'MANUTENCAO'
    STATUS_INOPERANTE = 'INOPERANTE'

    STATUS_CHOICES = [
        (STATUS_OPERACIONAL, 'Operacional'),
        (STATUS_MANUTENCAO, 'Em Manutenção'),
        (STATUS_INOPERANTE, 'Inoperante'),
    ]

    # Opções de Categoria no ambiente universitário
    CATEGORIA_INFORMATICA = 'INFORMATICA'
    CATEGORIA_LABORATORIO = 'LABORATORIO'
    CATEGORIA_AUDIOVISUAL = 'AUDIOVISUAL'
    CATEGORIA_CLIMATIZACAO = 'CLIMATIZACAO'
    CATEGORIA_REDE = 'REDE'
    CATEGORIA_OUTROS = 'OUTROS'

    CATEGORIA_CHOICES = [
        (CATEGORIA_INFORMATICA, 'Informática e Computadores'),
        (CATEGORIA_LABORATORIO, 'Instrumentação e Laboratório'),
        (CATEGORIA_AUDIOVISUAL, 'Audiovisual e Multimídia'),
        (CATEGORIA_CLIMATIZACAO, 'Climatização e Refrigeração'),
        (CATEGORIA_REDE, 'Infraestrutura de Rede'),
        (CATEGORIA_OUTROS, 'Outros Equipamentos'),
    ]

    # Campos principais
    nome = models.CharField(
        max_length=150,
        verbose_name='Nome do Equipamento',
        help_text='Ex: Microcomputador Dell OptiPlex, Projetor Epson PowerLite'
    )

    codigo_patrimonio = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        verbose_name='Código de Patrimônio',
        help_text='Identificador único do patrimônio institucional (etiqueta ou QR Code)'
    )

    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIA_CHOICES,
        default=CATEGORIA_INFORMATICA,
        verbose_name='Categoria'
    )

    localizacao = models.CharField(
        max_length=100,
        verbose_name='Localização',
        help_text='Ex: Bloco B - Laboratório de Redes (Sala 204), Auditório Central'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_OPERACIONAL,
        verbose_name='Status Operacional'
    )

    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição / Especificações Técnicas',
        help_text='Detalhes técnicos, número de série, configurações ou observações'
    )

    # Auditoria e Rastreabilidade
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Cadastrado em'
    )

    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )

    class Meta:
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['nome', 'codigo_patrimonio']

    def __str__(self):
        return f"{self.nome} [{self.codigo_patrimonio}] - {self.get_status_display()}"

    @property
    def total_chamados(self):
        """Retorna o total histórico de chamados deste equipamento."""
        return self.chamados.count()

    @property
    def total_chamados_abertos(self):
        """Retorna a quantidade de chamados em aberto ou em atendimento."""
        return self.chamados.filter(status__in=['ABERTO', 'EM_ATENDIMENTO']).count()

    @property
    def tem_chamado_pendente(self):
        """Indica se há algum chamado em andamento para o equipamento."""
        return self.total_chamados_abertos > 0
