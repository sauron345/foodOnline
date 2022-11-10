from django.shortcuts import render, redirect
from django.http import HttpResponse
from .forms import UserForm
from .models import User
from django.contrib import messages

# Create your views here.
def registerUser(request):
    # return HttpResponse("This is user register form")
    if request.method == 'POST':
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
            user.save()
            messages.success(request, 'Your account has been registered successfully!')
            return redirect('registerUser')
    else:
        form = UserForm()

    context = {'form': form}
    return render(request, 'accounts/registerUser.html', context)
