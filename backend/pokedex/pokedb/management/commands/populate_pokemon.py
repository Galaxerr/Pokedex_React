import requests
import re
from django.core.management.base import BaseCommand
from pokedb.models import Pokemon  # Replace pokedb with your app name

class Command(BaseCommand):
    help = 'Populates the database with Pokémon from the National Pokédex'

    def handle(self, *args, **kwargs):
        api_url = "https://pokeapi.co/api/v2/pokemon?limit=1025"
        response = requests.get(api_url)

        if response.status_code == 200:
            pokemon_list = response.json().get("results", [])#[:20]  # Debugging: Limit to first 20 Pokémon

            for index, pokemon in enumerate(pokemon_list, start=1):
                name = pokemon["name"]
                details_response = requests.get(pokemon["url"])

                #ALL FORM IMAGES
                sprites = details_response.json().get("sprites", {}).get("front_default", "")

                if details_response.status_code == 200:
                    species_url = details_response.json().get("species", {}).get("url", "")
                    species_response = requests.get(species_url)

                    if species_response.status_code == 200:
                        #DESCRIPTION
                        flavor_text_entries = species_response.json().get("flavor_text_entries", [])
                        raw_description = next(
                            (entry["flavor_text"] for entry in flavor_text_entries if entry["language"]["name"] == "en"),
                            "No description available"
                        )

                        # Replace \n inside words with "" and between words with a space
                        description = re.sub(r"(?<=\w)-?\n(?=\w)", " ", raw_description)  # Remove \n inside words
                        description = description.replace("\n", "").replace("\f", " ")  # Replace remaining \n with spaces

                        # Optional: Remove soft hyphen (U+00AD) from the description
                        description = description.replace("­", "")  # Remove soft hyphen if present

                    else:
                        description = "No description available"
                else:
                    description = "No description available"

                # Create or update the Pokémon in the database
                Pokemon.objects.update_or_create(
                    entry=index,
                    defaults={"name": name.capitalize(), "description": description, "images": sprites}
                )
                self.stdout.write(f"Added/Updated: {name.capitalize()} (#{index})")
        else:
            self.stderr.write("Failed to fetch Pokémon list from the API")