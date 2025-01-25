import { useState, useEffect } from 'react';
import axios from 'axios';

const usePokemonList = () => {
  const [pokemonList, setPokemonList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPokemonList = async () => {
      try {
        const response = await axios.get('http://localhost:8000');
        setPokemonList(response.data); // Use response.data to set the Pokémon list
        setLoading(false);
      } catch (err) {
        setError(err);
        setLoading(false);
      }
    };

    fetchPokemonList();
  }, []);

  return { pokemonList, loading, error };
};

export default usePokemonList;
