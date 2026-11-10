from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q
from django.utils import timezone
from django.urls import reverse
from uuid import uuid4

from .fotos import armazenamento_fotos, caminho_foto


class ConflitoEstado(ValidationError):
    pass


class Tag(models.Model):
    nome = models.CharField(max_length=100, unique=True)
    outro = models.BooleanField(default=False, help_text='Exige descrição no envio.')

    class Meta:
        ordering = ['outro', 'nome']
        constraints = [models.UniqueConstraint(fields=['outro'], condition=Q(outro=True), name='uma_tag_outro')]

    def __str__(self):
        return self.nome


class Chamado(models.Model):
    ABERTO = 'ABERTO'
    RESOLVIDO = 'RESOLVIDO'
    equipamento = models.ForeignKey('equipamentos.Equipamento', on_delete=models.PROTECT, related_name='chamados')
    laboratorio = models.ForeignKey('equipamentos.Laboratorio', on_delete=models.PROTECT)
    problema = models.ForeignKey(Tag, on_delete=models.PROTECT)
    descricao = models.CharField(max_length=250, blank=True)
    status = models.CharField(max_length=10, choices=[(ABERTO, 'Aberto'), (RESOLVIDO, 'Resolvido')], default=ABERTO)
    data_abertura = models.DateTimeField(auto_now_add=True)
    data_conclusao = models.DateTimeField(null=True, blank=True)
    conteudo_removido = models.BooleanField(default=False)

    class Meta:
        ordering = ['-data_abertura', '-pk']
        constraints = [models.CheckConstraint(
            condition=(Q(status='ABERTO', data_conclusao__isnull=True, conteudo_removido=False)
                       | Q(status='RESOLVIDO', data_conclusao__isnull=False, conteudo_removido=True, descricao='')),
            name='chamado_ciclo_e_descarte',
        )]

    def clean(self):
        if self.status == self.ABERTO and self.problema_id and self.problema.outro and not self.descricao.strip():
            raise ValidationError({'descricao': 'Descreva o problema para continuar.'})

    def save(self, *args, **kwargs):
        # Adaptação da transição individual existente. Lotes/conferência ficam
        # para outro commit; não usar QuerySet.update para atendimento.
        using = kwargs.get('using') or self._state.db or 'default'
        with transaction.atomic(using=using):
            if self.pk:
                anterior = type(self).objects.using(using).select_for_update().get(pk=self.pk)
                if anterior.status == self.RESOLVIDO:
                    raise ConflitoEstado('Relatos resolvidos não podem ser alterados ou reabertos.')
                if self.equipamento_id != anterior.equipamento_id or self.problema_id != anterior.problema_id:
                    raise ValidationError('Não é permitido trocar equipamento ou problema do relato.')
                self.laboratorio_id = anterior.laboratorio_id
            else:
                from equipamentos.models import Equipamento
                equipamento = Equipamento.objects.using(using).select_for_update().select_related('local').get(pk=self.equipamento_id)
                if not equipamento.ativo or self.status != self.ABERTO:
                    raise ValidationError('O relato deve ser Aberto e o equipamento deve estar ativo.')
                self.laboratorio_id = equipamento.local.laboratorio_id
            if self.status == self.RESOLVIDO:
                self.descricao = ''
                self.data_conclusao = timezone.now()
                self.conteudo_removido = True
                if kwargs.get('update_fields') is not None:
                    kwargs['update_fields'] = set(kwargs['update_fields']) | {
                        'status', 'descricao', 'data_conclusao', 'conteudo_removido',
                    }
            self.full_clean()
            super().save(*args, **kwargs)
            if self.status == self.RESOLVIDO:
                self.fotos.all().delete()

    def __str__(self):
        # Não incluir texto livre em representações usadas por logs/Admin.
        return f'Relato #{self.pk} — {self.status}'


class Foto(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    chamado = models.ForeignKey(Chamado, on_delete=models.CASCADE, related_name='fotos')
    arquivo = models.FileField(storage=armazenamento_fotos, upload_to=caminho_foto)
    posicao = models.PositiveSmallIntegerField()
    largura = models.PositiveIntegerField()
    altura = models.PositiveIntegerField()
    tamanho = models.PositiveIntegerField()

    class Meta:
        ordering = ['posicao']
        constraints = [
            models.UniqueConstraint(fields=['chamado', 'posicao'], name='foto_posicao_unica'),
            models.CheckConstraint(condition=Q(posicao__in=[1, 2]), name='foto_posicao_valida'),
        ]

    def get_absolute_url(self):
        return reverse('chamados:foto', args=[self.chamado_id, self.pk])
