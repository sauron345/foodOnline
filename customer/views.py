import json

from django.contrib import messages
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from accounts.forms import UserProfileForm, UserInfoForm
from accounts.models import UserProfile
from accounts.views import check_role_customer
from orders.models import Order, OrderedFood


@login_required(login_url='login')
@user_passes_test(check_role_customer)
def cprofile(request):
    profile = get_object_or_404(UserProfile, user=request.user)
    if request.method == 'POST':
        profile_form = UserProfileForm(instance=profile, files=request.FILES, data=request.POST)
        user_form = UserInfoForm(instance=request.user, data=request.POST)
        if profile_form.is_valid() and user_form.is_valid():
            profile_form.save()
            user_form.save()
            messages.success(request, 'Profile updated')
            return redirect('cprofile')
        else:
            print(profile_form.errors)
            print(user_form.errors)
    else:
        profile_form = UserProfileForm(instance=profile)
        user_form = UserInfoForm(instance=request.user)

    context = {
        'profile_form': profile_form,
        'user_form': user_form,
        'profile': profile
    }
    return render(request, 'customer/cprofile.html', context)


def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')

    context = {
        'orders': orders,
    }

    return render(request, 'orders/my_orders.html', context)


def order_detail(request, order_number):
    try:
        order = Order.objects.get(user=request.user, order_number=order_number)
        ordered_foods = OrderedFood.objects.filter(order=order)

        subtotal = 0
        for item in ordered_foods:
            subtotal += (item.price * item.quantity)

        tax_data = json.loads(order.tax_data)

        context = {
            'order': order,
            'ordered_foods': ordered_foods,
            'subtotal': subtotal,
            'tax_data': tax_data,
        }

        return render(request, 'orders/order_detail.html', context)

    except:
        return redirect('customer')




