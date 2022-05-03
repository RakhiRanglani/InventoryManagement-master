import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from django.views.decorators.csrf import csrf_exempt
from fbprophet import Prophet
import datetime
import numpy as np
import csv
import pandas as pd
from .models import Food , Profile
import seaborn as sns
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, PasswordResetView, PasswordChangeView
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.views import View
from django.contrib.auth.decorators import login_required
from .forms import RegisterForm, LoginForm, UpdateUserForm, UpdateProfileForm

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
    template_name = 'index.html'
    all_entries = Food.objects.all()  # get all foods
    return render(request, 'index.html', {'food_list': list(all_entries), 'food_pickup_info': food_pickup_info})



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


# For Login Details

class RegisterView(View):
    form_class = RegisterForm
    initial = {'key': 'value'}
    template_name = 'users/register.html'

    def dispatch(self, request, *args, **kwargs):
        # will redirect to the home page if a user tries to access the register page while logged in
        if request.user.is_authenticated:
            return redirect(to='/')

        # else process dispatch as it otherwise normally would
        return super(RegisterView, self).dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        form = self.form_class(initial=self.initial)
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)

        if form.is_valid():
            form.save()

            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}')

            return redirect(to='login')

        return render(request, self.template_name, {'form': form})


# Class based view that extends from the built in login view to add a remember me functionality
class CustomLoginView(LoginView):
    form_class = LoginForm

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')

        if not remember_me:
            # set session expiry to 0 seconds. So it will automatically close the session after the browser is closed.
            self.request.session.set_expiry(0)

            # Set session as modified to force data updates/cookie to be saved.
            self.request.session.modified = True

        # else browser session will be as long as the session cookie time "SESSION_COOKIE_AGE" defined in settings.py
        return super(CustomLoginView, self).form_valid(form)


class ResetPasswordView(SuccessMessageMixin, PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject'
    success_message = "We've emailed you instructions for setting your password, " \
                      "if an account exists with the email you entered. You should receive them shortly." \
                      " If you don't receive an email, " \
                      "please make sure you've entered the address you registered with, and check your spam folder."
    success_url = reverse_lazy('users-home')


class ChangePasswordView(SuccessMessageMixin, PasswordChangeView):
    template_name = 'users/change_password.html'
    success_message = "Successfully Changed Your Password"
    success_url = reverse_lazy('users-home')


@login_required
def profile(request):
    Profile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        user_form = UpdateUserForm(request.POST, instance=request.user)
        profile_form = UpdateProfileForm(request.POST, request.FILES, instance=request.user.profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, 'Your profile is updated successfully')
            return redirect(to='users-profile')
    else:
        user_form = UpdateUserForm(instance=request.user)
        profile_form = UpdateProfileForm(instance=request.user.profile)

    return render(request, 'users/profile.html', {'user_form': user_form, 'profile_form': profile_form})

