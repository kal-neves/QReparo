import uuid
from django.db import models


class Laboratorio(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nome = models.CharField(max_length=150)

    def __str__(self):
        return self.nome


class Local(models.Model):
    laboratorio = models.ForeignKey(Laboratorio, on_delete=models.PROTECT)
    nome = models.CharField(max_length=150)

    class Meta:
        constraints = [models.UniqueConstraint(fields=['laboratorio', 'nome'], name='local_unico_no_laboratorio')]

    def __str__(self):
        return f'{self.laboratorio} — {self.nome}'


class Equipamento(models.Model):
    nome = models.CharField(max_length=150)
    codigo_patrimonio = models.CharField(max_length=50, unique=True)
    descricao = models.TextField(blank=True)
    categoria = models.CharField(max_length=100, blank=True)
    local = models.ForeignKey(Local, on_delete=models.PROTECT)
    ativo = models.BooleanField(default=True)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    class Meta:
        ordering = ['nome', 'codigo_patrimonio']

    def __str__(self):
        return f'{self.nome} [{self.codigo_patrimonio}]'

    @property
    def total_chamados(self):
        return self.chamados.count()

    @property
    def total_chamados_abertos(self):
        return self.chamados.filter(status='ABERTO').count()

    @property
    def tem_chamado_pendente(self):
        return self.chamados.filter(status='ABERTO').exists()
