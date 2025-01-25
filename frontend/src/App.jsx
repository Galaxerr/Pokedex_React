import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Pokedex from './pages/Pokedex';
import PokemonDetails from './pages/PokemonDetails';
import Poké_Ball from './assets/Poké_Ball_icon.png';
import './App.css';

const App = () => {
  return (
    <Router>
      <header className="app-header">
        <a href='/'>
          <img src={Poké_Ball} alt="Pokeball icon" />
        </a>
      </header>
      <div className="app-container">
        <Routes>
          <Route path="/" element={<Pokedex />} />
          <Route path="/:entry" element={<PokemonDetails />} />
        </Routes>
      </div>
      <footer className="app-footer">
        <h3>Created By <a href='https://github.com/Galaxerr'>@Galaxer</a></h3>
      </footer>
    </Router>
  );
};

export default App;
