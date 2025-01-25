import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import usePokemonList from '../hooks/usePokemonList';
import PokemonCard from '../components/PokemonCard';
import SearchBar from '../components/SearchBar';
import '../css/Pokedex.css';

const Pokedex = () => {
  const { pokemonList, loading, error } = usePokemonList();
  const [searchPokemon, setSearchPokemon] = useState('');
  const navigate = useNavigate();

  const filteredPokemons = pokemonList.filter(pokemon =>
    pokemon.name.toLowerCase().includes(searchPokemon.toLowerCase())
  );

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error loading Pokémon data.</div>;

  const handleCardClick = (entry) => {
    navigate(`/${entry}`);
  };

  return (
    <div className="pokedex-container">
      <h1>Pokédex</h1>
      <SearchBar searchTerm={searchPokemon} setSearchPokemon={setSearchPokemon} />

      <div className="pokemon-grid">
        {filteredPokemons.map(pokemon => (
          <PokemonCard pokemon={pokemon} onClick={() => handleCardClick(pokemon.entry)} />
        ))}
      </div>
    </div>
  );
};

export default Pokedex;
