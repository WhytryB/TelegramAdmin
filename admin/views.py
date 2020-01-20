import base64
from threading import Thread
from json import loads, dumps
from time import sleep
from datetime import datetime

import flask
import telebot
from flask import Blueprint, redirect, url_for, request, render_template, flash
from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.mongoengine import ModelView
from flask_login import LoginManager, current_user, login_user, logout_user
from telebot.apihelper import ApiException
import mongoengine

import admin.methods as methods
import defaults
from admin.forms import LoginForm, SaleForm
from bot.bot_manager import BotManager
from models import User, Administrator, Texts, Mailing, District, Payment, City, BotProfile, Good, BotPhoto, LeadTexts, \
    LeadRequest, WithdrawRequest, Order, Sale, StorageModel
import datetime as dt
admin_blueprint = Blueprint('admin_bp', __name__)
login = LoginManager()

BOTS_INDEX_BREADCRUMBS = [{
    'name': '@',
    'url': '/admin/bots'
}]


def parse_like_term(term):
    case_sensitive = term.startswith('*')
    if case_sensitive:
        term = term[1:]
    # apply operators
    if term.startswith('^'):
        oper = 'startswith'
        term = term[1:]
    elif term.startswith('='):
        oper = 'exact'
        term = term[1:]
    else:
        oper = 'contains'
    # add case insensitive flag
    if not case_sensitive:
        oper = 'i' + oper
    return oper, term


@login.user_loader
def load_user(user_id):
    return Administrator.objects(id=user_id).first()


@admin_blueprint.route('/')
def index():
    return redirect(url_for('admin.index'))


def validate_login(user, form):
    if user is None:
        return False

    if user.password == form.password.data:
        return True
    else:
        return False


@admin_blueprint.route('/login', methods=['GET', 'POST'])
def handle_login():
    if current_user.is_authenticated:
        return redirect('/admin/bots')
    form = LoginForm()
    if form.validate_on_submit():
        user = Administrator.objects(username=form.username.data).first()

        if validate_login(user, form):
            login_user(user)
            flash('Logged in', category='success')
            return redirect(url_for('admin.index'))
        else:
            flash('Wrong username or password', category='danger')

    return render_template('login.html', form=form)


@admin_blueprint.route('/logout')
def handle_logout():
    logout_user()
    return redirect(url_for('admin.index'))


class MyIndexView(AdminIndexView):
    @expose('/')
    def index(self):
        return redirect('bots')


class BreadcrumbsView(ModelView):
    def get_breadcrumbs(self):
        return []

    def _handle_view(self, name, **kwargs):
        self._template_args.update(breadcrumbs=self.get_breadcrumbs())
        return super()._handle_view(name, **kwargs)


class SecureView(BreadcrumbsView):
    def is_accessible(self):
        return current_user.is_authenticated

    def _handle_view(self, name, **kwargs):
        if not self.is_accessible():
            return redirect('/login')
        return super()._handle_view(name, **kwargs)


class RootView(SecureView):

    def _handle_view(self, name, **kwargs):
        menu_items = [{
            'caption': 'Боты',
            'url': '/admin/bots',
        }, {
            'caption': 'Пользователи',
            'url': '/admin/users',
        }, {
            'caption': 'Рассылка',
            'url': '/admin/mailing',
        }, {
            'caption': 'Лиды',
            'url': '/admin/lead-requests',
        }, {
            'caption': 'Кошелек',
            'url': '/admin/wallet',
        }, {
            'caption': 'Заказы',
            'url': '/admin/orders',
        }, {
            'caption': 'Запросы на вывод',
            'url': '/admin/withdraw-requests',
        }, {
            'caption': 'Тексты (лиды)',
            'url': '/admin/lead-texts',
        }, {
            'caption': 'Админы',
            'url': '/admin/settings',
        }]
        for item in menu_items:
            item['active'] = item['caption'] == self.name
        self._template_args.update(menu_items=menu_items)
        return super()._handle_view(name, **kwargs)

    def get_breadcrumbs(self):
        return BOTS_INDEX_BREADCRUMBS


