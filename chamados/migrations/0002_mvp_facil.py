from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q
from django.utils import timezone


def converter_relatos(apps, schema_editor):
    Chamado = apps.get_model('chamados', 'Chamado')
    Tag = apps.get_model('chamados', 'Tag')
    alias = schema_editor.connection.alias
    relatos = Chamado.objects.using(alias)
    # Não interpretar cancelamento como reparo nem truncar texto silenciosamente.
    if relatos.exclude(status__in=['ABERTO', 'EM_ATENDIMENTO', 'RESOLVIDO']).exists():
        raise RuntimeError('Há relatos cancelados ou com estado desconhecido. Classifique-os explicitamente antes de migrar.')
    if any(len(r.descricao) > 250 for r in relatos.exclude(status='RESOLVIDO').iterator()):
        raise RuntimeError('Há descrições abertas com mais de 250 caracteres. Revise-as antes de migrar.')
    Tag.objects.using(alias).get_or_create(outro=True, defaults={'nome': 'Outro problema'})
    if relatos.exists():
        legado = Tag.objects.using(alias).create(nome='Problema legado (não classificado)')
        for relato in relatos.select_related('equipamento__local').iterator():
            relato.problema = legado
            relato.laboratorio_id = relato.equipamento.local.laboratorio_id
            if relato.status == 'RESOLVIDO':
                relato.descricao = ''
                relato.conteudo_removido = True
                relato.data_conclusao = relato.data_conclusao or relato.data_atualizacao or timezone.now()
            else:
                relato.status = 'ABERTO'
                relato.data_conclusao = None
            relato.save(using=alias)
    # Logs antigos do Admin podem conter título/texto e autoria do atendimento.
    ContentType = apps.get_model('contenttypes', 'ContentType')
    LogEntry = apps.get_model('admin', 'LogEntry')
    ids = ContentType.objects.using(alias).filter(app_label='chamados', model='chamado').values_list('pk', flat=True)
    LogEntry.objects.using(alias).filter(content_type_id__in=ids).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('chamados', '0001_initial'),
        ('equipamentos', '0002_mvp_facil'),
        ('admin', '0003_logentry_add_action_flag_choices'),
    ]
    operations = [
        migrations.CreateModel(name='Tag', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('nome', models.CharField(max_length=100, unique=True)),
            ('outro', models.BooleanField(default=False, help_text='Exige descrição no envio.')),
        ], options={'ordering': ['outro', 'nome'], 'constraints': [
            models.UniqueConstraint(fields=['outro'], condition=Q(outro=True), name='uma_tag_outro')]}),
        migrations.AddField('chamado', 'problema', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='chamados.tag')),
        migrations.AddField('chamado', 'laboratorio', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='equipamentos.laboratorio')),
        migrations.AddField('chamado', 'conteudo_removido', models.BooleanField(default=False)),
        migrations.RunPython(converter_relatos),
        *[migrations.RemoveField('chamado', campo) for campo in [
            'titulo', 'solicitante', 'tecnico_responsavel', 'prioridade', 'laudo_tecnico', 'data_atualizacao']],
        migrations.AlterField('chamado', 'equipamento', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='chamados', to='equipamentos.equipamento')),
        migrations.AlterField('chamado', 'problema', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='chamados.tag')),
        migrations.AlterField('chamado', 'laboratorio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='equipamentos.laboratorio')),
        migrations.AlterField('chamado', 'descricao', models.CharField(max_length=250, blank=True)),
        migrations.AlterField('chamado', 'status', models.CharField(max_length=10, choices=[('ABERTO', 'Aberto'), ('RESOLVIDO', 'Resolvido')], default='ABERTO')),
        migrations.AlterField('chamado', 'data_abertura', models.DateTimeField(auto_now_add=True)),
        migrations.AlterField('chamado', 'data_conclusao', models.DateTimeField(null=True, blank=True)),
        migrations.AlterModelOptions('chamado', {'ordering': ['-data_abertura', '-pk']}),
        migrations.AddConstraint('chamado', models.CheckConstraint(
            condition=(Q(status='ABERTO', data_conclusao__isnull=True, conteudo_removido=False)
                       | Q(status='RESOLVIDO', data_conclusao__isnull=False, conteudo_removido=True, descricao='')),
            name='chamado_ciclo_e_descarte')),
    ]
