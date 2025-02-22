# Generated by Django 4.2.19 on 2025-02-21 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_alter_user_role'),
    ]

    operations = [
        migrations.AlterField(
            model_name='class',
            name='language',
            field=models.CharField(choices=[('ru', 'Russian'), ('kz', 'Kazakh'), ('en', 'English')], default='kz', max_length=50),
        ),
        migrations.AlterField(
            model_name='class',
            name='section',
            field=models.CharField(choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D'), ('E', 'E'), ('F', 'F'), ('G', 'G'), ('H', 'H'), ('I', 'I'), ('J', 'J'), ('K', 'K'), ('L', 'L'), ('M', 'M'), ('N', 'N'), ('O', 'O'), ('P', 'P'), ('Q', 'Q'), ('R', 'R'), ('S', 'S'), ('T', 'T'), ('U', 'U'), ('V', 'V'), ('W', 'W'), ('X', 'X'), ('Y', 'Y'), ('Z', 'Z'), ('А', 'А'), ('Б', 'Б'), ('В', 'В'), ('Г', 'Г'), ('Д', 'Д'), ('Е', 'Е'), ('Ж', 'Ж'), ('З', 'З'), ('И', 'И'), ('Й', 'Й'), ('К', 'К'), ('Л', 'Л'), ('М', 'М'), ('Н', 'Н'), ('О', 'О'), ('П', 'П'), ('Р', 'Р'), ('С', 'С'), ('Т', 'Т'), ('У', 'У'), ('Ф', 'Ф'), ('Х', 'Х'), ('Ц', 'Ц'), ('Ч', 'Ч'), ('Ш', 'Ш'), ('Щ', 'Щ'), ('Ъ', 'Ъ'), ('Ы', 'Ы'), ('Ь', 'Ь'), ('Э', 'Э'), ('Ю', 'Ю'), ('Я', 'Я'), ('Ә', 'Ә'), ('ә', 'ә'), ('Ӛ', 'Ӛ'), ('ӛ', 'ӛ'), ('Ӝ', 'Ӝ'), ('ӝ', 'ӝ'), ('Ӟ', 'Ӟ'), ('ӟ', 'ӟ'), ('Ӡ', 'Ӡ'), ('ӡ', 'ӡ'), ('Ӣ', 'Ӣ'), ('ӣ', 'ӣ'), ('Ӥ', 'Ӥ'), ('ӥ', 'ӥ'), ('Ӧ', 'Ӧ'), ('ӧ', 'ӧ'), ('Ө', 'Ө')], max_length=1),
        ),
        migrations.AlterField(
            model_name='student',
            name='language',
            field=models.CharField(choices=[('ru', 'Russian'), ('kz', 'Kazakh'), ('en', 'English')], default='kz', max_length=50),
        ),
    ]