class BotModelView(BreadcrumbsView):

    def set_bot(self, bot_id):
        bot_profile = BotProfile.objects.get(id=bot_id)
        if bot_profile is not None:
            self._template_args.update(bot=bot_profile)

    @expose('/api/file/', methods=('POST',))
    def api_file_view(self, bot_id):
        self.set_bot(bot_id)
        return super().api_file_view()

    @expose('/delete/', methods=('POST',))
    def delete_view(self, bot_id):
        self.set_bot(bot_id)
        return super().delete_view()

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self, bot_id):
        self.set_bot(bot_id)
        return super().edit_view()

    @expose('/create', methods=('GET', 'POST'))
    def create_view(self, bot_id):
        self.set_bot(bot_id)
        return super().create_view()

    @expose('/')
    def index_view(self, bot_id):
        self.set_bot(bot_id)
        return super().index_view()

    def get_url(self, endpoint, **kwargs):
        kwargs.update(bot_id=str(self._template_args['bot'].id))
        return url_for(endpoint, **kwargs)

    def get_breadcrumbs(self):
        res = BOTS_INDEX_BREADCRUMBS + []
        bp = self._template_args.get('bot')
        if bp is not None:
            res.append({
                'name': bp.name,
                'url': url_for('bots/<bot_id>.index_view', bot_id=bp.id)
            })
        return res

    def get_custom_query(self, add_bot):
        query = super().get_query()
        if add_bot:
            query = query.filter(**{'bot_id': str(self._template_args['bot'].id)})
        return query

    def get_query(self):
        return self.get_custom_query(True)


class CityModelView(BotModelView):

    def set_city(self, city_id):
        city = City.objects.get(id=city_id)
        if city is not None:
            self._template_args.update(city=city)

    @expose('/api/file/')
    def api_file_view(self, bot_id, city_id):
        self.set_city(city_id)
        return super().api_file_view(bot_id)

    @expose('/delete/', methods=('POST',))
    def delete_view(self, bot_id, city_id):
        self.set_city(city_id)
        return super().delete_view(bot_id)

    @expose('/edit/', methods=('GET', 'POST'))
    def edit_view(self, bot_id, city_id):
        self.set_city(city_id)
        return super().edit_view(bot_id)

    @expose('/create', methods=('GET', 'POST'))
    def create_view(self, bot_id, city_id):
        self.set_city(city_id)
        self.form_args = dict(city_id=city_id)
        return super().create_view(bot_id)

    @expose('/')
    def index_view(self, bot_id, city_id):
        self.set_city(city_id)
        return super().index_view(bot_id)

    def get_url(self, endpoint, **kwargs):
        kwargs.update(city_id=str(self._template_args['city'].id))
        return super().get_url(endpoint, **kwargs)

    def get_breadcrumbs(self):
        res = super().get_breadcrumbs()
        bot = self._template_args.get('bot')
        city = self._template_args.get('city')
        if city is not None and bot is not None:
            res.append({
                'name': city.name,
                'url': '/admin/bots/%s/%s' % (str(bot.id), str(city.id))
            })
        return res

    def get_query(self):
        return super().get_custom_query(False).filter(**{'city_id': str(self._template_args['city'].id)})


class BotRootView(BotModelView):

    def _handle_view(self, name, **kwargs):
        res = super()._handle_view(name, **kwargs)
        bot = self._template_args.get('bot')
        if bot is not None:
            menu_items = [{
                'caption': 'Города',
                'url': '/admin/bots/%s' % bot.id,
            }, {
                'caption': 'Варианты оплаты',
                'url': '/admin/bots/%s/payments' % bot.id,
            }, {
                'caption': 'Тексты',
                'url': '/admin/bots/%s/texts' % bot.id,
            }, {
                'caption': 'Создать дубликат',
                'url': '/admin/bots/%s/dublicate' % bot.id,
            }]
            for item in menu_items:
                item['active'] = item['caption'] == self.name
            self._template_args.update(menu_items=menu_items)
        return res


class CityRootView(CityModelView):

    def _handle_view(self, name, **kwargs):
        res = super()._handle_view(name, **kwargs)
        bot = self._template_args.get('bot')
        city = self._template_args.get('city')
        if bot is not None and city is not None:
            menu_items = [{
                'caption': 'Продукты',
                'url': '/admin/bots/%s/%s/goods' % (bot.id, city.id),
            }, {
                'caption': 'Районы',
                'url': '/admin/bots/%s/%s/districts' % (bot.id, city.id),
            }]
            for item in menu_items:
                item['active'] = item['caption'] == self.name
            self._template_args.update(menu_items=menu_items)
        return res


import csv
import random, os
from flask_admin import form
import pandas as pd


