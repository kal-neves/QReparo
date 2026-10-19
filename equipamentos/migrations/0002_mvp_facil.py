import uuid
from django.db import migrations, models
import django.db.models.deletion


def converter_locais(apps, schema_editor):
    Equipamento = apps.get_model('equipamentos', 'Equipamento')
    Laboratorio = apps.get_model('equipamentos', 'Laboratorio')
    Local = apps.get_model('equipamentos', 'Local')
    alias = schema_editor.connection.alias
    if not Equipamento.objects.using(alias).exists():
        return
    # A localização antiga é texto livre; não inventar uma classificação histórica.
    lab = Laboratorio.objects.using(alias).create(codigo='LEGADO-REVISAR', nome='Laboratório legado (revisar)')
    for equipamento in Equipamento.objects.using(alias).all().iterator():
        local, _ = Local.objects.using(alias).get_or_create(laboratorio=lab, nome=equipamento.localizacao or 'Local não informado')
        equipamento.local = local
        equipamento.qr_token = uuid.uuid4()
        equipamento.save(using=alias, update_fields=['local', 'qr_token'])


class Migration(migrations.Migration):
    dependencies = [('equipamentos', '0001_initial')]
    operations = [
        migrations.CreateModel(name='Laboratorio', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('codigo', models.CharField(max_length=50, unique=True)),
            ('nome', models.CharField(max_length=150)),
        ]),
        migrations.CreateModel(name='Local', fields=[
            ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
            ('nome', models.CharField(max_length=150)),
            ('laboratorio', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='equipamentos.laboratorio')),
        ], options={'constraints': [models.UniqueConstraint(fields=['laboratorio', 'nome'], name='local_unico_no_laboratorio')]}),
        migrations.AddField('equipamento', 'local', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='equipamentos.local')),
        migrations.AddField('equipamento', 'qr_token', models.UUIDField(null=True, editable=False)),
        migrations.AddField('equipamento', 'ativo', models.BooleanField(default=True)),
        migrations.RunPython(converter_locais),  # Sem reversão: tokens e locais não podem ser reconstruídos.
        migrations.AlterField('equipamento', 'local', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='equipamentos.local')),
        migrations.AlterField('equipamento', 'qr_token', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
        migrations.RemoveField('equipamento', 'categoria'),
        migrations.RemoveField('equipamento', 'localizacao'),
        migrations.RemoveField('equipamento', 'status'),
        migrations.RemoveField('equipamento', 'criado_em'),
        migrations.RemoveField('equipamento', 'atualizado_em'),
        migrations.AlterField('equipamento', 'nome', models.CharField(max_length=150)),
        migrations.AlterField('equipamento', 'codigo_patrimonio', models.CharField(max_length=50, unique=True)),
        migrations.AlterField('equipamento', 'descricao', models.TextField(blank=True)),
        migrations.AlterModelOptions('equipamento', {'ordering': ['nome', 'codigo_patrimonio']}),
    ]
