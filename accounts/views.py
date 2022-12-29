from django.shortcuts import render, redirect

from orders.models import Order
from vendor.models import Vendor
from .forms import UserForm
from .models import User, UserProfile
from django.contrib import messages
from vendor.forms import VendorForm
from django.contrib import auth
from .utils import detectUser, send_verification_email
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.template.defaultfilters import slugify
from datetime import datetime


# Restrict the vendor from accessing the customer page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied


# Restrict the customer from accessing the customer page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied


def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect('myAccount')
    elif request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            # FIRST WAY
            # user = form.save(commit=False)
            # user.role = User.CUSTOMER
            # password = form.cleaned_data['password']
            # user.set_password(password)
            # user.save()

            # SECOND WAY
            cd = form.cleaned_data
            first_name = cd['first_name']
            last_name = cd['last_name']
            username = cd['username']
            email = cd['email']
            password = cd['password']
            user = User.objects.create_user(first_name=first_name, last_name=last_name,
                                            username=username, email=email, password=password)
            user.role = User.CUSTOMER
            user.save()

            # Send verification email
            mail_subject = 'Please activate your account'
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(request, 'Your account has been registered successfully!')
            return redirect('registerUser')
    else:
        form = UserForm()

    context = {'form': form}
    return render(request, 'accounts/registerUser.html', context)


def registerVendor(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect('myAccount')
    elif request.method == 'POST':
        # store the data and create the user
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST, request.FILES)
        if form.is_valid() and v_form.is_valid():
            cd = form.cleaned_data
            first_name = cd['first_name']
            last_name = cd['last_name']
            username = cd['username']
            email = cd['email']
            password = cd['password']

            user = User.objects.create_user(first_name=first_name, last_name=last_name,
                                            username=username, email=email, password=password)
            user.role = User.VENDOR
            user.save()

            vendor = v_form.save(commit=False)
            vendor.user = user

            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile

            vendor_name = v_form.cleaned_data['vendor_name']
            vendor.vendor_slug = slugify(vendor_name) + '-' + str(user.id)

            vendor.save()

            # Send verification email
            mail_subject = 'Please activate your account'
            email_template = 'accounts/emails/account_verification_email.html'
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(request, 'Your account has been registered successfully! Please wait for the approval. ')
            return redirect('registerVendor')
        else:
            print('invalid form')
            print(form.errors)
    else:
        form = UserForm()
        v_form = VendorForm()

    context = {
        'form': form,
        'v_form': v_form,
    }
    return render(request, 'accounts/registerVendor.html', context)


def activate(request, uidb64, token):
    # Activate the user by setting the is_active status to True
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    # for example: token is invalid
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
                            # check created token to make sure that is the token of this user
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulation! Your account is activated.')
        return redirect('myAccount')
    else:
        messages.error(request, "Invalid activation link")
        return redirect('myAccount')


def login(request):
    if request.user.is_authenticated:
        messages.warning(request, "You are already logged in!")
        return redirect('myAccount')
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            auth.login(request, user)
            messages.success(request, "You are now logged in")
            return redirect('myAccount')
        else:
            # tł. Nieprawidłowe dane logowania
            messages.error(request, "Invalid login credentials")
            return redirect('login')

    return render(request, 'accounts/login.html')


def logout(request):
    auth.logout(request)
    messages.info(request, "You are logged out")
    return redirect('login')


@login_required(login_url='login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)


@login_required(login_url='login')
@user_passes_test(check_role_customer)
def custDashboard(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True)
    recent_orders = orders[:5]
    context = {
        'orders': orders,
        'orders_counter': orders.count(),
        'recent_orders': recent_orders,
    }
    return render(request, "accounts/custDashboard.html", context)


@login_required(login_url='login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    vendor = Vendor.objects.get(user=request.user)
    orders = Order.objects.filter(vendors__in=[vendor.id], is_ordered=True).order_by('-created_at')
    orders_counter = orders.count()
    recent_orders = orders[:5]

    current_month_revenue = 0
    current_month = datetime.today().month
    current_month_orders = orders.filter(created_at__month=current_month)

    for i in current_month_orders:
        current_month_revenue += i.get_total_by_vendor()['grand_total']

    total_revenue = 0

    for order in orders:
        total_revenue += order.get_total_by_vendor()['grand_total']

    context = {
        'orders': orders,
        'orders_counter': orders_counter,
        'recent_orders': recent_orders,
        'total_revenue': total_revenue,
        'current_month_revenue': current_month_revenue,
    }

    return render(request, "accounts/vendorDashboard.html", context)


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)

            # send reset password email
            mail_subject = 'Reset Your Password'
            email_template = 'accounts/emails/reset_password_email.html'
            send_verification_email(request, user, mail_subject, email_template)

            messages.success(request, 'Password reset link has been sent to your email address')
            return redirect('login')
        else:
            messages.error(request, 'Account does not exist')
            return redirect('forgot_password')

    return render(request, 'accounts/forgot_password.html')


def reset_password_validate(request, uidb64, token):
    # validate the user by decoding the token and user pk
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except(ValueError, TypeError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request, 'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request, 'This link has been expired!')
        return redirect('myAccount')


def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            pk = request.session.get('uid')
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request, 'Password reset successful')
            return redirect('login')
        else:
            messages.error(request, 'Password do not match')
            return redirect('reset_password')

    return render(request, 'accounts/reset_password.html')