class   StorageAdminModel(RootView):
    list_template = 'import.html'
    form_extra_fields = {
        'file': form.FileUploadField('file')
    }
    def chanse(self, names, type):
        try:
            if type == "int":
                if str(names) == "nan":
                    return 0
                return int(names)
            elif type == "str":
                if str(names) == "nan":
                    return "'"
                return str(names)
            else:
                if str(names) == "nan":
                    return []
                return list(names.split(","))
        except Exception as e:
            print(e)


    # def _change_path_data(self, _form):
    #     try:
    #         storage_file = _form.file.data
    #
    #         if storage_file is not None:
    #             hash = random.getrandbits(128)
    #             ext = storage_file.filename.split('.')[-1]
    #             path = '%s.%s' % (hash, ext)
    #
    #             storage_file.save(
    #                 os.path.join("files", path)
    #             )
    #
    #             _form.name.data = path
    #             _form.type.data = ext
    #             del _form.file
    #
    #             df = pd.read_excel( os.path.join("files", path), sheet_name='Tablib Dataset')
    #
    #             for i in range(0, len(df.values.tolist())):
    #                 try:
    #                     bot = StorageAdminModel.chanse(self, df['Bot'][i], "str")
    #                     bot = ''.join(bot)
    #                     user_id =StorageAdminModel.chanse(self, df['User Id'][i], "int"),
    #                     user_id = user_id[0]
    #                     username = StorageAdminModel.chanse(self, df['Username'][i], "str"),
    #                     username = ''.join(username)
    #                     first_name =StorageAdminModel.chanse(self, df['First Name'][i], "str") ,
    #                     first_name = ''.join(first_name)
    #                     last_name =StorageAdminModel.chanse(self, df['Last Name'][i], "str") ,
    #                     last_name = ''.join(last_name)
    #                     state = StorageAdminModel.chanse(self, df['State'][i], "str"),
    #                     state = ''.join(state)
    #                     is_admin =StorageAdminModel.chanse(self, df['Is Admin'][i], "str") ,
    #                     is_admin = ''.join(is_admin)
    #                     if is_admin == 'True':
    #                         is_admin = True
    #                     else:
    #                         is_admin = False
    #                     city = StorageAdminModel.chanse(self, df['City'][i], "str"),
    #                     city = ''.join(city)
    #                     good = StorageAdminModel.chanse(self, df['Good'][i], "str"),
    #                     good = ''.join(good)
    #                     district = StorageAdminModel.chanse(self, df['District'][i], "str"),
    #                     district = ''.join(district)
    #                     payment = StorageAdminModel.chanse(self, df['Payment'][i], "str"),
    #                     payment = ''.join(payment)
    #                     code = StorageAdminModel.chanse(self, df['Code'][i], "str"),
    #                     code = ''.join(code)
    #                     clicked_goods = StorageAdminModel.chanse(self, df['Clicked Goods'][i], "list"),
    #                     ordered_goods = StorageAdminModel.chanse(self, df['Ordered Goods'][i], "list"),
    #                     balance =StorageAdminModel.chanse(self, df['Balance'][i], "int"),
    #                     balance= balance[0]
    #                     tax = StorageAdminModel.chanse(self, df['Tax'][i], "int"),
    #                     tax = tax[0]
    #                     wallet = StorageAdminModel.chanse(self, df['Wallet'][i], "str"),
    #                     wallet = ''.join(wallet)
    #                     datetime = StorageAdminModel.chanse(self, df['Datetime'][i], "str")
    #                     datetime = ''.join(datetime)
    #                     try:
    #                         bots = BotProfile.objects.get(name=bot)
    #                         # print(bots, "@@@@@")
    #                     except:
    #                         bots = None
    #                     try:
    #                         city = City.objects.get(name=city)
    #                         # print(city, "@@@@@")
    #                     except:
    #                         city = None
    #                     try:
    #                         good = Good.objects.get(name=good)
    #                         # print(good, "@@@@@")
    #                     except:
    #                         good = None
    #                     try:
    #                         cli = []
    #                         clicked_goods = (list(clicked_goods)[0])
    #                         if len(clicked_goods) == 1:
    #                             cli.append(Good.objects.get(name=clicked_goods[0]))
    #                         else:
    #                             for i in clicked_goods:
    #                                 try:
    #                                     cli.append(Good.objects.get(name=i.replace(' ', '')))
    #                                 except Exception as e:
    #                                     print(e)
    #                                     pass
    #                         # print(cli, "@@@@@@!")
    #                         if cli == []:
    #                             cli = None
    #                     except Exception as e:
    #                         print(e)
    #                         cli = None
    #                     try:
    #                         orde = []
    #                         ordered_goods = (list(ordered_goods)[0])
    #                         if len(ordered_goods) == 1:
    #                             orde.append(Good.objects.get(name= ordered_goods[0]))
    #                         else:
    #                             for i in ordered_goods:
    #                                 try:
    #                                     # print(i)
    #                                     orde.append(Good.objects.get(name= i.replace(' ', '')))
    #                                 except Exception as e:
    #                                     print(e)
    #                                     pass
    #                         # print(orde, "@@@@@@!!")
    #                         if orde == []:
    #                             orde = None
    #                     except:
    #                         orde = None
    #                     try:
    #                         district = District.objects.get(name=district)
    #                         # print(district, "@@@@@")
    #                     except:
    #                         district = None
    #                     try:
    #                         payment = Payment.objects.get(payment_name=payment)
    #                         # print(payment, "@@@@@")
    #                     except:
    #                         payment = None
    #                     try:
    #                         User(
    #                             bot=bots,
    #                             user_id=user_id,
    #                             username=username,
    #                             first_name=first_name,
    #                             last_name=last_name,
    #                             state=state,
    #                             is_admin=is_admin,
    #                             city=city,
    #                             good=good,
    #                             district=district,
    #                             payment=payment,
    #                             code=code,
    #                             clicked_goods=cli,
    #                             ordered_goods=orde,
    #                             balance=balance, tax=tax,
    #                             wallet=wallet,
    #                             datetime=datetime).save()
    #                         flash('Отправлено', category='success')
    #                     except Exception as e:
    #                         print(e)
    #                         User(
    #                             # bot=bot,
    #                             user_id=user_id,
    #                             username=username,
    #                             first_name=first_name,
    #                             last_name=last_name,
    #                             state=state,
    #                             is_admin=is_admin,
    #                             # city=city,
    #                             # good=good,district=district, payment=payment,
    #                              code=code,
    #                             # clicked_goods=clicked_goods,
    #                             #  ordered_goods=ordered_goods,
    #                             balance=balance,tax=tax,
    #                              wallet=wallet,
    #                              datetime=datetime).save()
    #                         flash('Отправлено без связанных полеи', category='success')
    #                 except Exception as e:
    #                     print(e)
    #
    #
    #     except Exception as ex:
    #         print(ex)

    #     return _form

    def _change_path_data(self, _form):
        try:
            storage_file = _form.file.data

            if storage_file is not None:
                hash = random.getrandbits(128)
                ext = storage_file.filename.split('.')[-1]
                path = '%s.%s' % (hash, ext)

                storage_file.save(
                    os.path.join("files", path)
                )

                _form.name.data = path
                _form.type.data = ext
                del _form.file

                df = pd.read_excel( os.path.join("files", path), sheet_name='Tablib Dataset')

                for i in range(0, len(df.values.tolist())):
                    try:

                        user_id =StorageAdminModel.chanse(self, df['User Id'][i], "int"),
                        user_id = user_id[0]
                        first_name =StorageAdminModel.chanse(self, df['First Name'][i], "str") ,
                        first_name = ''.join(first_name)
                        last_name =StorageAdminModel.chanse(self, df['Last Name'][i], "str") ,
                        last_name = ''.join(last_name)

                        try:
                            User(
                                user_id=user_id,
                                first_name=first_name,
                                last_name=last_name).save()
                            flash('Отправлено', category='success')
                        except Exception as e:
                            print(e)
                            flash('Не валидные данные', category='danger')
                    except Exception as e:
                        print(e)
        except Exception as ex:
            print(ex)

        return _form

    def edit_form(self, obj=None):
        return self._change_path_data(
            super(StorageAdminModel, self).edit_form(obj)
        )

    def create_form(self, obj=None):
        return self._change_path_data(
            super(StorageAdminModel, self).create_form(obj)
        )


