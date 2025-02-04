import React from 'react';
import { useParams } from 'react-router-dom';
import '../css/PokemonDetails.css'
import usePokemonDetails from '../hooks/usePokemonDetails';
import PokemonCard from '../components/PokemonCard';

const PokemonDetails = () => {
  const { entry } = useParams();

  const { pokemon, loading, error } = usePokemonDetails({entry});

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error loading Pokémon data.</div>;

  return (
    <div className="pokemon-details-container">
      <h1>Pokémon Details</h1>
      <div className="pokemon-details-wrapper">
        <PokemonCard pokemon={pokemon} />
        <div className="pokemon-description-box">
          <h3>{pokemon.description}</h3>
        </div>
      </div>
    </div>
  );
};

export default PokemonDetails;
