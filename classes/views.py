from django.shortcuts import render, get_object_or_404
from django.urls import reverse

from classes.models import ApeClass, ApeClassSession


def class_list(request):
    classes = ApeClass.objects.filter(active=True)
    return render(request, 'classes/class_list.html', {'classes': classes})


def class_detail(request, class_id):
    ape_class = get_object_or_404(ApeClass, pk=class_id)

    return render(request, 'classes/class_detail.html', {
        'uplink': {'url': reverse('class_list'), 'label': "Classes"},
        'class': ape_class,
    })

def session_detail(request, class_id, session_id):
    ape_class = get_object_or_404(ApeClass, pk=class_id)
    session = get_object_or_404(ApeClassSession, pk=session_id)

    return render(request, 'classes/session_detail.html', {
        'uplink': {'url': reverse('class_detail', kwargs={'class_id': class_id}), 'label': "{}".format(ape_class)},
        'class': ape_class,
        'session': session
    })