class MyUserView(RootView):
    list_template = 'user_list.html'
    column_searchable_list = ['username', 'first_name', 'last_name', 'bot']
    can_set_page_size = True
    column_filters = ['username', 'first_name', 'last_name', 'datetime']
    can_export = True
    can_import = True
    export_types = ['xls']


    allowed_search_types = (mongoengine.StringField,
                            mongoengine.URLField,
                            mongoengine.EmailField,
                            mongoengine.fields.ReferenceField,
                            )

    @expose('last24')
    def last24(self):
        count = 0
        users = User.objects()
        for user in users:
            date_was = user.datetime
            date_now = datetime.now()
            if not(date_was is None) and (date_now - date_was).total_seconds()/60/60 <= 24:
                count += 1
        return str(count)

    def _search(self, query, search_term):
        op, term = parse_like_term(search_term)

        criteria = None

        for field in self._search_fields:
            if field.name == 'bot':
                bots = BotProfile.objects(name__contains=term)
                for bot in bots:
                    if not (bot is None):
                        flt = {'%s__%s' % (field.name, 'exact'): bot.id}
                        q = mongoengine.Q(**flt)
                        if criteria is None:
                            criteria = q
                        else:
                            criteria |= q
            else:
                flt = {'%s__%s' % (field.name, op): term}
                q = mongoengine.Q(**flt)
            if criteria is None:
                criteria = q
            else:
                criteria |= q

        return query.filter(criteria)

    @expose('<user_id>/send_message', methods=['GET', 'POST'])
    def send_message(self, user_id):
        user = User.objects(id=user_id).first()
        if user is None:
            return '', 404
        if request.form:
            print(request)
            if user.bot:
                body = request.form.get('body')
                bot = BotManager().get(str(user.bot.id))
                if bot is None:
                    flash('Бот не активен', category='error')
                elif body:
                    bot.send_message(user.user_id, body, parse_mode='markdown')
                    flash('Отправлено', category='success')
            return redirect(url_for('users.send_message', user_id=user_id))
        return self.render('user_send_message.html', user=user)


