import { useState, useEffect } from 'react';
import axios from 'axios';

const usePokemonDetails = ({entry}) => {
  const [pokemon, setPokemon] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!entry) return;

    const fetchPokemonDetails = async () => {
      try {
        const response = await axios.get(`http://localhost:8000/pokemon/${entry}`);
        setPokemon(response.data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPokemonDetails();
  }, [entry]);

  return { pokemon, loading, error };
};

export default usePokemonDetails;