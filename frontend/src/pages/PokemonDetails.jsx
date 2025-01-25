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
    <div className='pokemon-details'>
      <h2>Pokémon Details</h2>

      <PokemonCard pokemon={pokemon} />
      <h3>{pokemon.description}</h3>
    </div>
  );
};

export default PokemonDetails;
