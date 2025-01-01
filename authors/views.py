from django.shortcuts import render, get_object_or_404
from .models import Author

# Create your views here.



def index(request):
    print("view is triggered")
    all_authors = Author.objects.all()
    return render(request, "base.html", {
      "all_authors": all_authors
    })


def author_details(request, slug):
     identified_author = get_object_or_404(Author, slug=slug)
     all_authors = Author.objects.all()
     return render(request, "authors/author.html", {
      "details": identified_author,
       "all_authors": all_authors
    })