class MyUseridView(RootView):
    list_template = 'userid_list.html'
    column_filters = ['user_id']
    column_list = ['user_id']
    can_export = True
    export_types = ['xls', 'csv']


class MyUsernameView(RootView):
    list_template = 'username_list.html'
    column_searchable_list = ['username']
    column_filters = ['username']
    column_list = ['username']
    can_export = True
    export_types = ['xls', 'csv']







class MyTextsView(BotRootView):
    create_template = 'texts_create.html'
    edit_template = 'texts_edit.html'
    form_columns = ['bot_id','back_btn', 'use_buttons_msg', 'choose_good_msg','choose_city_msg','choose_district_msg',
                    'choose_payment_msg', 'done_btn', 'leads_btn', 'new_order_msg', 'selected_good_msg', 'selected_good_msg2']
    column_list = ['greet_msg', 'choose_good_msg', 'choose_city_msg', 'choose_district_msg', 'choose_payment_msg']

    @expose('/create', methods=('GET', 'POST'))
    def create_view(self, bot_id):
        self._template_args.update(texts=defaults.texts.to_json())
        return super().create_view(bot_id)


class MyMailingView(RootView):
    list_template = 'mailing_list.html'

    @expose('<mailing_id>/send', methods=['GET', 'POST'])
    def send(self, mailing_id):
        mailing = Mailing.objects(id=mailing_id).first()
        if mailing is None:
            return '', 404
        if request.form:
            bots = [dict(bot_id=bot_id, bot=BotManager().get(bot_id)) for bot_id in request.form.getlist('bots')]
            bots = [bot for bot in bots if bot['bot'] is not None]
            if bots is None or len(bots) == 0:
                flash('Нет активных ботов', category='error')
            else:
                for bot in bots:
                    Thread(target=methods.send_messages, args=(bot['bot_id'], bot['bot'], mailing,)).start()
                flash(f'Отправлено ({len(bots)})', category='success')
                return redirect(url_for('mailing.send', mailing_id=mailing_id))
        return self.render('mailing_send.html', mailing=mailing, bots=BotProfile.objects(active=True))




@admin_blueprint.route('/admin/bots/sale', methods=['GET', 'POST'])
def handle_sale():
    form = SaleForm()
    if form.validate_on_submit():
        try:
            sale = int(form.sale.data)
            god = Good.objects()

            for i in god:
                saleFinal = i.sale
                i.sale = sale
                i.saleSecond = saleFinal
                i.PriceWithSale = str(int(int(i.price) - (int(i.price) * (int(sale)/ 100))))
                i.save()
            flash('Скидка применилась для всех ботов', category='success')
        except Exception as e:
            flash('Введены не правильные данные', category='danger')
    return render_template('sale.html', form=form)


@admin_blueprint.route('/admin/bots/unsale', methods=['GET', 'POST'])
def handle_Unsale():
    god = Good.objects()
    for i in god:
        i.sale = i.saleSecond
        i.PriceWithSale = i.SecondSavePrice
        i.save()
    flash('Скидка для всех ботов вернулась', category='success')

    return redirect("/admin/bots")


# @admin_blueprint.route('/admin/users/addNew', methods=['GET', 'POST'])
# def impfile(self):
#     print("1")
#     if request.method == 'POST':
#         print("2")
#         f = request.files['fileupload']
#         fstring = f.read()
#
#         csv_dicts = [{k: v for k, v in row.items()} for row in
#                      csv.DictReader(fstring.splitlines(), skipinitialspace=True)]
#         print(fstring, "2", csv_dicts)
#
#         return "success"
#     return render_template('import.html', form=form)


