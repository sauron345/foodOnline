import datetime
from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect

from accounts.models import UserProfile
from marketplace.context_processors import get_cart_counter, get_cart_amounts
from marketplace.models import Cart
from menu.models import Category, FoodItem
from orders.forms import OrderForm
from vendor.models import Vendor, OpeningHour
from django.db.models import Prefetch, Q
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.measure import D  # ``D`` is a shortcut for ``Distance``
from django.contrib.gis.db.models.functions import Distance


def marketplace(request):
    vendors = Vendor.objects.filter(is_approved=True, user__is_active=True)
    vendor_count = vendors.count()

    context = {
        'vendors': vendors,
        'vendor_count': vendor_count,
    }
    return render(request, 'marketplace/listings.html', context)


def vendor_detail(request, vendor_slug):
    vendor = get_object_or_404(Vendor, vendor_slug=vendor_slug)
    categories = Category.objects.filter(vendor=vendor).prefetch_related(
        Prefetch(
            'fooditems',
            queryset=FoodItem.objects.filter(is_available=True)
        )
    )

    # will return today data
    day = date.today()
    # will return week day in number
    today_day = day.isoweekday()

    opening_hours = OpeningHour.objects.filter(vendor=vendor).order_by('day', '-from_hour')

    current_opening_hours = OpeningHour.objects.filter(vendor=vendor, day=today_day)

    if request.user.is_authenticated:
        cart_items = Cart.objects.filter(user=request.user)
    else:
        cart_items = None

    context = {
        'vendor': vendor,
        'categories': categories,
        'cart_items': cart_items,
        'current_opening_hours': current_opening_hours,
        'opening_hours': opening_hours,
    }
    return render(request, 'marketplace/vendor_detail.html', context)


def add_to_cart(request, food_id):
    if request.user.is_authenticated:
        # previously: request.is_ajax()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(fooditem=fooditem, user=request.user)
                    # Increase the cart quantity
                    chkCart.quantity += 1
                    chkCart.save()
                    return JsonResponse({'status': 'Success', 'message': 'Increased the cart quantity',
                                         'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity,
                                         'cart_amounts': get_cart_amounts(request)})
                except:
                    chkCart = Cart.objects.create(fooditem=fooditem, user=request.user, quantity=1)
                    return JsonResponse({'status': 'Success', 'message': 'Added food to the cart',
                                         'cart_counter': get_cart_counter(request), 'qty': chkCart.quantity,
                                         'cart_amounts': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


def decrease_cart(request, food_id):
    if request.user.is_authenticated:
        # previously: request.is_ajax()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            # Check if the food item exists
            try:
                fooditem = FoodItem.objects.get(id=food_id)
                # Check if the user has already added that food to the cart
                try:
                    chkCart = Cart.objects.get(fooditem=fooditem, user=request.user)
                    if chkCart.quantity > 1:
                        # Increase the cart quantity
                        chkCart.quantity -= 1
                        chkCart.save()
                    else:
                        chkCart.delete()
                        chkCart.quantity = 0                           # funkcja ta zwroci slownik {cart_count:liczba}
                    return JsonResponse({'status': 'Success', 'cart_counter': get_cart_counter(request),
                                         'qty': chkCart.quantity, 'cart_amounts': get_cart_amounts(request)})
                except:
                    return JsonResponse({'status': 'Failed', 'message': 'You do not have this item in your cart'})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request'})
    else:
        return JsonResponse({'status': 'login_required', 'message': 'Please login to continue'})


@login_required(login_url='login')
def cart(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('created_at')
    context = {
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/cart.html', context)


def delete_cart(request, cart_id):
    if request.user.is_authenticated:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            try:
                cart_item = Cart.objects.get(user=request.user, id=cart_id)
                if cart_item:
                    cart_item.delete()
                    return JsonResponse({'status': 'Success', 'message': 'Cart item has been deleted!',
                                         'cart_counter': get_cart_counter(request),
                                         'cart_amounts': get_cart_amounts(request)})
            except:
                return JsonResponse({'status': 'Failed', 'message': 'This food does not exist!'})
        else:
            return JsonResponse({'status': 'Failed', 'message': 'Invalid request'})


def search(request):
    if 'address' not in request.GET:
        return redirect('marketplace')
    else:
        latitude = request.GET['lat']
        longitude = request.GET['lng']
        address = request.GET['address']
        radius = request.GET['radius']
        keyword = request.GET['keyword']
                                                                                                                # list of ids of food items
        fetch_vendors_by_fooditems = FoodItem.objects.filter(food_title__icontains=keyword, is_available=True).values_list('vendor', flat=True)

        if latitude and longitude and radius:
            pnt = GEOSGeometry('POINT(%s %s)' % (longitude, latitude))

        vendors = Vendor.objects.filter(Q(id__in=fetch_vendors_by_fooditems) | Q(vendor_name__icontains=keyword, is_approved=True, user__is_active=True),
                                        user_profile__location__distance_lte=(pnt, D(km=radius))).\
            annotate(distance=Distance('user_profile__location', pnt)).order_by('distance')
        vendor_count = vendors.count()

        for v in vendors:
            v.kms = round(v.distance.km, 1)

        context = {
            'vendors': vendors,
            'vendor_count': vendor_count,
            'souce_locaction': address,
        }

        return render(request, 'marketplace/listings.html', context)


@login_required(login_url='login')
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user).order_by('-created_at')
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('marketplace')

    user_profile = UserProfile.objects.get(user=request.user)

    default_values = {
        'first_name': 'Sebastian',
        'last_name': request.user.last_name,
        'phone': request.user.phone_number,
        'email': request.user.email,
        'address': user_profile.address,
        'country': user_profile.country,
        'state': user_profile.state,
        'city': user_profile.city,
        'pin_code': user_profile.pin_code,
    }

    form = OrderForm(initial=default_values)

    context = {
        'form': form,
        'cart_items': cart_items,
    }
    return render(request, 'marketplace/checkout.html', context)
