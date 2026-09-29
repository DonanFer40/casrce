from django.shortcuts import render

def panel_usuario(request):
    return render(request, 'Logueado/dashboard.html')