class MyBotProfileView(RootView):
    list_template = 'bot_list.html'
    create_template = 'bot_create.html'
    edit_template = 'bot_edit.html'
    column_filters = ['name']
    column_list = ['active', 'photo_file_id', 'name', 'stat']
    column_labels = dict(active='Активен', photo_file_id='', name='Name', stat='Statistic ID')


    def statistic(self, username):
            users = User.objects()
            count = 0
            countSec = 0
            countThird = 0
            Err = False
            for user in users:
                try:
                    # print(user.bot, "BOTNAME")
                    if user.bot is not None:
                        name1 = BotProfile(name=user.bot)
                        # print("Second", " 2", name1, type(name1))
                        if str(name1) == str(username):
                            # print("GotchA!!!")
                            count += 1
                            date_was = user.datetime
                            date_now = datetime.now()
                            dates = dt.datetime.today()
                            daysOfMonth = dates.day
                            hours = int(daysOfMonth) * 24
                            # print(hours, 'hours')
                            if not (date_was is None) and (date_now - date_was).total_seconds() / 60 / 60 <= hours:
                                countSec += 1
                            if not (date_was is None) and (date_now - date_was).total_seconds() / 60 / 60 <= 24:
                                countThird += 1
                except Exception as e:
                    print(e)
                    print("Default")
                    Err = True
            if not Err:
                # print(count, "111")
                # print("ste", str(countSec))
                # print("third", str(countThird))
                return "{0}-{1}-{2}".format(count, countSec, countThird)
            else:
                return "{0}-{1}-{2}".format(count, countSec, countThird)


    @expose('fetch')
    def fetch(self):
            try:
                token = request.args['token']
                fb = telebot.TeleBot(token)
                me = fb.get_me()
                FinalId = MyBotProfileView.statistic(self, me.username)
                t_id = str(me.id)
                stat = FinalId
                try:
                    profile = dict(name=me.username, t_id=t_id, stat=stat)
                except Exception as e:
                    print(e)
                    profile = dict(name=me.username, t_id=t_id)
                photos = fb.get_user_profile_photos(me.id, limit=1).photos
                if len(photos) > 0:
                    file_id = photos[0][0].file_id
                    profile['photo_file_id'] = file_id
                    photo = BotPhoto.objects(t_bot_id=t_id, file_id=file_id).first()
                    if photo is None:
                        img = fb.download_file(fb.get_file(file_id).file_path)
                        photo = BotPhoto(t_bot_id=t_id, file_id=file_id, data=img)
                        BotPhoto.save(photo)
                    profile['photo'] = base64.b64encode(photo.data).decode('ascii')
            except ApiException as e:
                print(e)
                return dict(error='WRONG_TOKEN'), 400
            return profile


    @expose('off-all')
    def off_all(self):
        bots = BotProfile.objects()
        for bot in bots:
            bot_id = bot.id.binary.hex()
            if BotManager().is_running(bot_id):
                BotManager().stop(bot_id)
            bot.active = False
            bot.save()
        return 'good'

    @expose('on-all')
    def on_all(self):
        bots = BotProfile.objects()
        for bot in bots:
            bot_id = bot.id.binary.hex()
            if not BotManager().is_running(bot_id):
                try:
                    BotManager().run(bot)
                    bot.active = True
                    bot.save()
                except Exception as ex:
                    if '401' in str(ex):
                        flash('Бот ' + bot.name + ' был забанен')
        return 'good'


    @expose('statistics')
    def statistics(self):
        try:
            Botnames = BotProfile.objects()
            count = 0
            for i in Botnames:
                count += 1
                print("Обновлена статистика у " +  str(count) + "/" + str(len(Botnames)))
                # print(i.name)
                FinalId = MyBotProfileView.statistic(self, i.name)
                i.stat = FinalId
                i.save()
        except ApiException as e:
            print(e)
            return dict(error='WRONG_TOKEN'), 400
        return "good"

    @expose('<bot_id>/active', methods=['POST'])
    def set_active(self, bot_id):
        bot = BotProfile.objects(id=bot_id).first()
        if bot is None:
            return '', 404
        bot.active = request.args['active'] == 'true'
        bot.save()
        if bot.active and not BotManager().is_running(bot_id):
            BotManager().run(bot)
        elif not bot.active and BotManager().is_running(bot_id):
            BotManager().stop(bot_id)
        return {'active': bot.active}

    @expose('<bot_id>/photo')
    def bot_photo(self, bot_id):
        bot = BotProfile.objects(id=bot_id).first()
        if bot is None or bot.photo_file_id is None or len(bot.photo_file_id) == 0:
            return '', 404
        photo = BotPhoto.objects(t_bot_id=bot.t_id, file_id=bot.photo_file_id).first()
        if photo is None:
            return '', 404
        resp = flask.Response(photo.data)
        resp.headers['Content-Type'] = 'image/png'
        return resp

    @expose('/delete/', methods=('POST',))
    def delete_view(self):
        bot_id = request.form.get('id')
        if BotManager().is_running(bot_id):
            BotManager().stop(bot_id)
        return super().delete_view()




class MyCityView(BotRootView):
    list_template = 'city_list.html'
    create_template = 'city_create.html'
    edit_template = 'city_edit.html'
    column_filters = ['name']
    column_list = ['name']


class MyPaymentView(BotRootView):
    create_template = 'payment_create.html'
    edit_template = 'payment_edit.html'
    column_filters = ['payment_name', 'answer_text']
    column_list = ['payment_name', 'answer_text', 'answer_on_payment']


class MyDistrictView(CityRootView):
    create_template = 'district_create.html'
    edit_template = 'district_edit.html'
    column_filters = ['name']
    column_list = ['name']

