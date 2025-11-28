from django.shortcuts import render
from pillars import generate_character


def index(request):
    """Main page with generate button."""
    character = None
    years = 0  # Default value

    if request.method == 'POST':
        years_input = request.POST.get('years', '0')
        try:
            years = int(years_input)
        except ValueError:
            years = 0
        character = generate_character(years=years)

    return render(request, 'generator/index.html', {
        'character': character,
        'years': years,
    })
