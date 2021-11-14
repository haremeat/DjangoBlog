from django.shortcuts import render

# Create your views here.
def landing(req):
    return render(
        req,
        'single_pages/landing.html'
    )


def about_me(req):
    return render(
        req,
        'single_pages/about_me.html'
    )