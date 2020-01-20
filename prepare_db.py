from models import Administrator
from run import init_app

init_app()

admin = Administrator()
admin.username = input("Введите логин для входа в админпанель: ")
admin.password = input("Введите пароль: ")
admin.save()