from flask_admin.actions import action


class MyGoodsView(CityRootView):
    create_template = 'good_create.html'
    edit_template = 'good_edit.html'
    column_list = [
        'name', 'city_id', 'description', 'price', 'sale', 'districts', 'PriceWithSale'
    ]
    form_columns = [
        'name', 'city_id', 'description', 'price', 'sale', 'districts', 'PriceWithSale'
    ]


    form_widget_args = {
        'PriceWithSale': {
            'readonly': True
        },
    }

    def on_model_change(self, form, Good, is_created=False):
        if int(Good.sale) > 0:
            Good.PriceWithSale = str(int(int(Good.price) - (int(Good.price) * (int(Good.sale)/ 100))))
            Good.SecondSavePrice = Good.PriceWithSale
        else:
            Good.PriceWithSale = 0



    # column_filters = ['name']
    # column_list = ['name']


class MyCityOneView(BaseView):
    @expose('/')
    def index_view(self, bot_id, city_id):
        return redirect('/admin/bots/%s/%s/goods' % (bot_id, city_id))


class MyLeadTextsView(RootView):
    create_template = 'lead_texts_create.html'

    @expose('/create', methods=('GET', 'POST'))
    def create_view(self):
        self._template_args.update(texts=defaults.l_texts.to_json())
        return super().create_view()


class LeadRequestsView(RootView):
    can_create = False
    can_edit = False
    column_filters = ['approved', 'user']
    column_list = ['approved', 'user', 'code', 'sum', 'date']
    list_template = 'lead_request_list.html'

    @expose('<lr_id>/approve', methods=['POST'])
    def approve(self, lr_id):
        lr = LeadRequest.objects(id=lr_id).first()
        if lr is None or lr.approved:
            return '', 404
        lr.approved = True
        lr.save()
        if not lr.user.balance:
            lr.user.balance = 0
        lr.user.balance += lr.sum
        lr.user.save()
        return {'approved': lr.approved}


class WithdrawRequestsView(RootView):
    can_create = False
    can_edit = False
    column_filters = ['done', 'user']
    column_list = ['done', 'user', 'sum']
    list_template = 'withdraw_request_list.html'

    @expose('<wr_id>/done', methods=['POST'])
    def set_done(self, wr_id):
        wr = WithdrawRequest.objects(id=wr_id).first()
        if wr is None or wr.done:
            return '', 404
        if not wr.user.balance or wr.user.balance < wr.sum:
            return {'error': 'LOW_BALANCE'}, 400
        wr.done = True
        wr.save()
        wr.user.balance -= wr.sum
        wr.user.save()
        return {'done': wr.done}


class OrdersView(RootView):
    can_create = False
    can_edit = False


class CreateDublicate(BotRootView):
    create_template = 'bot_dublicate.html'

    @expose('/', methods=['POST', 'GET'])
    def create_dublicate_page(self, bot_id):
        return super().create_view(bot_id)

    @expose('/<bot_2>', methods=['POST', 'GET'])
    def create_dub(self, bot_id, bot_2):
        try:
            telebot.TeleBot(bot_2).get_me()
        except Exception:
            return 'ERROR, go back'
        bot_2 = loads(BotProfile.objects(token=bot_2).first().to_json())['_id']['$oid']

        text = Texts.objects(bot_id=bot_id).first()

        if not (text is None):
            text_dict = loads(text.to_json())

            dub_text = {}

            for key in text_dict:
                if key != '_id':
                    dub_text.update({key: text_dict[key]})

            dub_text['bot_id'] = bot_2

            new_text = Texts(**dub_text)
            new_text.save()

        cities = City.objects(bot_id=bot_id)

        if cities is not None:
            for city in cities:
                if not (city is None):
                    city_dict = loads(city.to_json())

                    dub_city = {}

                    for key in city_dict:
                        if key != '_id':
                            dub_city.update({key: city_dict[key]})

                    dub_city['bot_id'] = bot_2

                    new_city = City(**dub_city)
                    new_city.save()
                    goods = Good.objects(city_id=city.id.binary.hex())

                    for good in goods:
                        if good is not None:
                            Good(name=good.name,
                                 city_id=new_city.id.binary.hex(),
                                 price=good.price,
                                 description=good.description,
                                 photo=good.photo,
                                 districts=good.districts).save()

        payment = Payment.objects(bot_id=bot_id).first()

        if not (payment is None):
            payment_dict = loads(payment.to_json())

            dub_payment = {}

            for key in payment_dict:
                if key != '_id':
                    dub_payment.update({key: payment_dict[key]})

            dub_payment['bot_id'] = bot_2

            new_payment = Payment(**dub_payment)
            new_payment.save()
        return str(bot_2)


