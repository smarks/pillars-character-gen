from django.shortcuts import render
from pillars import generate_character


def index(request):
    """Main page with generate button."""
    character = None
    if request.method == 'POST':
        character = generate_character()
    return render(request, 'generator/index.html', {'character': character})
