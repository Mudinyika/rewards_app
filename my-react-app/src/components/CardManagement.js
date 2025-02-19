import React, { useEffect, useState } from 'react';

function CardManagement() {
  const [cards, setCards] = useState([]);

  useEffect(() => {
    fetch('http://127.0.0.1:5000/api/cards') // Replace with your actual endpoint
      .then((response) => response.json())
      .then((data) => setCards(data))
      .catch((error) => console.error('Error fetching cards:', error));
  }, []);

  return (
    <div>
      <h2>Card Management</h2>
      <ul>
        {cards.map((card) => (
          <li key={card.id}>
            Card Number: {card.card_number}, User ID: {card.user_id}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default CardManagement;
