from io import BytesIO

from django.http import JsonResponse
from django.urls import Resolver404, resolve

from .fotos import LIMITE_ENVIO


class LimiteEnvioMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'POST':
            try:
                nome = resolve(request.path_info).view_name
            except Resolver404:
                nome = None
            if nome in {'paginas:relato', 'chamados:api_lista_ou_criar'}:
                try:
                    tamanho = int(request.META.get('CONTENT_LENGTH') or 0)
                except (ValueError, TypeError):
                    return JsonResponse({'erro': 'Tamanho do envio inválido.'}, status=400)
                if tamanho > LIMITE_ENVIO:
                    return self.rejeitar()
                corpo = request.read(LIMITE_ENVIO + 1)
                if len(corpo) > LIMITE_ENVIO:
                    return self.rejeitar()
                request._body = corpo
                request._stream = BytesIO(corpo)
        return self.get_response(request)

    def rejeitar(self):
        resposta = JsonResponse({'erro': 'O envio completo deve ter no máximo 25 MB.'}, status=413)
        resposta['Cache-Control'] = 'no-store'
        return resposta
