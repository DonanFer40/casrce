from django import forms
from .models import Usuario, Contacto, Pnf, Nucleos, PNFNucleo, Cuenta
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
import re
from .validators import validar_contrasenia_segura


class ConfiguracionUsuarioForm(forms.ModelForm):
    DISCAPACIDAD_CHOICES = [
        ("", "Seleccione una opción"),
        ("N/A", "No aplica"),
    ]
    telefono_personal = forms.CharField(
        label="Teléfono principal",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    telefono_suplete = forms.CharField(
        label="Teléfono secundario",
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={"autocomplete": "tel"}),
    )
    condicion_residencia = forms.CharField(
        label="Condición de residencia",
        max_length=100,
        required=False,
    )
    municipio = forms.CharField(label="Municipio", max_length=100, required=False)
    parroquia = forms.CharField(label="Parroquia", max_length=100, required=False)
    direccion_residencia = forms.CharField(
        label="Dirección de residencia",
        max_length=100,
        required=False,
        widget=forms.Textarea(attrs={"rows": 3}),
    )
    carnet_discapacidad = forms.CharField(
        label="Carnet de discapacidad",
        max_length=50,
        required=False,
    )
    registro_medico = forms.CharField(
        label="N.º de registro médico",
        max_length=5,
        required=False,
    )
    tipos_discapacidad = forms.ChoiceField(
        label="Tipo de discapacidad",
        required=False,
        choices=DISCAPACIDAD_CHOICES + [
            ("Visual", "Visual"),
            ("Auditiva", "Auditiva"),
            ("Lenguaje", "Lenguaje"),
            ("Lengauje", "Lenguaje (registro anterior)"),
            ("Intelectual", "Intelectual"),
            ("Autista", "Autista"),
            ("Fisica y Motora", "Física y motora"),
            ("Otro", "Otro"),
        ],
    )
    grado_discapacidad = forms.ChoiceField(
        label="Grado de discapacidad",
        required=False,
        choices=DISCAPACIDAD_CHOICES + [
            ("Leve", "Leve"),
            ("Moderada", "Moderada"),
            ("Grave", "Grave"),
        ],
    )
    causa_discapacidad = forms.ChoiceField(
        label="Causa de discapacidad",
        required=False,
        choices=DISCAPACIDAD_CHOICES + [
            ("Congenita", "Congénita"),
            ("Adquirida", "Adquirida"),
        ],
    )
    eliminar_foto = forms.BooleanField(
        label="Quitar foto actual",
        required=False,
    )

    class Meta:
        model = Usuario
        fields = (
            "nombres",
            "apellidos",
            "genero",
            "estado_civil",
            "foto_perfil",
        )
        widgets = {
            "nombres": forms.TextInput(attrs={"autocomplete": "given-name"}),
            "apellidos": forms.TextInput(attrs={"autocomplete": "family-name"}),
            "genero": forms.TextInput(),
            "estado_civil": forms.TextInput(),
            "foto_perfil": forms.FileInput(
                attrs={"accept": "image/jpeg,image/png,image/webp"}
            ),
        }
        labels = {
            "nombres": "Nombres",
            "apellidos": "Apellidos",
            "genero": "Género",
            "estado_civil": "Estado civil",
            "foto_perfil": "Foto de perfil",
        }

    def clean_foto_perfil(self):
        foto = self.cleaned_data.get("foto_perfil")
        if foto and foto.size > 5 * 1024 * 1024:
            raise ValidationError("La foto no debe superar los 5 MB.")
        return foto

    def clean(self):
        cleaned_data = super().clean()
        campos_residencia = (
            "condicion_residencia",
            "municipio",
            "parroquia",
            "direccion_residencia",
        )
        if any(cleaned_data.get(campo) for campo in campos_residencia):
            for campo in campos_residencia:
                if not cleaned_data.get(campo):
                    self.add_error(campo, "Completa todos los datos de residencia.")
        campos_discapacidad = (
            "carnet_discapacidad",
            "registro_medico",
            "tipos_discapacidad",
            "grado_discapacidad",
            "causa_discapacidad",
        )
        if any(cleaned_data.get(campo) for campo in campos_discapacidad):
            for campo in campos_discapacidad:
                if not cleaned_data.get(campo):
                    self.add_error(
                        campo,
                        "Completa todos los datos de discapacidad.",
                    )
        return cleaned_data

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("eliminar_foto"):
            usuario.foto_perfil = None
        if commit:
            usuario.save()
        return usuario