class Wallet(RootView):
    @expose('/', methods=['POST', 'GET'])
    def create_wallet(self):
        if request.form:
            not_for_all = False
            wallet = request.form['wallet']
            for key in request.form:
                try:
                    if key != 'wallet':
                        bot_id = request.form[key]
                        bot = BotProfile.objects(id=bot_id).first()
                        bot.wallet = wallet
                        bot.save()
                except Exception:
                    not_for_all = True
                    flash('К боту ' + request.form[key] + ' не удалось привязать кошелек')
            if not not_for_all:
                flash('Кошелек успешно привязан')
        return self.render('wallet.html', bots=BotProfile.objects())

    def get_url(self, endpoint, **kwargs):
        bots = BotProfile.objects(active=True)
        for bot in bots:
            kwargs.update(bot_id=bot.id.binary.hex())
        return url_for(endpoint, **kwargs)


from defaults import *


class MyMsg(RootView):
    form_columns = ["greet_msg"]

    @expose('/', methods=['POST', 'GET'])
    def create_wallet(self, bot_id):
        if request.form:
            not_for_all = False
            wallet = request.form['greet_msg']
            for key in request.form:
                try:
                    if key != 'greet_msg':
                        bot_id = request.form[key]
                        text = Texts.objects(bot_id=bot_id)
                        if str(text) != "[]":
                            for i in text:
                                if str(i) != "None":
                                    i.greet_msg = wallet
                                    i.save()
                        else:
                            Texts(greet_msg = wallet, bot_id=bot_id,back_btn=BACKBTN, use_buttons_msg=USEBUTTONS,
                                  choose_good_msg=CHOOSEGOOD,choose_city_msg=CHOOSESITY,choose_district_msg=CHOOSEDISTRICT,
                                  choose_payment_msg=CHOOSEPAYMENT, done_btn=DONE, leads_btn=LEADS, new_order_msg=NEWORDER,
                                  selected_good_msg=SELECTED, selected_good_msg2=SELECTED2).save()


                except Exception as e:
                    print(e)
                    not_for_all = True
                    flash('К боту ' + request.form[key] + ' не удалось привязать greet msg')
            if not not_for_all:
                flash('Greet msg успешно привязано')

        return self.render('MyMsg.html', bot_id=bot_id, bots=BotProfile.objects())

    def get_url(self, endpoint, **kwargs):
        bots = BotProfile.objects(active=True)
        for bot in bots:
            kwargs.update(bot_id=bot.id.binary.hex())
        return url_for(endpoint, **kwargs)

admin = Admin(template_mode='bootstrap3', index_view=MyIndexView())

admin.add_view(MyUserView(User, name='Пользователи', endpoint='users'))
admin.add_view(MyUseridView(User, name='экспорт user id', endpoint='userid'))
admin.add_view(MyUsernameView(User, name='экспорт username', endpoint='username'))
admin.add_view(MyMailingView(Mailing, name='Рассылка', endpoint='mailing'))
admin.add_view(LeadRequestsView(LeadRequest, name='Лиды', endpoint='lead-requests'))
admin.add_view(WithdrawRequestsView(WithdrawRequest, name='Запросы на вывод', endpoint='withdraw-requests'))
admin.add_view(OrdersView(Order, name='Заказы', endpoint='orders'))
admin.add_view(MyLeadTextsView(LeadTexts, name='Тексты (лиды)', endpoint='lead-texts'))
admin.add_view(RootView(Administrator, name='Админы', endpoint='settings'))
admin.add_view(Wallet(BotProfile, name='Кошелек', endpoint='wallet'))
admin.add_view(MyMsg(Texts, name="Сообщение", endpoint="bots/<bot_id>/texts/edit/addmsg"))
admin.add_view(MyMsg(Texts, name="Сообщение", endpoint="bots/<bot_id>/texts/addmsg"))
admin.add_view(MyBotProfileView(BotProfile, name='Боты', endpoint='bots'))
admin.add_view(MyPaymentView(Payment, name='Варианты оплаты', endpoint='bots/<bot_id>/payments'))
admin.add_view(MyCityView(City, name='Города', endpoint='bots/<bot_id>'))
admin.add_view(CreateDublicate(BotProfile, name='Создать дубликат', endpoint='bots/<bot_id>/dublicate'))
admin.add_view(MyTextsView(Texts, name='Тексты', endpoint='bots/<bot_id>/texts'))
admin.add_view(MyCityOneView(City, endpoint='bots/<bot_id>/<city_id>'))
admin.add_view(MyGoodsView(Good, name='Продукты', endpoint='bots/<bot_id>/<city_id>/goods'))
admin.add_view(StorageAdminModel(StorageModel, name="Фаилы", endpoint='import'))
admin.add_view(MyDistrictView(District, name='Районы', endpoint='bots/<bot_id>/<city_id>/districts'))
