from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('equipamentos', '0002_mvp_facil')]

    operations = [
        migrations.AddField(
            model_name='equipamento',
            name='categoria',
            field=models.CharField(blank=True, max_length=100),
        ),
    ]
