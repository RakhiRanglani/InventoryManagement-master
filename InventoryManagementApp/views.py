import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from fbprophet import Prophet
import datetime
import numpy as np
import csv
import pandas as pd
from .models import Food
from django.contrib import messages
from django.shortcuts import render, redirect
import seaborn as sns
from django.contrib.auth.models import User, auth

sns.set()  # matplotlib style


# function to retrain the model based on the new data
# returns model object
def update_csv(csv_path, value):
    with open(csv_path, 'a') as csvfile:
        spamwriter = csv.writer(csvfile)
        date = datetime.date.today() - datetime.timedelta(weeks=4)
        date = date.strftime('%m/%d/%Y')
        temp = date
        spamwriter.writerow([])
        spamwriter.writerow([temp, value])


def retrain(csv_path):
    df = pd.read_csv(csv_path)
    df.head()
    m = Prophet()
    m.fit(df)
    return m


def find_adjusted_food_order(demand_csv, sell_csv, month_after):
    # create models for both inventory and wastage
    date = datetime.date.today() + pd.DateOffset(months=month_after)
    inventory_model = retrain(demand_csv)
    waste_model = retrain(sell_csv)
    inventory = predict_date(date, inventory_model, month_after)
    waste = predict_date(date, waste_model, month_after)
    # return adjusted amount for needed date
    return (inventory - waste, inventory, waste)


def predict_date(date, model, period):
    # make dataframe
    # current date - last date in training + period
    period = int(((pd.to_datetime("today") - list(model.history['ds'])[-1]) / np.timedelta64(1, 'M'))) + period
    # period = pd.to_datetime("today") - list(model.history['ds'])[-1] + pd.offsets.MonthOffset(period)
    future = model.make_future_dataframe(periods=90 * period)
    # add to tail
    future.tail()
    # make prediction
    forecast = model.predict(future)
    forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']].tail()
    # change to standard times
    forecast['ds'] = pd.to_datetime(forecast['ds'])
    date_formatted = pd.Timestamp(date)
    list_index = list(forecast['ds']).index(date_formatted)
    return list(forecast['yhat_lower'])[list_index]


# Create your views here.
@csrf_exempt
def homepage(request):
    food_pickup_info = ''
    if (request.method == 'POST'):
        # if the button clicked on was food x, delete it and record info for user
        for food in list(Food.objects.all()):
            if (food.key in request.POST):
                chosen_food = food
                print(chosen_food.name)
                food_pickup_info = "Get your " + chosen_food.name + " at " + chosen_food.address + \
                                   " before " + chosen_food.expiration + ", contact " + chosen_food.phone
                chosen_food.delete()
    template_name = 'homepage.html'
    all_entries = Food.objects.all()  # get all foods
    return render(request, 'homepage.html', {'food_list': list(all_entries), 'food_pickup_info': food_pickup_info})


def save_wasted():
    df = pd.read_csv('./InventoryAdjustmentPrediction/monthly_tomatoes_future_prediction.csv')
    x = list(df['ds'])
    dates = []
    y = list(df['y'])
    for date in x:
        s = date.rstrip()
        dates.append(datetime.datetime.strptime(s, "%m/%d/%Y").date())
        # date = s.strftime("%Y%m%d")
        # date = datetime(year=int(s[0:4]), month=int(s[0:2]), day=int(s[6:8]))
    x = matplotlib.dates.date2num(dates)
    # print(x, y)
    plt.plot_date(x, y, 'k', color='mediumvioletred')
    plt.xlabel('Dates')
    plt.ylabel('Apples wasted')
    plt.title('Apples wasted across time')
    plt.savefig('InventoryManagementApp/static/images/wasted.jpg')


def save_ordered():
    df = pd.read_csv('./InventoryAdjustmentPrediction/monthly_tomatoes.csv')
    x = list(df['ds'])
    dates = []
    y = list(df['y'])
    for date in x:
        s = date.rstrip()
        dates.append(datetime.datetime.strptime(s, "%m/%d/%Y").date())
        # date = s.strftime("%Y%m%d")
        # date = datetime(year=int(s[0:4]), month=int(s[0:2]), day=int(s[6:8]))
    x = matplotlib.dates.date2num(dates)
    plt.plot_date(x, y, 'k', color='mediumvioletred')
    plt.xlabel('Dates')
    plt.ylabel('Apples ordered')
    plt.title('Apples ordered across time')
    plt.savefig('InventoryManagementApp/static/images/ordered.jpg')


# the csrf cookie crashes any posting of content to server so disable
@csrf_exempt
def upload(request):
    template_name = 'upload.html'
    # if an image is uploaded
    if (request.method == 'POST' and request.POST['name'] is not None):
        food = Food(name=request.POST['name'], amount=request.POST['amount'],
                    expiration=request.POST['expiration'], address=request.POST['address'], phone=request.POST['phone'])
        food.key = food.address + food.name + food.amount
        food.save()  # save in database
        return render(request, 'upload.html', {'result': 'Uploaded food!'})
    else:
        return render(request, 'upload.html', {'result': ''})


@csrf_exempt
def feed(request):
    return render(request, 'feed.html', {'feed_image': 'output.jpg'})


@csrf_exempt
def index(request):
    return render(request, 'index.html')


@csrf_exempt
def about(request):
    return render(request, 'about.html')


@csrf_exempt
def blog(request):
    return render(request, 'blog.html')


@csrf_exempt
def testimonial(request):
    return render(request, 'testimonial.html')


@csrf_exempt
def register(request):
    if request.method == 'POST':
        first_name = request.POST['first_name']
        last_name = request.POST['last_name']
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username is already taken')
                return redirect(register)
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email is already taken')
                return redirect(register)
            else:
                user = User.objects.create_user(username=username, password=password,
                                                email=email, first_name=first_name, last_name=last_name)
                user.save()

                return redirect('login')


        else:
            messages.info(request, 'Both passwords are not matching')
            return redirect(register)


    else:
        return render(request, 'register.html')

@csrf_exempt
def logout(request):
    auth.logout(request)
    return redirect('index')


@csrf_exempt
def login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)

        if user is not None:
            auth.login(request, user)
            return redirect('index.html')
        else:
            messages.info(request, 'Invalid Username or Password')
            return redirect('login.html')



    else:
        return render(request, 'login.html')


# the csrf cookie crashes any posting of content to server so disable
@csrf_exempt
def statistic(request):
    template_name = 'statistic.html'
    plt.clf()
    save_wasted()
    plt.clf()
    save_ordered()
    plt.clf()
    # if an image is uploaded
    if (request.method == 'POST' and request.POST['order'] is not None):
        order = int(request.POST['order'])
        update_csv('InventoryAdjustmentPrediction/monthly_tomatoes_future_prediction.csv', order)
        result, inventory, waste = find_adjusted_food_order('InventoryAdjustmentPrediction/monthly_tomatoes.csv',
                                                            'InventoryAdjustmentPrediction/monthly_tomatoes_future_prediction.csv',
                                                            1)  # predict one month ahead
        result = str(round(result)) + ' apples'
        inventory = 'Predicted demand for next month: ' + str(round(inventory)) + ' apples'
        waste = "Estimated predicted waste for next month (before adjustment): " + str(round(waste)) + ' apples'
        return render(request, 'statistic.html',
                      {'result': result, 'estimation': "Estimated optimal order of apples in next month: ",
                       'inventory': inventory, 'waste': waste})
    else:
        return render(request, 'statistic.html', {'result': '',
                                                  'estimation': 'Input your order of apples this month and get the estimate for next month\'s optimal order: '})
