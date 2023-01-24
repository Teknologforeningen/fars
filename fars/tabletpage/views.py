from django.views import View
from django.shortcuts import render, get_object_or_404, redirect, reverse
from django.utils import timezone
from booking.models import *


class TabletView(View):
    template = 'tablet.html'
    context = {}

    def dispatch(self, request, bookable):
        bookable_obj = get_object_or_404(Bookable, id_str=bookable)
        if not bookable_obj.public and not request.user.is_authenticated:
            return redirect('{}?next={}'.format(reverse('login'), request.path_info))
        self.context['bookable'] = bookable_obj
        self.context['errors'] = 0
        return super().dispatch(request, bookable)

    def get(self, request, bookable):
        now = timezone.now()
        booking = Booking()
        booking.bookable = self.context['bookable']
        # self.context['bookform'] = BookingForm(instance=booking)
        return render(request, self.template, context=self.context)


    def post(self, request, bookable):
        username = request.POST.get('username')
        pw = request.POST.get('password')
        user = authenticate(username=username, password=pw)
        postdata = request.POST.copy()
        try:
            postdata['user'] = user.id
        except AttributeError:
            postdata['user'] = -1
            self.context['errors'] = 1
            self.context['credential_error'] = 1
        form = BookingForm(postdata, instance=Booking())
        if form.is_valid():
            form.save()
            return redirect('tablet', bookable=bookable)
        self.context['errors'] = 1
        status = 400

        self.context['bookform'] = form
        return render(request, self.template, context=self.context, status=status)