class UsuarioAdminForm(forms.ModelForm):
    GENERO_CHOICES = [
        ('', 'Seleccione el Genero'),
        ('Masculino', 'Masculino'),
        ('Femenino', 'Femenino'),
    ]
    ESTADO_CIVIL_CHOICES = [
        ('', 'Seleccione el Estado Civil'),
        ('Soltero/a', 'Soltero/a'),
        ('Casado/a', 'Casado/a'),
        ('Viudo/a', 'Viudo/a'),
        ('Divorciado/a', 'Divorciado/a'),
    ]
    NACIONALIDAD_CHOICES = [
        ('', 'Seleccione'),
        ('V', 'V'),
        ('E', 'E'),
    ]
    
    nacionalidad = forms.ChoiceField(
        choices=NACIONALIDAD_CHOICES,
        widget=forms.Select(attrs={
            'id': 'nacionalidad',
            'class': 'inline-select'
        })
    )

    cedula_identidad = forms.CharField(
        widget=forms.TextInput(attrs={
            'id': 'cedula_identidad',
            'class': 'inline-input',
        })
    )
    genero = forms.ChoiceField(
        choices=GENERO_CHOICES
    )
    estado_civil = forms.ChoiceField(
        choices=ESTADO_CIVIL_CHOICES
    )

    def clean_nombres(self):
        nombres = self.cleaned_data['nombres'].strip()

        if len(nombres) < 3:
            raise ValidationError(
                "El nombre debe tener al menos 3 caracteres."
            )

        if len(nombres) > 30:
            raise ValidationError(
                "El nombre no puede superar los 30 caracteres."
            )

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', nombres):
            raise ValidationError(
                "El nombre solo puede contener letras."
            )
        return nombres

    def clean_apellidos(self):
        apellidos = self.cleaned_data['apellidos'].strip()

        if len(apellidos) < 3:
            raise ValidationError(
                "El apellido debe tener al menos 3 caracteres."
            )

        if len(apellidos) > 30:
            raise ValidationError(
                "El apellido no puede superar los 30 caracteres."
            )

        if not re.match(r'^[A-Za-zÁÉÍÓÚáéíóúÑñ ]+$', apellidos):
            raise ValidationError(
                "El apellido solo puede contener letras."
            )
        return apellidos

    def clean_cedula_identidad(self):
        cedula = self.cleaned_data['cedula_identidad'].strip()
        nacionalidad = self.cleaned_data.get('nacionalidad')

        if not cedula.isdigit():
            raise ValidationError(
                "La cédula solo puede contener números."
            )
        if nacionalidad == "V":
            if len(cedula) < 7 or len(cedula) > 8:
                raise ValidationError(
                    "La cédula venezolana debe tener entre 7 y 8 dígitos."
                )
        elif nacionalidad == "E":
            if len(cedula) < 10 or len(cedula) > 11:
                raise ValidationError(
                    "La cédula de extranjero debe tener entre 10 y 11 dígitos."
                )
        return cedula
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.cedula_identidad:
            if "-" in self.instance.cedula_identidad:
                nacionalidad, cedula = self.instance.cedula_identidad.split("-", 1)

                self.fields['nacionalidad'].initial = nacionalidad
                self.fields['cedula_identidad'].initial = cedula 

class CredencialesUsuarioAdminForm(forms.ModelForm):
    class Meta:
        model = Cuenta
        fields = "__all__"

    usuario = forms.CharField(
        widget=forms.TextInput(attrs={
            "id": "id_usuario",
            "class": "inline-input",
            "placeholder": "Nombre de usuario",
            "required": True,
            "autocomplete": "off",
        })
    )

    clave = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "id": "id_clave",
            "class": "inline-input",
            "placeholder": "Contraseña",
            "required": True,
            "autocomplete": "off",
        })
    )

    def clean_usuario(self):
        usuario = self.cleaned_data["usuario"].strip()
        if len(usuario) < 4:
            raise ValidationError(
                "El nombre de usuario debe tener al menos 4 caracteres."
            )
        if len(usuario) > 160:
            raise ValidationError("El nombre de usuario es demasiado largo.")
        consulta = Cuenta.objects.filter(usuario__iexact=usuario)
        if self.instance.pk:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise ValidationError("Este nombre de usuario ya existe.")
        return usuario

    def clean_clave(self):
        clave = self.cleaned_data["clave"]
        if not (self.instance.pk and clave == self.instance.clave):
            validar_contrasenia_segura(clave)
        return clave

    def save(self, commit=True):
        clave_actual = self.instance.clave
        cuenta = super().save(commit=False)

        clave = self.cleaned_data.get("clave")

        if clave and clave != clave_actual:
            cuenta.clave = make_password(clave)

        if commit:
            cuenta.save()

        return cuenta

class PNFNucleoAdminForm(forms.ModelForm):
    id_pnf = forms.ModelChoiceField(queryset=Pnf.objects.all(), label='PNF')
    id_nucleo = forms.ModelChoiceField(queryset=Nucleos.objects.all(), label='Núcleo')

    class Meta:
        model = PNFNucleo
        fields = '__all__'
    
class PnfAdminForm(forms.ModelForm):

    PERIODO_ACADEMICO_CHOICES = [
        ("", "Elije el Periodo Académico"),
        ("Trimestre", "Trimestre"),
        ("Semestre", "Semestre"),
    ]

    periodo_academico = forms.ChoiceField(
        choices=PERIODO_ACADEMICO_CHOICES,
        required=False
    )

    class Meta:
        model = Pnf
        fields = "__all__"

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()

        if len(nombre) < 5:
            raise forms.ValidationError(
                "El nombre del PNF debe tener al menos 5 caracteres."
            )

        return nombre

class NucleoAdminForm(forms.ModelForm):

    class Meta:
        model = Nucleos
        fields = "__all__"

    def clean_nombre(self):
        nombre = self.cleaned_data['nombre'].strip()

        if len(nombre) < 3:
            raise forms.ValidationError(
                "El nombre del núcleo debe tener al menos 3 caracteres."
            )

        return nombre

    