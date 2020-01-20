from flask_mongoengine import MongoEngine
from mongoengine import PULL, NULLIFY

db = MongoEngine()



class Sale(db.Document):
    meta = {'strict': False}
    salemain = db.BooleanField()

    def __unicode__(self):
        return self.salemain



class BotProfile(db.Document):
    meta = {'strict': False}
    name = db.StringField(required=True)
    token = db.StringField(required=True)
    stat = db.StringField(required=False)
    t_id = db.StringField(required=True)
    photo_file_id = db.StringField()
    active = db.BooleanField(default=False)
    wallet = db.StringField(required=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

class BotPhoto(db.Document):
    t_bot_id = db.StringField(required=True)
    file_id = db.StringField(required=True)
    data = db.BinaryField()


class District(db.Document):
    city_id = db.StringField(required=True)
    meta = {'strict': False}
    name = db.StringField()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)

class City(db.Document):
    meta = {'strict': False}

    name = db.StringField()
    bot_id = db.StringField(required=True)

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)


class Good(db.Document):
    meta = {'strict': False}
    name = db.StringField(required=True)
    city_id = db.StringField(required=True)
    description = db.StringField()
    price = db.StringField(required=True)
    sale = db.IntField(default=0)
    saleSecond = db.IntField(default=0)
    PriceWithSale = db.IntField(default=0)
    SecondSavePrice = db.IntField(default=0)
    # photo = db.ImageField()
    districts = db.ListField(db.ReferenceField(District, reverse_delete_rule=PULL))

    def __unicode__(self):
        return self.name

    def __str__(self):
        return str(self.name)




class Payment(db.Document):
    meta = {'strict': False}

    bot_id = db.StringField(required=True)
    payment_name = db.StringField()
    answer_text = db.StringField()
    answer_on_payment = db.StringField()

    def __unicode__(self):
        return self.payment_name

    def __str__(self):
        return str(self.payment_name)

class User(db.Document):
    bot = db.ReferenceField(BotProfile, reverse_delete_rule=NULLIFY)
    user_id = db.IntField(required=True)

    username = db.StringField()
    first_name = db.StringField()
    last_name = db.StringField()

    state = db.StringField(max_length=50)
    is_admin = db.BooleanField(default=False)

    city = db.ReferenceField(City, reverse_delete_rule=NULLIFY)
    good = db.ReferenceField(Good, reverse_delete_rule=NULLIFY)
    district = db.ReferenceField(District, reverse_delete_rule=NULLIFY)
    payment = db.ReferenceField(Payment, reverse_delete_rule=NULLIFY)
    code = db.StringField()

    clicked_goods = db.ListField(db.ReferenceField(Good, reverse_delete_rule=PULL))
    ordered_goods = db.ListField(db.ReferenceField(Good, reverse_delete_rule=PULL))

    balance = db.IntField(default=0)
    tax = db.IntField()

    wallet = db.StringField()

    datetime = db.DateTimeField()

    meta = {'strict': False}

    def __unicode__(self):
        return f'(Bot: {self.bot.name}) (ID: {self.user_id}) @{self.username} {self.first_name}'

    def __repr__(self):
        return f'User ({self.user_id} {self.username} {self.first_name})'


class Order(db.Document):
    user = db.ReferenceField(User, reverse_delete_rule=NULLIFY)
    city_name = db.StringField()
    district_name = db.StringField()
    good_name = db.StringField()
    payment_name = db.StringField()
    code = db.StringField()

    meta = {'strict': False}


class LeadRequest(db.Document):
    user = db.ReferenceField(User, reverse_delete_rule=NULLIFY)
    sum = db.IntField()
    code = db.StringField()
    approved = db.BooleanField(default=False)
    date = db.DateTimeField()

    meta = {'strict': False}


class WithdrawRequest(db.Document):
    user = db.ReferenceField(User, reverse_delete_rule=NULLIFY)
    sum = db.IntField()
    done = db.BooleanField(default=False)

    meta = {'strict': False}


class Administrator(db.Document):
    username = db.StringField()
    password = db.StringField()
    main_admin = db.BooleanField(default=False)

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    def __unicode__(self):
        return self.username


class Mailing(db.Document):
    text = db.StringField()
    image = db.ImageField()
    file = db.FileField()
    url_text = db.StringField()
    url = db.StringField()
    markup = db.BooleanField(default=False)

    meta = {'strict': False}

    def __repr__(self):
        return f'Mailing ({self.text} {self.url_text} {self.url})'

class StorageModel(db.Document):
    meta = {'strict': False}

    name = db.StringField()
    type = db.StringField()


class Texts(db.Document):
    meta = {'strict': False}

    bot_id = db.StringField(required=True)
    greet_msg = db.StringField()
    back_btn = db.StringField()
    use_buttons_msg = db.StringField()
    choose_good_msg = db.StringField()
    choose_city_msg = db.StringField()
    choose_district_msg = db.StringField()
    choose_payment_msg = db.StringField()
    done_btn = db.StringField()
    leads_btn = db.StringField()

    new_order_msg = db.StringField()
    selected_good_msg = db.StringField()
    selected_good_msg2 = db.StringField()


class LeadTexts(db.Document):
    meta = {'strict': False}

    wallet_btn = db.StringField()
    wallet_reply = db.StringField()

    withdraw_btn = db.StringField()
    withdraw_reply = db.StringField()
    withdraw_incorrect_sum = db.StringField()
    withdraw_low_balance = db.StringField()

    how_to_btn = db.StringField()
    how_to_reply = db.StringField()
    how_to_reply_image = db.ImageField()
    how_to_reply_file = db.FileField()

    request_btn = db.StringField()
    request_reply = db.StringField()
    request_incorrect_sum = db.StringField()

    summary_msg = db.StringField()
