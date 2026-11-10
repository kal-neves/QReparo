from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from .fotos import apagar_arquivo
from .models import Foto


@receiver(post_delete, sender=Foto)
def remover_arquivo_foto(sender, instance, using, **kwargs):
    if instance.arquivo.name:
        storage, nome = instance.arquivo.storage, instance.arquivo.name
        transaction.on_commit(lambda: apagar_arquivo(storage, nome), using=using)
