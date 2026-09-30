import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';
import App from '../App';

describe('M0 shell', () => {
  it('renders the inert application shell', () => {
    render(<App />);
    expect(screen.getByRole('heading', { name: 'Pokédex' })).toBeInTheDocument();
    expect(screen.getByText(/scaffolding m0/i)).toBeInTheDocument();
  });
});
