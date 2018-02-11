from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from accounts.models import UserProfile, ClassMember
from classes.forms import ApeClassRegistrationForm
from classes.models import ApeClass


@login_required
def register_for_class(request, ape_class_id):
    user = request.user
    ape_class = ApeClass.objects.get(id=ape_class_id)
    if request.method == 'GET':
        form = ApeClassRegistrationForm()
        return render(request, 'classes/ape_class_registration.html', {'ape_class': ape_class, 'form': form})

    if request.method == 'POST':
        form = ApeClassRegistrationForm(data=request.POST)
        if form.is_valid():
            has_paid = form.cleaned_data['pay_now']
            ClassMember.objects.create(ape_class=ape_class, student=user.profile, has_paid=has_paid)
            messages.add_message(request, messages.SUCCESS, 
                                 'Your spot in {} has been reserved.'.format(ape_class.name))

    return redirect(reverse('ape_class_wrapper', kwargs={'ape_class_id': ape_class.id}))
