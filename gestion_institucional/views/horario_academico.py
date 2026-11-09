from django.shortcuts import render


def reg_horario(request):
    return render(request, "Roles/Coordinador_PNF/horario/registrar_horario.html")