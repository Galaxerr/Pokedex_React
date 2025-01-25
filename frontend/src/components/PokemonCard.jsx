import React from 'react';
import '../css/PokemonCard.css';

const PokemonCard = ({ pokemon, onClick }) => {
  if(pokemon.entry <=  982)
    pokemon.name = pokemon.name.split('-')[0];

  return (
    <div className="pokemon-card" onClick={onClick}>
      <img 
        src={pokemon.images} 
        alt={`Image of ${pokemon.name}`} 
        className="pokemon-image" 
      />
      <h2>{pokemon.name}</h2>
    </div>
  );
};

export default PokemonCard;