import React from 'react';
import '../css/SearchBar.css';

const SearchBar = ({ searchTerm, setSearchPokemon }) => {
  return (
    <input 
      type="text" 
      placeholder="Search Pokémon" 
      value={searchTerm} 
      onChange={(e) => setSearchPokemon(e.target.value)} 
      className="search-bar"
    />
  );
};

export default SearchBar;