from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Pokemon
from .serializers import PokemonSerializer

class PokemonViewSet(viewsets.ModelViewSet):
    """
    A viewset for viewing and editing Pokemon instances.
    """
    queryset = Pokemon.objects.all()
    serializer_class = PokemonSerializer

class PokemonDetailView(APIView):
    """
    A view to retrieve a single Pokémon's name and description by its entry.
    """

    def get(self, request, id):
        try:
            pokemon = Pokemon.objects.get(pk=id)
            data = {
                "entry": pokemon.entry,
                "name": pokemon.name,
                "description": pokemon.description,
                "images": pokemon.images,
            }
            return Response(data, status=status.HTTP_200_OK)
        except Pokemon.DoesNotExist:
            return Response({"error": "Pokemon not found"}, status=status.HTTP_404_NOT_FOUND)