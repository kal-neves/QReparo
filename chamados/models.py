from django.db import models
from django.conf import settings
from django.utils import timezone


class Chamado(models.Model):
    """
    Representa uma solicitação de reparo ou manutenção aberta por um usuário
    (aluno, professor ou técnico) para um equipamento acadêmico específico.
    """

    # Opções de Status
    STATUS_ABERTO = 'ABERTO'
    STATUS_EM_ATENDIMENTO = 'EM_ATENDIMENTO'
    STATUS_RESOLVIDO = 'RESOLVIDO'
    STATUS_CANCELADO = 'CANCELADO'

    STATUS_CHOICES = [
        (STATUS_ABERTO, 'Aberto'),
        (STATUS_EM_ATENDIMENTO, 'Em Atendimento'),
        (STATUS_RESOLVIDO, 'Resolvido'),
        (STATUS_CANCELADO, 'Cancelado'),
    ]

    # Opções de Prioridade
    PRIORIDADE_BAIXA = 'BAIXA'
    PRIORIDADE_MEDIA = 'MEDIA'
    PRIORIDADE_ALTA = 'ALTA'
    PRIORIDADE_URGENTE = 'URGENTE'

    PRIORIDADE_CHOICES = [
        (PRIORIDADE_BAIXA, 'Baixa'),
        (PRIORIDADE_MEDIA, 'Média'),
        (PRIORIDADE_ALTA, 'Alta'),
        (PRIORIDADE_URGENTE, 'Urgente'),
    ]

    # Informações do Chamado
    titulo = models.CharField(
        max_length=150,
        verbose_name='Título do Chamado',
        help_text='Resumo do problema (ex: Monitor piscando, Projetor sem imagem)'
    )

    descricao = models.TextField(
        verbose_name='Descrição do Problema',
        help_text='Explique detalhadamente o sintoma, como reproduzir e impacto nas aulas/pesquisa'
    )

    # Relacionamento com Equipamento
    equipamento = models.ForeignKey(
        'equipamentos.Equipamento',
        on_delete=models.CASCADE,
        related_name='chamados',
        verbose_name='Equipamento',
        help_text='Equipamento acadêmico que apresentou o defeito'
    )

    # Atores do processo
    solicitante = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='chamados_solicitados',
        verbose_name='Solicitante',
        help_text='Usuário institucional que abriu a solicitação'
    )

    tecnico_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chamados_atribuidos',
        verbose_name='Técnico Responsável',
        help_text='Técnico do laboratório/TI encarregado da manutenção'
    )

    # Classificação
    prioridade = models.CharField(
        max_length=20,
        choices=PRIORIDADE_CHOICES,
        default=PRIORIDADE_MEDIA,
        verbose_name='Prioridade'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ABERTO,
        verbose_name='Status do Chamado'
    )

    # Fechamento e Laudo Técnico
    laudo_tecnico = models.TextField(
        blank=True,
        verbose_name='Laudo Técnico / Diagnóstico e Solução',
        help_text='Relatório emitido pelo técnico explicando peças trocadas, causas e testes realizados'
    )

    # Linha do Tempo
    data_abertura = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Data de Abertura'
    )

    data_atualizacao = models.DateTimeField(
        auto_now=True,
        verbose_name='Última Atualização'
    )

    data_conclusao = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data de Conclusão'
    )

    class Meta:
        verbose_name = 'Chamado'
        verbose_name_plural = 'Chamados'
        ordering = ['-data_abertura']

    def __str__(self):
        return f"#{self.id} - {self.titulo} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        """
        Regra de negócio automática:
        1. Se o status for RESOLVIDO e data_conclusao não estiver definida, salva a data atual.
        2. Atualiza de forma sincronizada o status operacional do equipamento:
           - Se chamado em atendimento ou urgente aberto, coloca o equipamento em MANUTENCAO.
           - Se chamado for resolvido, checa se não restam outros chamados abertos e restaura para OPERACIONAL.
        """
        if self.status == self.STATUS_RESOLVIDO and not self.data_conclusao:
            self.data_conclusao = timezone.now()
        elif self.status != self.STATUS_RESOLVIDO and self.data_conclusao:
            # Caso reabram o chamado
            self.data_conclusao = None

        super().save(*args, **kwargs)

        # Atualização inteligente do Equipamento
        equipamento = self.equipamento
        if self.status in [self.STATUS_ABERTO, self.STATUS_EM_ATENDIMENTO]:
            if self.prioridade == self.PRIORIDADE_URGENTE:
                equipamento.status = 'INOPERANTE'
            elif equipamento.status == 'OPERACIONAL':
                equipamento.status = 'MANUTENCAO'
            equipamento.save(update_fields=['status'])
        elif self.status == self.STATUS_RESOLVIDO:
            # Se não houver outros chamados pendentes para este equipamento, torna-o operacional
            outros_abertos = equipamento.chamados.filter(
                status__in=[self.STATUS_ABERTO, self.STATUS_EM_ATENDIMENTO]
            ).exclude(id=self.id).exists()
            if not outros_abertos and equipamento.status != 'OPERACIONAL':
                equipamento.status = 'OPERACIONAL'
                equipamento.save(update_fields=['status'])
